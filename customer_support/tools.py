ORDERS = {
    "ORD-1001": {
        "customer_name": "Alice Smith",
        "items": ["Wireless Noise-Canceling Headphones"],
        "amount_pence": 4500,  # £45.00 (under £100, standard refund eligible)
        "currency": "GBP",
        "delivery_status": "delivered",
        "current_location": "Delivered (Left on front porch)",
        "carrier": "Royal Mail",
        "tracking_number": "GB100123456RM",
        "order_date": "2026-10-06",
        "delivery_date": "2026-10-10",
        "estimated_delivery": "Delivered on 10 Oct 2026",
    },
    "ORD-1002": {
        "customer_name": "Bob Jones",
        "items": ["34-inch Ultrawide Gaming Monitor"],
        "amount_pence": 24900,  # £249.00 (> £100, requires manager approval)
        "currency": "GBP",
        "delivery_status": "delivered",
        "current_location": "Delivered (Signed by B. Jones)",
        "carrier": "DHL Express",
        "tracking_number": "DHL9876543210",
        "order_date": "2026-10-09",
        "delivery_date": "2026-10-12",
        "estimated_delivery": "Delivered on 12 Oct 2026",
    },
    "ORD-1003": {
        "customer_name": "Charlie Brown",
        "items": ["Ergonomic Mechanical Keyboard"],
        "amount_pence": 8000,  # £80.00
        "currency": "GBP",
        "delivery_status": "delivered",
        "current_location": "Delivered",
        "carrier": "Evri",
        "tracking_number": "EVR456789012",
        "order_date": "2026-07-28",
        "delivery_date": "2026-08-01",
        "estimated_delivery": "Delivered on 01 Aug 2026",
    },
    "ORD-1004": {
        "customer_name": "Diana Prince",
        "items": ["USB-C 7-in-1 Charging Hub"],
        "amount_pence": 3500,  # £35.00
        "currency": "GBP",
        "delivery_status": "in_transit",
        "current_location": "Local Distribution Depot, Birmingham Hub",
        "carrier": "Royal Mail Tracked 24",
        "tracking_number": "RM883920194GB",
        "order_date": "2026-10-16",
        "delivery_date": None,
        "estimated_delivery": "Tomorrow by 2:00 PM",
    },
}


def get_order(order_id: str) -> dict:
    """Retrieve order and delivery details by order ID.

    Args:
        order_id: The unique order identifier (e.g. 'ORD-1001', 'ORD-1004').
    """
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)

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