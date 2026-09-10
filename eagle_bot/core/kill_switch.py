"""Emergency execution stop.

This is a local foundation mechanism; production deployment must add durable,
operator-controlled infrastructure around it.
"""


class KillSwitch:
    def __init__(self):
        self._engaged = False

    @property
    def engaged(self) -> bool:
        return self._engaged

    def engage(self) -> None:
        self._engaged = True

    def reset(self) -> None:
        self._engaged = False

    def assert_execution_allowed(self) -> None:
        if self._engaged:
            raise RuntimeError("Eagle execution is stopped by the emergency kill switch")
