import json
from pathlib import Path

ORDERS_FILE = Path(__file__).resolve().parent / "orders.json"


def _load_orders() -> dict:
    """Load mock orders from the orders.json database file."""
    if not ORDERS_FILE.exists():
        return {}
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_order(order_id: str) -> dict:
    """Retrieve order and delivery details by order ID.

    Args:
        order_id: The unique order identifier (e.g. 'ORD-1001', 'ORD-1004').
    """
    order_id = order_id.strip().upper()
    orders = _load_orders()
    order = orders.get(order_id)

    if order is None:
        return {
            "status": "not_found",
            "message": f"No matching order found for ID '{order_id}'. Please check the order number.",
        }

    return {
        "status": "success",
        "order_id": order_id,
        **order,
    }


def draft_reply(
    customer_name: str,
    message: str,
    order_id: str = "",
    tone: str = "friendly and professional",
) -> dict:
    """Draft a professional, empathetic customer service reply.

    Args:
        customer_name: Name of the customer being addressed.
        message: The proposed resolution, delivery update, or explanation.
        order_id: Optional order identifier referenced in the message.
        tone: Tone of the response (e.g., 'friendly and professional', 'empathetic', 'concise').
    """
    clean_name = customer_name.strip() if customer_name else "Valued Customer"
    subject = (
        f"Update regarding your order {order_id}"
        if order_id
        else "Update from Customer Support"
    )

    draft_text = (
        f"Dear {clean_name},\n\n"
        f"{message.strip()}\n\n"
        "If you have any further questions or require additional assistance, please reply to this message.\n\n"
        "Warm regards,\n"
        "Customer Support Team"
    )

    return {
        "status": "success",
        "subject": subject,
        "recipient": clean_name,
        "tone": tone,
        "draft": draft_text,
    }


def issue_refund(order_id: str, reason: str = "Customer request") -> dict:
    """Evaluate and process a refund for an order.

    Company Policy:
        - Refunds up to £100 (10,000 pence) are automatically approved and issued.
        - Refunds exceeding £100 require manager approval.

    Args:
        order_id: The unique order identifier (e.g. 'ORD-1001', 'ORD-1002').
        reason: The reason for the refund request (e.g. 'damaged item', 'late delivery').
    """
    order_id = order_id.strip().upper()
    order_info = get_order(order_id)

    if order_info.get("status") != "success":
        return order_info

    amount_pence = order_info.get("amount_pence", 0)
    amount_gbp = amount_pence / 100
    customer_name = order_info.get("customer_name", "Customer")

    # Policy threshold: > £100 requires manager authorization
    if amount_pence > 10000:
        return {
            "status": "manager_approval_required",
            "order_id": order_id,
            "customer_name": customer_name,
            "amount_gbp": amount_gbp,
            "refund_issued": False,
            "reason": reason,
            "message": (
                f"Refund of £{amount_gbp:.2f} for order {order_id} exceeds the £100 threshold "
                "and requires manager approval before processing."
            ),
        }

    return {
        "status": "success",
        "order_id": order_id,
        "customer_name": customer_name,
        "amount_gbp": amount_gbp,
        "refund_issued": True,
        "reason": reason,
        "message": (
            f"Refund of £{amount_gbp:.2f} for order {order_id} has been successfully issued to {customer_name}."
        ),
    }


# Backwards compatibility alias
request_refund = issue_refund

__all__ = ["get_order", "draft_reply", "issue_refund", "request_refund"]