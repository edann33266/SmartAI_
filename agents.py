import json
from dataclasses import dataclass
from typing import Dict, List

from llm import generate_json, generate_text


@dataclass
class Customer:
    name: str
    email: str
    company: str
    industry: str
    lead_score: int
    last_contact_days_ago: int
    annual_revenue: int
    current_tool: str
    region: str

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "Customer":
        # Support both column name formats
        contact_days = row.get("last_contact_days_ago") or row.get("contact_days_ago", "0")
        
        return cls(
            name=row["name"],
            email=row["email"],
            company=row["company"],
            industry=row["industry"],
            lead_score=int(row["lead_score"]),
            last_contact_days_ago=int(contact_days),
            annual_revenue=int(row["annual_revenue"]),
            current_tool=row["current_tool"],
            region=row["region"],
        )


class EmailWriterAgent:
    """
    A simple "agent" with its own style and goal, implemented via a
    distinct system prompt.
    """

    def __init__(self, name: str, style_description: str) -> None:
        self.name = name
        self.style_description = style_description

    def draft_email(self, customer: Customer, product_name: str, product_value_prop: str) -> str:
        system_prompt = (
            "You are an expert B2B sales email writer. "
            f"Your specific style: {self.style_description}. "
            "Write a concise outbound sales email.\n"
            "- 3 short paragraphs max\n"
            "- Clear subject line\n"
            "- Personalized using the customer profile\n"
            "- One clear call to action (15–30 minute call)\n"
            "- Neutral, professional tone\n\n"
            "IMPORTANT: Output ONLY the email content. Do NOT include any preamble, "
            "introduction, or phrases like 'Here is a concise outbound sales email:' or "
            "'Here's the email:'. Start directly with 'Subject:' line."
        )

        user_prompt = f"""
Customer profile:
- Name: {customer.name}
- Company: {customer.company}
- Industry: {customer.industry}
- Region: {customer.region}
- Lead score: {customer.lead_score}
- Last contact (days ago): {customer.last_contact_days_ago}
- Annual revenue: {customer.annual_revenue}
- Current tool: {customer.current_tool}

Product:
- Name: {product_name}
- Value proposition: {product_value_prop}

Write the full email including subject line. Start directly with "Subject:" - no preamble.
"""
        prompt = f"{system_prompt}\n\n{user_prompt}"
        raw_email = generate_text(prompt, temperature=0.8)
        
        # Clean up any preamble text that might still appear
        return self._clean_email_output(raw_email)
    
    def _clean_email_output(self, text) -> str:
        """Remove common preamble phrases from LLM output."""
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        # List of common preambles to remove
        preambles = [
            "Here is a concise outbound sales email:",
            "Here's a concise outbound sales email:",
            "Here is the email:",
            "Here's the email:",
            "Here is an email:",
            "Here's an email:",
            "Here is a sales email:",
            "Here's a sales email:",
            "Here is the outbound email:",
            "Here's the outbound email:",
        ]
        
        cleaned = text.strip()
        
        # Remove preambles (case-insensitive)
        for preamble in preambles:
            if cleaned.lower().startswith(preamble.lower()):
                cleaned = cleaned[len(preamble):].strip()
                break
        
        # Remove any leading colons or dashes
        cleaned = cleaned.lstrip(":-").strip()
        
        return cleaned


class SalesManagerAgent:
    """
    Manager agent that:
    - selects which leads to contact
    - chooses the best email among drafts from writer agents
    """

    def __init__(self) -> None:
        ...

    def select_leads(self, customers: List[Customer]) -> List[Customer]:
        """
        Very simple lead selection heuristic:
        - lead_score >= 80
        - last_contact_days_ago >= 14
        """
        selected = [
            c
            for c in customers
            if c.lead_score >= 80 and c.last_contact_days_ago >= 14
        ]
        return selected

    def choose_best_email(self, customer: Customer, drafts: Dict[str, str]) -> Dict[str, str]:
        """
        Ask the LLM (as a manager) to evaluate and pick the best email draft.
        Returns a dict with keys:
        - chosen_agent
        - final_email (optionally lightly edited by the manager)
        - reasoning
        """
        system_prompt = (
            "You are a sales manager evaluating 3 outbound sales emails "
            "for a single B2B prospect. You must pick the single best email "
            "and can lightly edit it for clarity and impact. "
            "Return ONLY a JSON object with keys: chosen_agent, final_email, reasoning."
        )

        drafts_text = "\n\n".join(
            f"Agent: {agent_name}\n---\n{email}\n---"
            for agent_name, email in drafts.items()
        )

        user_prompt = f"""
Customer profile:
- Name: {customer.name}
- Company: {customer.company}
- Industry: {customer.industry}
- Region: {customer.region}
- Lead score: {customer.lead_score}
- Last contact (days ago): {customer.last_contact_days_ago}
- Annual revenue: {customer.annual_revenue}
- Current tool: {customer.current_tool}

Here are 3 candidate outbound emails from different agents:

{drafts_text}

Evaluate them on:
- Personalization and relevance
- Clarity of value proposition
- Strength but politeness of the CTA

Pick the single best email. You MAY make small edits to improve it, but keep the original tone.
"""
        prompt = f"{system_prompt}\n\n{user_prompt}"

        data = generate_json(prompt, temperature=0.4)

        # Helper function to safely convert to string
        def safe_str(value) -> str:
            """Safely convert any value to string."""
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, (list, dict)):
                return str(value)
            return str(value).strip()

        # If the model didn't return valid JSON, fall back safely
        if "_raw" in data:
            raw = data.get("_raw", "")
            fallback_agent = next(iter(drafts.keys()), "unknown")
            return {
                "chosen_agent": fallback_agent,
                "final_email": drafts.get(fallback_agent, ""),
                "reasoning": safe_str(raw),
            }

        # Basic validation / defaults with safe string conversion
        chosen_agent = safe_str(data.get("chosen_agent", "")) or next(iter(drafts.keys()), "unknown")
        
        # Get final email with fallback
        final_email = data.get("final_email")
        if not final_email:
            final_email = drafts.get(chosen_agent) or drafts.get(next(iter(drafts.keys()), ""), "")
        final_email = safe_str(final_email)
        
        reasoning = safe_str(data.get("reasoning", ""))

        return {
            "chosen_agent": chosen_agent,
            "final_email": final_email,
            "reasoning": reasoning,
        }
