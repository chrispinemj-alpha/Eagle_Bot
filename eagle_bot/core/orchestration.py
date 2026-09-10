"""Core coordinator. It routes intent; it does not pretend to be an autonomous AGI."""
from .coworkers import CoworkerRegistry
from .orders import WorkOrder


class Orchestrator:
    def __init__(self, coworkers: CoworkerRegistry | None = None):
        self.coworkers = coworkers or CoworkerRegistry()

    def prepare(self, order: WorkOrder) -> dict:
        order.validate()
        coworker = self.coworkers.get(order.coworker)
        return {
            "order_id": order.id,
            "objective": order.objective,
            "coworker": coworker.key,
            "coworker_purpose": coworker.purpose,
            "status": "prepared",
        }
