"""Web channel adapter. The API exposes Eagle Core; it does not own core state."""
from flask import Blueprint, jsonify, request
from eagle_bot.core.orders import WorkOrder
from eagle_bot.core.orchestration import Orchestrator

bp = Blueprint("eagle_web", __name__)
orchestrator = Orchestrator()


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "product": "Eagle Bot", "core": "available"})


@bp.get("/api/coworkers")
def coworkers():
    return jsonify([
        {"key": c.key, "name": c.name, "purpose": c.purpose}
        for c in orchestrator.coworkers.list()
    ])


@bp.post("/api/orders/prepare")
def prepare_order():
    payload = request.get_json(silent=True) or {}
    try:
        order = WorkOrder(
            owner_id=str(payload.get("owner_id", "")),
            objective=str(payload.get("objective", "")),
            coworker=str(payload.get("coworker", "generalist")),
        )
        return jsonify(orchestrator.prepare(order)), 200
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400
