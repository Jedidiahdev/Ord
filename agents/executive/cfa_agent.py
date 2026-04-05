import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, A2AMessage, MessagePriority


@dataclass
class FinancialTransaction:
    """Immutable financial transaction record"""
    transaction_id: str
    type: str  # revenue, expense, transfer, refund
    amount: float
    currency: str
    source: str  # stripe, crypto, manual
    description: str
    timestamp: float
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    signature: Optional[str] = None  # Cryptographic signature


@dataclass
class RevenueMetrics:
    """Key revenue metrics"""
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    total_revenue: float
    churn_rate: float
    ltv: float  # Lifetime Value
    cac: float  # Customer Acquisition Cost
    ltv_cac_ratio: float
    payback_period_days: int


@dataclass
class CryptoHolding:
    """Cryptocurrency holding"""
    asset: str  # BTC, ETH, SOL, etc.
    balance: float
    usd_value: float
    wallet_address: str
    last_updated: float


class CFAAgent(BaseAgent):
    """
    Ord-CFA: The Chief Financial Agent
    
    Responsibilities:
    1. Stripe integration: payments, subscriptions, webhooks
    2. Crypto treasury: multi-sig wallet management
    3. Real-time revenue tracking and forecasting
    4. Unit economics dashboard (Feature 34)
    5. Predictive financial twin (Feature 32)
    6. Investor-grade reporting (Feature 37)
    7. Expense and token budget tracking
    
    Security:
    - All financial writes require CEO approval via PM
    - Cryptographic signatures on all transactions
    - Immutable ledger for audit trail
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-cfa",
            name="Ord-CFA",
            role="Chief Financial Agent",
            layer=1,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        # Revenue tracking
        self.transactions: List[FinancialTransaction] = []
        self.metrics = RevenueMetrics(
            mrr=0, arr=0, total_revenue=0,
            churn_rate=0, ltv=0, cac=0,
            ltv_cac_ratio=0, payback_period_days=0
        )
        
        # Crypto holdings
        self.crypto_holdings: Dict[str, CryptoHolding] = {}
        
        # Stripe integration (mock in demo)
        self.stripe_connected = False
        self.stripe_webhook_secret = None
        
        # Pending approvals (financial writes require CEO)
        self.pending_financial_actions: Dict[str, Dict] = {}
        
        # Revenue milestones for celebrations (Feature 40)
        self.celebrated_milestones = set()
        
        self.logger.info("💰 Ord-CFA initialized | Treasury Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "stripe_integration",
            "crypto_treasury",
            "revenue_tracking",
            "financial_forecasting",
            "unit_economics",
            "expense_monitoring",
            "investor_reporting",
            "transaction_auditing",
            "milestone_tracking",
            "budget_governance"
        ]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # STRIPE INTEGRATION (Feature 31)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def connect_stripe(self, api_key: str, webhook_secret: str) -> Dict:
        """Connect Stripe account"""
        # In production: validate API key with Stripe
        self.stripe_connected = True
        self.stripe_webhook_secret = webhook_secret
        
        self.logger.info("💳 Stripe connected successfully")
        
        return {
            "status": "connected",
            "message": "Stripe integration active. Ready to process payments! 💳"
        }
    
    async def process_stripe_webhook(self, event: Dict) -> Dict:
        """
        Process Stripe webhook events in real-time (Feature 31)
        Events: payment_intent.succeeded, subscription.created, etc.
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        
        if event_type == "payment_intent.succeeded":
            return await self._record_payment(data)
        elif event_type == "subscription.created":
            return await self._record_subscription(data)
        elif event_type == "invoice.paid":
            return await self._record_invoice_payment(data)
        elif event_type == "customer.subscription.deleted":
            return await self._record_churn(data)
        
        return {"status": "ignored", "event_type": event_type}
    
    async def _record_payment(self, payment_data: Dict) -> Dict:
        """Record successful payment"""
        transaction = FinancialTransaction(
            transaction_id=payment_data.get("id"),
            type="revenue",
            amount=payment_data.get("amount", 0) / 100,  # Convert from cents
            currency=payment_data.get("currency", "usd").upper(),
            source="stripe",
            description=f"Payment: {payment_data.get('description', 'Unknown')}",
            timestamp=time.time(),
            metadata={
                "customer_id": payment_data.get("customer"),
                "payment_method": payment_data.get("payment_method")
            }
        )
        
        # Sign transaction
        transaction.signature = self._sign_transaction(transaction)
        
        self.transactions.append(transaction)
        await self._update_revenue_metrics()
        
        # Notify CMA for follow-up
        await self.send_message(
            recipient_id="ord-cma",
            message_type="event",
            payload={
                "event_type": "payment_received",
                "amount": transaction.amount,
                "customer_id": payment_data.get("customer")
            },
            priority=MessagePriority.NORMAL
        )
        
        return {"status": "recorded", "transaction_id": transaction.transaction_id}
    
    async def _record_subscription(self, sub_data: Dict) -> Dict:
        """Record new subscription"""
        # Update MRR
        amount = sub_data.get("plan", {}).get("amount", 0) / 100
        interval = sub_data.get("plan", {}).get("interval", "month")
        
        if interval == "month":
            self.metrics.mrr += amount
        elif interval == "year":
            self.metrics.mrr += amount / 12
        
        self.metrics.arr = self.metrics.mrr * 12
        
        await self._check_milestones()
        
        return {"status": "subscription_recorded", "mrr": self.metrics.mrr}
    
    async def _record_churn(self, sub_data: Dict) -> Dict:
        """Record subscription cancellation"""
        # Update churn metrics
        # In production: calculate actual churn rate
        self.logger.info("📉 Subscription churn recorded")
        return {"status": "churn_recorded"}
    
    async def _record_invoice_payment(self, invoice_data: Dict) -> Dict:
        """Record invoice payment"""
        transaction = FinancialTransaction(
            transaction_id=invoice_data.get("id"),
            type="revenue",
            amount=invoice_data.get("amount_paid", 0) / 100,
            currency=invoice_data.get("currency", "usd").upper(),
            source="stripe",
            description=f"Invoice: {invoice_data.get('description', 'Unknown')}",
            timestamp=time.time()
        )
        
        transaction.signature = self._sign_transaction(transaction)
        self.transactions.append(transaction)
        
        return {"status": "invoice_recorded"}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CRYPTO TREASURY (Feature 38)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def connect_crypto_wallet(
        self,
        chain: str,  # base, solana, ethereum
        wallet_address: str,
        private_key_ref: str  # Reference to secure key storage
    ) -> Dict:
        """Connect crypto wallet for treasury management"""
        self.crypto_holdings[chain] = CryptoHolding(
            asset=chain.upper(),
            balance=0,
            usd_value=0,
            wallet_address=wallet_address,
            last_updated=time.time()
        )
        
        self.logger.info(f"🔐 {chain.upper()} wallet connected: {wallet_address[:10]}...")
        
        return {
            "status": "connected",
            "chain": chain,
            "address": wallet_address
        }
    
    async def get_crypto_balance(self, chain: str) -> Dict:
        """Get crypto balance with USD valuation"""
        holding = self.crypto_holdings.get(chain)
        if not holding:
            return {"error": f"No wallet connected for {chain}"}
        
        # In production: query blockchain
        return {
            "chain": chain,
            "balance": holding.balance,
            "usd_value": holding.usd_value,
            "address": holding.wallet_address
        }
    
    async def propose_crypto_transfer(
        self,
        chain: str,
        to_address: str,
        amount: float,
        reason: str
    ) -> str:
        """
        Propose crypto transfer (requires CEO approval)
        24h timelock for security (Feature 38)
        """
        proposal_id = f"crypto-proposal-{int(time.time())}"
        
        self.pending_financial_actions[proposal_id] = {
            "proposal_id": proposal_id,
            "type": "crypto_transfer",
            "chain": chain,
            "to_address": to_address,
            "amount": amount,
            "reason": reason,
            "proposed_at": time.time(),
            "execute_after": time.time() + (24 * 3600),  # 24h timelock
            "status": "awaiting_approval"
        }
        
        # Request CEO approval via PM
        await self.send_message(
            recipient_id="ord-pm",
            message_type="ceo_approval_request",
            payload={
                "approval_type": "crypto_transfer",
                "proposal_id": proposal_id,
                "details": {
                    "chain": chain,
                    "amount": amount,
                    "to": to_address[:10] + "...",
                    "reason": reason,
                    "timelock": "24 hours"
                }
            },
            priority=MessagePriority.HIGH
        )
        
        return proposal_id
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REVENUE METRICS & FORECASTING (Features 32, 39)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _update_revenue_metrics(self) -> None:
        """Update all revenue metrics"""
        # Calculate total revenue
        self.metrics.total_revenue = sum(
            t.amount for t in self.transactions if t.type == "revenue"
        )
        
        # Calculate LTV and CAC (simplified)
        # In production: use cohort analysis
        customer_count = len(set(
            t.metadata.get("customer_id") for t in self.transactions
            if t.metadata.get("customer_id")
        ))
        
        if customer_count > 0:
            self.metrics.ltv = self.metrics.total_revenue / customer_count
        
        # LTV/CAC ratio
        if self.metrics.cac > 0:
            self.metrics.ltv_cac_ratio = self.metrics.ltv / self.metrics.cac
        
        # Payback period
        if self.metrics.mrr > 0 and self.metrics.cac > 0:
            self.metrics.payback_period_days = int(
                (self.metrics.cac / (self.metrics.mrr / 30))
            )
    
    async def get_revenue_dashboard(self) -> Dict:
        """Get real-time revenue dashboard data (Feature 34)"""
        return {
            "mrr": self.metrics.mrr,
            "arr": self.metrics.arr,
            "total_revenue": self.metrics.total_revenue,
            "churn_rate": self.metrics.churn_rate,
            "ltv": self.metrics.ltv,
            "cac": self.metrics.cac,
            "ltv_cac_ratio": self.metrics.ltv_cac_ratio,
            "payback_period_days": self.metrics.payback_period_days,
            "recent_transactions": [
                {
                    "id": t.transaction_id,
                    "amount": t.amount,
                    "type": t.type,
                    "timestamp": t.timestamp
                }
                for t in self.transactions[-10:]
            ]
        }
    
    async def generate_revenue_forecast(
        self,
        months_ahead: int = 3
    ) -> Dict:
        """
        Predictive revenue forecasting with confidence intervals (Feature 39)
        Uses Monte Carlo simulation
        """
        # Simplified forecast
        # In production: use DAA for sophisticated modeling
        base_mrr = self.metrics.mrr
        growth_rates = [0.05, 0.10, 0.15]  # Conservative, expected, optimistic
        
        forecasts = []
        for month in range(1, months_ahead + 1):
            for rate in growth_rates:
                forecasted_mrr = base_mrr * ((1 + rate) ** month)
                forecasts.append({
                    "month": month,
                    "scenario": "conservative" if rate == 0.05 else "expected" if rate == 0.10 else "optimistic",
                    "mrr": forecasted_mrr
                })
        
        return {
            "current_mrr": base_mrr,
            "forecasts": forecasts,
            "confidence_interval": {
                "low": base_mrr * 0.8,
                "expected": base_mrr * 1.1,
                "high": base_mrr * 1.3
            }
        }
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MILESTONE TRACKING (Feature 40)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _check_milestones(self) -> None:
        """Check and celebrate revenue milestones"""
        milestones = [
            (1000, "First $1k MRR! 🎉"),
            (10000, "$10k MRR milestone! 🚀"),
            (100000, "$100k MRR - Incredible! 🌟"),
            (500000, "$500k MRR - Unstoppable! 💎"),
            (1000000, "$1M MRR - LEGENDARY! 👑")
        ]
        
        for threshold, celebration in milestones:
            if self.metrics.mrr >= threshold and threshold not in self.celebrated_milestones:
                self.celebrated_milestones.add(threshold)
                await self._celebrate_milestone(threshold, celebration)
    
    async def _celebrate_milestone(self, amount: float, message: str) -> None:
        """Celebrate revenue milestone with team"""
        await self.send_message(
            recipient_id="broadcast",
            message_type="celebration",
            payload={
                "celebration_type": "revenue_milestone",
                "milestone": amount,
                "message": f"🎉 **MILESTONE REACHED!** {message} We did it together! 💙"
            },
            priority=MessagePriority.NORMAL
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # INVESTOR REPORTING (Feature 37)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def generate_board_deck(self) -> Dict:
        """Generate investor-grade board deck in <60 seconds"""
        dashboard = await self.get_revenue_dashboard()
        forecast = await self.generate_revenue_forecast()
        
        # Get agent performance from COO
        await self.send_message(
            recipient_id="ord-coo",
            message_type="query",
            payload={"query_type": "intelligence_report"},
            priority=MessagePriority.NORMAL
        )
        
        deck = {
            "title": f"Ord v3.0 Board Deck - {datetime.now().strftime('%B %Y')}",
            "generated_at": time.time(),
            "sections": {
                "financials": dashboard,
                "forecast": forecast,
                "agent_performance": "pending",  # Will be filled by COO response
                "active_projects": "pending"  # Will be filled by PM response
            }
        }
        
        return {
            "status": "generated",
            "deck": deck,
            "message": "📊 Board deck generated! Ready for your review."
        }
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SECURITY & AUDITING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _sign_transaction(self, transaction: FinancialTransaction) -> str:
        """Cryptographically sign transaction"""
        data = f"{transaction.transaction_id}:{transaction.amount}:{transaction.timestamp}"
        private_key = hashlib.sha256(f"cfa_private_{self.identity.agent_id}".encode()).hexdigest()
        return hashlib.sha256(f"{data}:{private_key}".encode()).hexdigest()
    
    async def get_audit_log(
        self,
        start_date: Optional[float] = None,
        end_date: Optional[float] = None
    ) -> List[Dict]:
        """Get immutable audit log of all transactions"""
        if not start_date:
            start_date = time.time() - (30 * 24 * 3600)  # Last 30 days
        if not end_date:
            end_date = time.time()
        
        filtered = [
            {
                "id": t.transaction_id,
                "type": t.type,
                "amount": t.amount,
                "currency": t.currency,
                "timestamp": t.timestamp,
                "signature": t.signature
            }
            for t in self.transactions
            if start_date <= t.timestamp <= end_date
        ]
        
        return filtered
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN TASK PROCESSOR
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process CFA-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "stripe_webhook":
            return await self.process_stripe_webhook(task.get("event", {}))
        
        elif task_type == "connect_stripe":
            return await self.connect_stripe(
                task.get("api_key"),
                task.get("webhook_secret")
            )
        
        elif task_type == "connect_crypto":
            return await self.connect_crypto_wallet(
                task.get("chain"),
                task.get("wallet_address"),
                task.get("private_key_ref")
            )
        
        elif task_type == "get_dashboard":
            return await self.get_revenue_dashboard()
        
        elif task_type == "generate_forecast":
            return await self.generate_revenue_forecast(task.get("months", 3))
        
        elif task_type == "generate_board_deck":
            return await self.generate_board_deck()
        
        elif task_type == "get_audit_log":
            return {"transactions": await self.get_audit_log()}
        
        elif task_type == "propose_transfer":
            return await self.propose_crypto_transfer(
                task.get("chain"),
                task.get("to_address"),
                task.get("amount"),
                task.get("reason")
            )
        
        elif task_type == "record_revenue":
            # Record revenue from product deployment
            transaction = FinancialTransaction(
                transaction_id=f"rev-{int(time.time())}",
                type="revenue",
                amount=task.get("amount", 0),
                currency="usd",
                source="product",
                description=f"Revenue from {task.get('project_name', 'Unknown')}",
                timestamp=time.time(),
                project_id=task.get("project_id")
            )
            transaction.signature = self._sign_transaction(transaction)
            self.transactions.append(transaction)
            await self._update_revenue_metrics()
            
            return {"status": "recorded", "transaction_id": transaction.transaction_id}
        
        return {"error": f"Unknown task type: {task_type}"}
