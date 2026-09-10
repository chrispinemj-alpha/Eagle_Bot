"""Telegram boundary only. Telegram is a channel, not the Eagle product.

Integration is intentionally not activated until credentials and a production
adapter are configured.
"""


class TelegramChannel:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def status(self) -> dict:
        return {"channel": "telegram", "enabled": self.enabled}
