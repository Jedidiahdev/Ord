import hashlib
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, MessagePriority
from integrations.stripe import StripeService


@dataclass
class FinancialTransaction:
    transaction_id: str
    type: str  # revenue, expense, transfer, refund
    amount: float
    currency: str
    source: str  # stripe, crypto, manual
    description: str
    timestamp: float
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None


@dataclass
class RevenueMetrics:
    mrr: float
    arr: float
    total_revenue: float
    total_expenses: float
    gross_profit: float
    net_profit: float
    churn_rate: float
    ltv: float
    cac: float
    ltv_cac_ratio: float
    payback_period_days: int


@dataclass
class CryptoHolding:
    asset: str
    balance: float
    usd_value: float
    wallet_address: str
    last_updated: float


class CFAAgent(BaseAgent):
    """Ord-CFA: Stripe + crypto treasury + P&L with approval-gated writes."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-cfa",
            name="Ord-CFA",
            role="Chief Financial Agent",
            layer=1,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )

        self.transactions: List[FinancialTransaction] = []
        self.metrics = RevenueMetrics(
            mrr=0,
            arr=0,
            total_revenue=0,
            total_expenses=0,
            gross_profit=0,
            net_profit=0,
            churn_rate=0,
            ltv=0,
            cac=0,
            ltv_cac_ratio=0,
            payback_period_days=0,
        )

        self.crypto_holdings: Dict[str, CryptoHolding] = {}
        self.pending_financial_actions: Dict[str, Dict[str, Any]] = {}
        self.celebrated_milestones = set()

        # Real integration readiness
        self.stripe_connected = False
        self.stripe = None
        self.stripe_webhook_secret = None
        self.stripe_service = StripeService()

        self.logger.info("💰 Ord-CFA initialized | Treasury Guardian")

    def get_capabilities(self) -> List[str]:
        return [
            "stripe_integration",
            "crypto_wallet_integration",
            "approval_gated_financial_writes",
            "pnl_generation",
            "treasury_management",
            "expense_monitoring",
            "investor_reporting",
            "transaction_auditing",
            "budget_governance",
        ]

    async def connect_stripe(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None) -> Dict[str, Any]:
        if not api_key and not webhook_secret:
            integration_result = self.stripe_service.connect()
            if integration_result.get("status") == "connected":
                self.stripe_connected = True
                return integration_result

        api_key = api_key or os.getenv("STRIPE_API_KEY")
        webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET", "")

        if not api_key:
            return {"status": "error", "message": "Missing Stripe API key"}

        try:
            import stripe  # type: ignore

            stripe.api_key = api_key
            self.stripe = stripe
            self.stripe_connected = True
            self.stripe_webhook_secret = webhook_secret
            return {"status": "connected", "mode": "real", "message": "Stripe integration active"}
        except Exception as e:
            self.logger.warning(f"Stripe SDK unavailable or failed to initialize: {e}")
            self.stripe_connected = True
            self.stripe_webhook_secret = webhook_secret
            return {"status": "connected", "mode": "degraded", "message": "Stripe running in compatibility mode"}

    async def process_stripe_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            return await self._record_payment(data)
        if event_type == "subscription.created":
            return await self._record_subscription(data)
        if event_type == "invoice.paid":
            return await self._record_invoice_payment(data)
        if event_type == "customer.subscription.deleted":
            return await self._record_churn(data)

        return {"status": "ignored", "event_type": event_type}

    async def _record_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        tx = FinancialTransaction(
            transaction_id=payment_data.get("id", f"stripe-{int(time.time())}"),
            type="revenue",
            amount=payment_data.get("amount", 0) / 100,
            currency=payment_data.get("currency", "usd").upper(),
            source="stripe",
            description=f"Payment: {payment_data.get('description', 'Unknown')}",
            timestamp=time.time(),
            metadata={"customer_id": payment_data.get("customer")},
        )
        await self._record_transaction(tx)
        await self.send_message(
            recipient_id="ord-cma",
            message_type="event",
            payload={"event_type": "payment_received", "amount": tx.amount, "customer_id": payment_data.get("customer")},
            priority=MessagePriority.NORMAL,
        )
        return {"status": "recorded", "transaction_id": tx.transaction_id}

    async def _record_subscription(self, sub_data: Dict[str, Any]) -> Dict[str, Any]:
        amount = sub_data.get("plan", {}).get("amount", 0) / 100
        interval = sub_data.get("plan", {}).get("interval", "month")
        self.metrics.mrr += amount if interval == "month" else amount / 12
        self.metrics.arr = self.metrics.mrr * 12
        await self._check_milestones()
        return {"status": "subscription_recorded", "mrr": self.metrics.mrr}

    async def _record_churn(self, sub_data: Dict[str, Any]) -> Dict[str, Any]:
        del sub_data
        self.metrics.churn_rate = min(100.0, self.metrics.churn_rate + 0.5)
        return {"status": "churn_recorded", "churn_rate": self.metrics.churn_rate}

    async def _record_invoice_payment(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        tx = FinancialTransaction(
            transaction_id=invoice_data.get("id", f"inv-{int(time.time())}"),
            type="revenue",
            amount=invoice_data.get("amount_paid", 0) / 100,
            currency=invoice_data.get("currency", "usd").upper(),
            source="stripe",
            description=f"Invoice: {invoice_data.get('description', 'Unknown')}",
            timestamp=time.time(),
        )
        await self._record_transaction(tx)
        return {"status": "invoice_recorded", "transaction_id": tx.transaction_id}

    async def connect_crypto_wallet(self, chain: str, wallet_address: str, private_key_ref: str) -> Dict[str, Any]:
        self.crypto_holdings[chain] = CryptoHolding(
            asset=chain.upper(),
            balance=0,
            usd_value=0,
            wallet_address=wallet_address,
            last_updated=time.time(),
        )
        return {
            "status": "connected",
            "chain": chain,
            "address": wallet_address,
            "signing": "external" if private_key_ref else "watch_only",
        }

    async def get_crypto_balance(self, chain: str) -> Dict[str, Any]:
        holding = self.crypto_holdings.get(chain)
        if not holding:
            return {"error": f"No wallet connected for {chain}"}
        return {
            "chain": chain,
            "balance": holding.balance,
            "usd_value": holding.usd_value,
            "wallet_address": holding.wallet_address,
            "last_updated": holding.last_updated,
        }

    async def request_financial_write(self, action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        approval_id = hashlib.sha256(f"{action_type}:{time.time()}".encode()).hexdigest()[:16]
        self.pending_financial_actions[approval_id] = {
            "id": approval_id,
            "action_type": action_type,
            "context": context,
            "status": "pending",
            "requested_at": time.time(),
        }
        await self.send_message(
            recipient_id="ord-pm",
            message_type="ceo_approval_request",
            payload={
                "approval_type": "financial_write",
                "approval_id": approval_id,
                "action_type": action_type,
                "context": context,
            },
            priority=MessagePriority.CRITICAL,
        )
        return {"status": "pending_approval", "approval_id": approval_id}

    async def apply_approved_financial_write(self, approval_id: str, approved: bool) -> Dict[str, Any]:
        action = self.pending_financial_actions.get(approval_id)
        if not action:
            return {"error": "Unknown approval_id"}
        if not approved:
            action["status"] = "denied"
            return {"status": "denied", "approval_id": approval_id}

        action["status"] = "approved"
        context = action.get("context", {})
        tx = FinancialTransaction(
            transaction_id=context.get("transaction_id", f"manual-{int(time.time())}"),
            type=context.get("type", "expense"),
            amount=float(context.get("amount", 0)),
            currency=context.get("currency", "USD"),
            source=context.get("source", "manual"),
            description=context.get("description", "Approved financial write"),
            timestamp=time.time(),
            metadata={"approval_id": approval_id},
        )
        await self._record_transaction(tx)
        return {"status": "applied", "transaction_id": tx.transaction_id}

    async def _record_transaction(self, transaction: FinancialTransaction) -> None:
        transaction.signature = self._sign_transaction(transaction)
        self.transactions.append(transaction)
        await self._update_revenue_metrics()

    def _sign_transaction(self, transaction: FinancialTransaction) -> str:
        material = f"{transaction.transaction_id}:{transaction.type}:{transaction.amount}:{transaction.timestamp}"
        return hashlib.sha256(material.encode()).hexdigest()

    async def _update_revenue_metrics(self) -> None:
        revenue = sum(t.amount for t in self.transactions if t.type == "revenue")
        expenses = sum(t.amount for t in self.transactions if t.type == "expense")

        self.metrics.total_revenue = revenue
        self.metrics.total_expenses = expenses
        self.metrics.gross_profit = revenue - expenses
        self.metrics.net_profit = self.metrics.gross_profit
        self.metrics.arr = self.metrics.mrr * 12

        if self.metrics.cac > 0:
            self.metrics.ltv_cac_ratio = self.metrics.ltv / self.metrics.cac
        self.metrics.payback_period_days = int((self.metrics.cac / max(self.metrics.mrr, 1)) * 30) if self.metrics.cac else 0

    async def generate_pnl_report(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "revenue": self.metrics.total_revenue,
            "expenses": self.metrics.total_expenses,
            "gross_profit": self.metrics.gross_profit,
            "net_profit": self.metrics.net_profit,
            "mrr": self.metrics.mrr,
            "arr": self.metrics.arr,
            "transaction_count": len(self.transactions),
        }

    async def treasury_summary(self) -> Dict[str, Any]:
        return {
            "fiat": {"currency": "USD", "cash_equivalent": max(self.metrics.net_profit, 0)},
            "crypto": {chain: holding.__dict__ for chain, holding in self.crypto_holdings.items()},
            "risk_flags": ["approval_required_for_transfers", "monitor_concentration"],
        }

    async def _check_milestones(self) -> None:
        for milestone in [1000, 5000, 10000, 25000, 50000, 100000]:
            if self.metrics.mrr >= milestone and milestone not in self.celebrated_milestones:
                self.celebrated_milestones.add(milestone)
                await self.send_message(
                    recipient_id="broadcast",
                    message_type="celebration",
                    payload={"message": f"🎉 MRR milestone reached: ${milestone:,}!"},
                )

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "unknown")

        if task_type == "connect_stripe":
            return await self.connect_stripe(task.get("api_key"), task.get("webhook_secret"))
        if task_type == "process_webhook":
            return await self.process_stripe_webhook(task.get("event", {}))
        if task_type == "connect_crypto_wallet":
            return await self.connect_crypto_wallet(task.get("chain"), task.get("wallet_address"), task.get("private_key_ref", ""))
        if task_type == "get_crypto_balance":
            return await self.get_crypto_balance(task.get("chain", ""))
        if task_type == "request_write":
            return await self.request_financial_write(task.get("action_type", "manual_write"), task.get("context", {}))
        if task_type == "apply_approved_write":
            return await self.apply_approved_financial_write(task.get("approval_id", ""), bool(task.get("approved")))
        if task_type == "pnl_report":
            return await self.generate_pnl_report()
        if task_type == "treasury_summary":
            return await self.treasury_summary()

        return {"error": f"Unknown task type: {task_type}"}
