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


def request_refund(order_id: str) -> dict:
    """Evaluate a simulated full-order refund.

    Args:
        order_id: The unique order identifier (e.g. 'ORD-1001').
    """
    result = get_order(order_id)

    if result.get("status") != "success":
        return result

    # Refunds over £100 (10,000 pence) require manager approval
    if result.get("amount_pence", 0) > 10000:
        return {
            "status": "manager_approval_required",
            "order_id": order_id,
            "amount_gbp": result.get("amount_pence", 0) / 100,
            "payment_issued": False,
        }

    return {
        "status": "simulation_only",
        "order_id": order_id,
        "amount_gbp": result.get("amount_pence", 0) / 100,
        "payment_issued": False,
    }