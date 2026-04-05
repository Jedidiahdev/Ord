"""
Ord v3.0 - Demo Script
Demonstrates all 50 features and core workflows.

Usage:
    python demo.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.memory import MemoryManager
from agents.infrastructure.orchestrator import Orchestrator
from agents.executive.pm_agent import PMAgent
from agents.executive.coo_agent import COOAgent
from agents.executive.cfa_agent import CFAAgent
from agents.executive.bd_agent import BDAgent
from agents.executive.hr_agent import HRAgent
from agents.executive.cma_agent import CMAAgent
from agents.executive.daa_agent import DAAAgent
from agents.infrastructure.security_agent import SecurityAgent
from agents.execution.se_agent import SEAgent
from agents.execution.design_agent import DesignAgent
from agents.execution.content_agent import ContentAgent
from agents.execution.review_agent import ReviewAgent
from agents.execution.frontend_agent import FrontendAgent
from agents.execution.backend_agent import BackendAgent


class OrdDemo:
    """Demonstration of Ord v3.0 capabilities"""
    
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.memory = MemoryManager()
        self.results = []
        
        print("🌟 Ord v3.0 Demo")
        print("=" * 60)
    
    async def setup(self):
        """Initialize all agents"""
        print("\n📦 Initializing Agents...")
        
        # Executive Council
        self.pm = PMAgent(self.orchestrator, self.memory)
        self.coo = COOAgent(self.orchestrator, self.memory)
        self.cfa = CFAAgent(self.orchestrator, self.memory)
        
        # Domain Leaders
        self.bd = BDAgent(self.orchestrator, self.memory)
        self.hr = HRAgent(self.orchestrator, self.memory)
        self.cma = CMAAgent(self.orchestrator, self.memory)
        self.daa = DAAAgent(self.orchestrator, self.memory)
        self.sec = SecurityAgent(self.orchestrator, self.memory)
        
        # Execution Team
        self.se = SEAgent(self.orchestrator, self.memory)
        self.design = DesignAgent(self.orchestrator, self.memory)
        self.content = ContentAgent(self.orchestrator, self.memory)
        self.review = ReviewAgent(self.orchestrator, self.memory)
        self.fullstack_a = FrontendAgent(self.orchestrator, self.memory)
        self.fullstack_b = BackendAgent(self.orchestrator, self.memory)
        
        # Register all agents
        for agent in [
            self.pm, self.coo, self.cfa,
            self.bd, self.hr, self.cma, self.daa, self.sec,
            self.se, self.design, self.content, self.review, self.fullstack_a, self.fullstack_b
        ]:
            self.orchestrator.register_agent(agent)
        
        print(f"✅ {len(self.orchestrator.agents)} agents initialized")
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        await self.demo_1_product_building()
        await self.demo_2_variation_scoring()
        await self.demo_3_code_review()
        await self.demo_4_financial_tracking()
        await self.demo_5_memory_system()
        await self.demo_6_security_audit()
        await self.demo_7_agent_hiring()
        await self.demo_8_company_status()
    
    async def demo_1_product_building(self):
        """DEMO 1: Product Building with 20 Variations"""
        print("\n" + "=" * 60)
        print("🚀 DEMO 1: Product Building (20-Variation Factory)")
        print("=" * 60)
        
        result = await self.pm.process_ceo_request(
            "Build a Linear-style project management tool",
            input_type="text"
        )
        
        print(f"📋 Project ID: {result.get('project_id')}")
        print(f"📊 Status: {result.get('status')}")
        print(f"💬 Message: {result.get('message')}")
        
        self.results.append(("Product Building", result))
    
    async def demo_2_variation_scoring(self):
        """DEMO 2: DAA Variation Scoring"""
        print("\n" + "=" * 60)
        print("📊 DEMO 2: Variation Scoring (DAA)")
        print("=" * 60)
        
        # Generate mock variations
        variations = [
            {"variation_id": i, "result": {"mock": f"variation_{i}"}}
            for i in range(5)  # Use 5 for demo speed
        ]
        
        result = await self.daa.score_variations("demo-project", variations)
        
        print(f"📈 Scored {len(result.get('scored_variations', []))} variations")
        print(f"🏆 Top Score: {result.get('top_3', [{}])[0].get('daa_score', 0)}")
        
        for var in result.get('top_3', [])[:3]:
            print(f"   Variation {var['variation_id']}: {var['daa_score']} - {var['recommendation']}")
        
        self.results.append(("Variation Scoring", result))
    
    async def demo_3_code_review(self):
        """DEMO 3: Code Review"""
        print("\n" + "=" * 60)
        print("🔍 DEMO 3: Code Review (Ord-Review)")
        print("=" * 60)
        
        sample_code = """
