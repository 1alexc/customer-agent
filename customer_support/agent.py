import os
from pathlib import Path

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
for env_candidate in [CURRENT_DIR.parent / ".env", CURRENT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(env_candidate, override=True)
        break

from google.adk.agents import Agent
from .guardrails import explain_model_armor_block, model_armor_config
from .order_agent import order_support_agent
from .refund_agent import refund_support_agent

root_agent = Agent(
    name="support_orchestrator",
    model=os.getenv("SUPPORT_MODEL", "gemini-2.5-flash"),
    description="Routes customer support requests to specialist agents for order tracking and refunds.",
    instruction="""
    You are the Customer Support Orchestrator.
    Your role is to understand the customer's request and coordinate with specialized agents:
    - Route order tracking, shipping status, and order inquiry responses to `order_support_agent`.
    - Route refund requests, return policy inquiries, and refund drafting to `refund_support_agent`.
    - For combined requests (e.g. order inquiry + refund), route to `refund_support_agent`.
    - If the customer's inquiry is ambiguous or missing an order ID, ask a concise clarifying question.
    - Do not fabricate order data or execute financial actions directly; always delegate to the specialist agents.
    """,
    sub_agents=[
        order_support_agent,
        refund_support_agent,
    ],
    generate_content_config=model_armor_config(),
    after_model_callback=explain_model_armor_block,
)