"""Python hooks for franchise system tools."""
from datetime import datetime


def update_order_hold(ctx, order_id, hold_reason, line_no=None):
    """Place or lift a hold on franchise order lines."""

    if not order_id:
        return {"error": "order_id is required"}

    # Check order exists
    order = ctx.q(
        "SELECT * FROM franchise_orders WHERE order_id = $oid",
        oid=order_id
    )
    if not order:
        return {"error": f"Order {order_id} not found"}

    order_rec = order[0]

    # If hold_reason is empty, lift the hold
    if not hold_reason or hold_reason == "":
        # Lift holds
        if line_no:
            ctx.q(
                "UPDATE franchise_order_lines SET hold_status = 'released' WHERE order_id = $oid AND line_no = $ln",
                oid=order_id, ln=line_no
            )
        else:
            ctx.q(
                "UPDATE franchise_order_lines SET hold_status = 'released' WHERE order_id = $oid",
                oid=order_id
            )
        ctx.q(
            "UPDATE franchise_orders SET hold_reason = NULL WHERE order_id = $oid",
            oid=order_id
        )
        return {
            "order_id": order_id,
            "action": "lifted",
            "hold_reason": None,
            "lines_affected": "all" if not line_no else f"line {line_no}"
        }
    else:
        # Place hold
        if line_no:
            ctx.q(
                "UPDATE franchise_order_lines SET hold_status = 'held' WHERE order_id = $oid AND line_no = $ln",
                oid=order_id, ln=line_no
            )
        else:
            ctx.q(
                "UPDATE franchise_order_lines SET hold_status = 'held' WHERE order_id = $oid",
                oid=order_id
            )
        ctx.q(
            "UPDATE franchise_orders SET hold_reason = $hr WHERE order_id = $oid",
            oid=order_id, hr=hold_reason
        )
        return {
            "order_id": order_id,
            "action": "held",
            "hold_reason": hold_reason,
            "lines_affected": "all" if not line_no else f"line {line_no}"
        }