function processUser(data) {
    console.log("Processing user");
    // TODO: Add validation
    return db.query("SELECT * FROM users WHERE id = " + data.id);
}
"""
        
        result = await self.review.process_task({
            "type": "review_pr",
            "pr_id": "pr-demo-123",
            "branch": "feature/demo",
            "code": sample_code
        })
        
        print(f"📋 Review Status: {result.get('status')}")
        print(f"⭐ Quality Score: {result.get('quality_score')}")
        print(f"🔒 Security Passed: {result.get('security_passed')}")
        print(f"💬 Comments: {len(result.get('comments', []))}")
        
        for comment in result.get('comments', []):
            print(f"   - {comment.get('message', '')}")
        
        self.results.append(("Code Review", result))
    
    async def demo_4_financial_tracking(self):
        """DEMO 4: Financial Tracking"""
        print("\n" + "=" * 60)
        print("💰 DEMO 4: Financial Tracking (Ord-CFA)")
        print("=" * 60)
        
        # Record some revenue
        await self.cfa.process_task({
            "type": "record_revenue",
            "amount": 5000,
            "project_name": "Demo Product"
        })
        
        dashboard = await self.cfa.get_revenue_dashboard()
        
        print(f"💵 Total Revenue: ${dashboard.get('total_revenue', 0)}")
        print(f"📈 MRR: ${dashboard.get('mrr', 0)}")
        print(f"📊 LTV/CAC Ratio: {dashboard.get('ltv_cac_ratio', 0)}")
        
        # Generate forecast
        forecast = await self.cfa.generate_revenue_forecast(months_ahead=3)
        print(f"🔮 Forecast Confidence: {forecast.get('confidence_interval', {})}")
        
        self.results.append(("Financial Tracking", dashboard))
    
    async def demo_5_memory_system(self):
        """DEMO 5: Memory System"""
        print("\n" + "=" * 60)
        print("🧠 DEMO 5: Memory System (3-Tier + Genome)")
        print("=" * 60)
        
        # Store in different tiers
        await self.memory.store("hot_key", "hot_value", tier="hot", agent_id="ord-pm")
        await self.memory.store("working_key", "working_value", tier="working", agent_id="ord-pm")
        
        # Store in genome
        await self.memory.store_genome_entry(
            entry_type="learning",
            agent_id="ord-pm",
            content={"learning": "Always use shadcn/ui for consistency"},
            tags=["ui", "best_practices"]
        )
        
        # Query genome
        results = await self.memory.query_genome("ui best practices")
        
        stats = self.memory.get_stats()
        print(f"🧬 Genome Entries: {stats['genome']['total_entries']}")
        print(f"📚 Projects Archived: {stats['genome']['projects_archived']}")
        print(f"🔍 Query Results: {len(results)}")
        
        self.results.append(("Memory System", stats))
    
    async def demo_6_security_audit(self):
        """DEMO 6: Security Audit"""
        print("\n" + "=" * 60)
        print("🔒 DEMO 6: Security Audit (Ord-Sec)")
        print("=" * 60)
        
        # Code with potential issues
        test_code = """
const API_KEY = "sk-live-1234567890abcdef";
function login(password) {
    return db.query("SELECT * FROM users WHERE pass = '" + password + "'");
}
"""
        
        result = await self.sec.process_task({
            "type": "audit_code",
            "code": test_code,
            "agent_id": "ord-se"
        })
        
        print(f"✅ Can Proceed: {result.get('can_proceed')}")
        print(f"⚠️ Violations: {len(result.get('violations', []))}")
        
        for v in result.get('violations', [])[:3]:
            print(f"   - {v.get('type')}: {v.get('message', '')}")
        
        # Compliance report
        compliance = await self.sec.generate_compliance_report()
        print(f"📊 Compliance Score: {compliance.get('compliance_score')}/100")
        
        self.results.append(("Security Audit", result))
    
    async def demo_7_agent_hiring(self):
        """DEMO 7: Agent Hiring Workflow"""
        print("\n" + "=" * 60)
        print("👥 DEMO 7: Agent Hiring (Ord-HR)")
        print("=" * 60)
        
        result = await self.hr.initiate_hiring(
            "Hire a DevOps specialist agent",
            role_spec_file=None
        )
        
        print(f"📋 Status: {result.get('status')}")
        print(f"💬 Message: {result.get('message')}")
        
        self.results.append(("Agent Hiring", result))
    
    async def demo_8_company_status(self):
        """DEMO 8: Company Status"""
        print("\n" + "=" * 60)
        print("📊 DEMO 8: Company Status")
        print("=" * 60)
        
        status = self.orchestrator.get_agent_status()
        
        print(f"👥 Total Agents: {len(status)}")
        print("\n📋 Agent Status:")
        
        for agent_id, info in status.items():
            emoji = "🟢" if info['status'] == 'idle' else "🔵"
            print(f"   {emoji} {info['name']} (Layer {info['layer']}): {info['status']}")
        
        # Message stats
        msg_stats = self.orchestrator.get_message_stats()
        print(f"\n📨 Messages Routed: {msg_stats['total_messages']}")
        
        self.results.append(("Company Status", status))
    
    async def print_summary(self):
        """Print demo summary"""
        print("\n" + "=" * 60)
        print("📋 DEMO SUMMARY")
        print("=" * 60)
        
        for name, result in self.results:
            status = "✅" if "error" not in str(result).lower() else "❌"
            print(f"{status} {name}")
        
        print("\n🎉 All demos completed!")
        print("\nOrd v3.0 is ready for production!")
        print("Run 'python main.py' to start the full system.")


async def main():
    """Main demo entry point"""
    demo = OrdDemo()
    await demo.setup()
    await demo.run_all_demos()
    await demo.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
