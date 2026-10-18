import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from google.adk.agents import Agent
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
)