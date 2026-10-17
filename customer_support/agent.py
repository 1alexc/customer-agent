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
    description="Routes customers to the appropriate support specialist.",
    instruction="""
    You are the Customer Support Orchestrator.
    Welcome the customer and understand their request.
    Delegate order and delivery questions to order_support_agent.
    Delegate refund questions to refund_support_agent.
    For combined order-and-refund requests, use refund_support_agent.
    Ask a short clarifying question when necessary.
    Do not invent order information or process refunds yourself.
    Do not promise approval or payment.
    """,
    sub_agents=[
        order_support_agent,
        refund_support_agent,
    ],
)