import os
from pathlib import Path
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
for env_candidate in [CURRENT_DIR.parent / ".env", CURRENT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(env_candidate, override=True)
        break

from google.adk.agents import Agent
from .tools import draft_reply, get_order
from .guardrails import model_armor_config

order_support_agent = Agent(
    name="order_support_agent",
    model=os.getenv("SUPPORT_MODEL", "gemini-2.5-flash"),
    description="Handles order details, status, delivery questions, and drafts customer replies.",
    instruction="""
    You are the Order Support Agent.
    Responsibilities:
    1. Ask for the order ID (e.g., 'ORD-1004') if missing from the user's request.
    2. Always invoke the `get_order` tool before answering order or tracking questions.
    3. Use only facts returned by `get_order`. Do not invent or guess tracking details.
    4. If no order is found, ask the customer to verify their order number.
    5. When asked to draft a customer reply or notification message, call the `draft_reply` tool.
    6. If the customer requests a refund or cancellation, transfer back to `support_orchestrator`.
    7. Maintain a polite, empathetic, and concise communication style.
    """,
    tools=[get_order, draft_reply],
    generate_content_config=model_armor_config(),
)