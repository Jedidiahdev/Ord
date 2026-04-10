import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class StripeConfig:
    api_key: str
    webhook_secret: str = ""
    sandbox_mode: bool = True

    @classmethod
    def from_env(cls) -> "StripeConfig":
        key = os.getenv("STRIPE_API_KEY", "")
        sandbox_flag = os.getenv("STRIPE_SANDBOX", "true").lower() != "false"
        return cls(api_key=key, webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""), sandbox_mode=sandbox_flag)


class StripeService:
    """Real Stripe adapter for CFA with sandbox-first defaults."""

    def __init__(self, config: Optional[StripeConfig] = None):
        self.config = config or StripeConfig.from_env()
        self._stripe = None

    @property
    def enabled(self) -> bool:
        return bool(self.config.api_key)

    def connect(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "STRIPE_API_KEY not configured"}

        try:
            import stripe  # type: ignore

            stripe.api_key = self.config.api_key
            account = stripe.Account.retrieve()
            self._stripe = stripe
            return {
                "status": "connected",
                "account_id": account.get("id"),
                "sandbox_mode": self.config.sandbox_mode,
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def create_checkout_session(self, amount_cents: int, success_url: str, cancel_url: str, currency: str = "usd") -> Dict[str, Any]:
        if self._stripe is None:
            conn = self.connect()
            if conn.get("status") != "connected":
                return conn

        try:
            session = self._stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {"name": "Ord Offer"},
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return {"status": "created", "session_id": session.id, "url": session.url}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        if self._stripe is None:
            conn = self.connect()
            if conn.get("status") != "connected":
                return conn

        try:
            event = self._stripe.Webhook.construct_event(payload, signature, self.config.webhook_secret)
            return {"status": "verified", "event_type": event.get("type"), "event": event}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
