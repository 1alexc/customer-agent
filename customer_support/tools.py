def get_order(order_id: str) -> dict:
    """Retrieve a mock order using its order ID."""
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)

    if order is None:
        return {
            "status": "not_found",
            "message": "No matching order was found.",
        }

    return {
        "status": "success",
        "order_id": order_id,
        **order,
    }

def request_refund(order_id: str) -> dict:
    """Evaluate a simulated full-order refund."""
    result = get_order(order_id)

    if result["status"] != "success":
        return result

    if not result["refund_eligible"]:
        return {"status": "not_eligible", "payment_issued": False}

    if result["amount_pence"] > 10000:
        return {
            "status": "manager_approval_required",
            "payment_issued": False,
        }

    return {
        "status": "simulation_only",
        "payment_issued": False,
    }