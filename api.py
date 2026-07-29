import csv
import logging
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from agents import Customer, EmailWriterAgent, SalesManagerAgent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("salesai.api")

# ---------------- Config ----------------
_DATA_PATH = Path(os.getenv("CUSTOMERS_CSV", "data/customers.csv"))
_PRODUCT_NAME = os.getenv("PRODUCT_NAME", "SalesAI Copilot")
_PRODUCT_VALUE_PROP = os.getenv(
    "PRODUCT_VALUE_PROP",
    "helps sales teams automatically prioritize leads and draft highly "
    "personalized outreach, saving hours per week.",
)

# CORS origins — add your deployed frontend URL here once you have it
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if o.strip()
]

# ---------------- Optional ML scorer ----------------
try:
    from ml.ml_lead_scorer import MLLeadScorer

    _ml_scorer: Optional[MLLeadScorer] = MLLeadScorer()
except Exception as exc:  # noqa: BLE001
    logger.warning("ML scorer unavailable, falling back to rule-based selection: %s", exc)
    _ml_scorer = None

# ---------------- App setup ----------------
app = FastAPI(title="SalesAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = SalesManagerAgent()

_WRITER_AGENTS = {
    "value_focus": EmailWriterAgent(
        "value_focus",
        "ROI-focused; quantify value with concrete numbers and business impact",
    ),
    "relationship_focus": EmailWriterAgent(
        "relationship_focus",
        "warm, consultative, partnership-oriented tone",
    ),
    "urgency_focus": EmailWriterAgent(
        "urgency_focus",
        "direct, concise, gentle sense of urgency",
    ),
}


# ---------------- Data loading ----------------
def load_customers() -> List[Customer]:
    if not _DATA_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Customer data file not found at {_DATA_PATH}",
        )

    customers: List[Customer] = []
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                customers.append(Customer.from_row(row))
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping invalid row: %s", exc)
    return customers


def find_customer_by_email(email: str) -> Optional[Customer]:
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )
    for customer in load_customers():
        if customer.email.lower() == email.lower():
            return customer
    return None


# ---------------- Pydantic models ----------------
class EmailSendRequest(BaseModel):
    email_text: str = Field(..., min_length=10)

    @field_validator("email_text")
    @classmethod
    def validate_email_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email text cannot be empty")
        if len(v.strip()) < 10:
            raise ValueError("Email text is too short")
        return v


def _customer_to_dict(customer: Customer) -> dict:
    payload = {
        "name": customer.name,
        "email": customer.email,
        "company": customer.company,
        "industry": customer.industry,
        "lead_score": customer.lead_score,
        "last_contact_days_ago": customer.last_contact_days_ago,
        "annual_revenue": customer.annual_revenue,
        "current_tool": customer.current_tool,
        "region": customer.region,
        "selected_for_outreach": customer.lead_score >= 80 and customer.last_contact_days_ago >= 14,
    }
    if _ml_scorer is not None:
        try:
            payload["conversion_probability"] = _ml_scorer.predict_conversion_probability(customer)
            payload["ml_score_available"] = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("ML scoring failed for %s: %s", customer.email, exc)
            payload["ml_score_available"] = False
    else:
        payload["ml_score_available"] = False
    return payload


# ---------------- Routes ----------------
@app.get("/customers")
async def get_customers():
    customers = load_customers()
    return [_customer_to_dict(c) for c in customers]


@app.get("/customers/{email}")
async def get_customer(email: str):
    customer = find_customer_by_email(email)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with email '{email}' not found",
        )
    return _customer_to_dict(customer)


@app.post("/customers/{email}/generate")
async def generate_email(email: str):
    logger.info("Generating email for %s", email)
    customer = find_customer_by_email(email)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with email '{email}' not found",
        )

    try:
        drafts = {}
        for name, writer in _WRITER_AGENTS.items():
            draft = writer.draft_email(customer, _PRODUCT_NAME, _PRODUCT_VALUE_PROP)
            if not isinstance(draft, str):
                logger.warning("Agent %s returned non-string draft: %s", name, type(draft))
                draft = str(draft) if draft else ""
            drafts[name] = draft

        decision = manager.choose_best_email(customer, drafts)

        logger.info("Email generated successfully for %s (chosen: %s)", email, decision.get("chosen_agent"))

        return {
            "customer": _customer_to_dict(customer),
            "chosen_agent": decision.get("chosen_agent"),
            "final_email": decision.get("final_email"),
            "reasoning": decision.get("reasoning"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error generating email for %s: %s", email, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {exc}",
        )


@app.post("/customers/{email}/send")
async def send_generated_email(email: str, payload: EmailSendRequest):
    from email_sender import send_email

    try:
        customer = find_customer_by_email(email)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with email '{email}' not found",
            )

        result = send_email(to_address=customer.email, email_text=payload.email_text)

        return {
            "status": "ok",
            "message": f"Email sent to {customer.name}",
            "recipient": email,
            "dry_run": result.get("dry_run", True),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Error sending email to %s: %s", email, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sending failed: {exc}",
        )


@app.get("/stats")
async def get_stats():
    customers = load_customers()
    if not customers:
        return {
            "total_customers": 0,
            "selected_for_outreach": 0,
            "selection_rate": 0,
            "average_lead_score": 0,
            "ml_scorer_available": _ml_scorer is not None,
        }

    selected = manager.select_leads(customers)
    avg_score = sum(c.lead_score for c in customers) / len(customers)

    stats = {
        "total_customers": len(customers),
        "selected_for_outreach": len(selected),
        "selection_rate": round((len(selected) / len(customers)) * 100, 1),
        "average_lead_score": round(avg_score, 1),
        "ml_scorer_available": _ml_scorer is not None,
    }

    if _ml_scorer is not None:
        try:
            probs = [_ml_scorer.predict_conversion_probability(c) for c in customers]
            stats["average_conversion_probability"] = round(sum(probs) / len(probs), 3)
            stats["high_probability_leads"] = len([p for p in probs if p >= 0.7])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not compute ML stats: %s", exc)

    return stats


@app.get("/health")
async def health_check():
    try:
        customers = load_customers()
        return {
            "status": "healthy",
            "customers_loaded": len(customers),
            "ml_scorer_available": _ml_scorer is not None,
            "llm_provider": "gemini",
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Health check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy",
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc), "status_code": 500},
    )
