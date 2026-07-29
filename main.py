import os

from dotenv import load_dotenv

from agents import Customer, EmailWriterAgent, SalesManagerAgent
from api import load_customers  # reuses the same CSV loader as the API
from email_sender import send_email

load_dotenv()

_PRODUCT_NAME = os.getenv("PRODUCT_NAME", "SalesAI Copilot")
_PRODUCT_VALUE_PROP = os.getenv(
    "PRODUCT_VALUE_PROP",
    "helps sales teams automatically prioritize leads and draft highly "
    "personalized outreach, saving hours per week.",
)


def main() -> None:
    customers = load_customers()
    print(f"Loaded {len(customers)} customers.")

    manager = SalesManagerAgent()
    selected = manager.select_leads(customers)
    print(f"SalesManager selected {len(selected)} customer(s) for outreach.")

    writer_agents = {
        "value_focus": EmailWriterAgent(
            "value_focus", "ROI-focused; quantify value with concrete numbers"
        ),
        "relationship_focus": EmailWriterAgent(
            "relationship_focus", "warm, consultative, partnership-oriented tone"
        ),
        "urgency_focus": EmailWriterAgent(
            "urgency_focus", "direct, concise, gentle sense of urgency"
        ),
    }

    for customer in selected:
        print(f"\n=== Working on customer: {customer.name} ({customer.company}) ===")

        drafts = {
            name: agent.draft_email(customer, _PRODUCT_NAME, _PRODUCT_VALUE_PROP)
            for name, agent in writer_agents.items()
        }

        decision = manager.choose_best_email(customer, drafts)
        print(f"Manager chose agent: {decision.get('chosen_agent')}")
        print(f"Reasoning: {decision.get('reasoning')}")
        print("-" * 60)
        print(decision.get("final_email"))
        print("-" * 60)

        send_email(to_address=customer.email, email_text=decision.get("final_email", ""))


if __name__ == "__main__":
    main()
