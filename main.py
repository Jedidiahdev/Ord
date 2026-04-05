import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from core.memory import MemoryManager
from agents.infrastructure.orchestrator import Orchestrator

# Agent imports
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

# Integration imports
from integrations.telegram.bot import TelegramBot, TelegramConfig


class OrdCompany:
    """
    Ord v3.0 - The AI-Native Company
    
    Initializes and coordinates all 15 agents across 4 layers:
    - Layer 1: Executive Council (PM, COO, CFA)
    - Layer 2: Domain Leaders (BD, HR, CMA, DAA, Sec)
    - Layer 3: Execution Team (SE, Design, Content, Review, FullStack-A/B)
    - Layer 4: Infrastructure (Orchestrator)
    """
    
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.memory = MemoryManager()
        self.telegram_bot: Optional[TelegramBot] = None
        
        self.logger = self._setup_logging()
        self.logger.info("🌟 Ord v3.0 Initializing...")
    
    def _setup_logging(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        return logging.getLogger("Ord")
    
    async def initialize(self):
        """Initialize all agents and systems"""
        
        # LAYER 1: EXECUTIVE COUNCIL
        
        self.logger.info("👑 Initializing Executive Council...")
        
        pm = PMAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        coo = COOAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        cfa = CFAAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        
        self.orchestrator.register_agent(pm)
        self.orchestrator.register_agent(coo)
        self.orchestrator.register_agent(cfa)
        
        
        # LAYER 2: DOMAIN LEADERS
        
        self.logger.info("📊 Initializing Domain Leaders...")
        
        bd = BDAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        hr = HRAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        cma = CMAAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        daa = DAAAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        sec = SecurityAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        
        self.orchestrator.register_agent(bd)
        self.orchestrator.register_agent(hr)
        self.orchestrator.register_agent(cma)
        self.orchestrator.register_agent(daa)
        self.orchestrator.register_agent(sec)
        
        
        # LAYER 3: EXECUTION TEAM
        
        self.logger.info("🔨 Initializing Execution Team...")
        
        se = SEAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        design = DesignAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        content = ContentAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        review = ReviewAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        fullstack_a = FrontendAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        fullstack_b = BackendAgent(orchestrator=self.orchestrator, memory_manager=self.memory)
        
        self.orchestrator.register_agent(se)
        self.orchestrator.register_agent(design)
        self.orchestrator.register_agent(content)
        self.orchestrator.register_agent(review)
        self.orchestrator.register_agent(fullstack_a)
        self.orchestrator.register_agent(fullstack_b)
        
        
        # TELEGRAM BOT (Primary Interface)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            self.logger.info("📱 Initializing Telegram Bot...")
            config = TelegramConfig(
                bot_token=bot_token,
                ceo_chat_id=os.getenv("CEO_CHAT_ID"),
                voice_enabled=True
            )
            self.telegram_bot = TelegramBot(config, orchestrator=self.orchestrator)
            await self.telegram_bot.start()
        else:
            self.logger.info("⚠️ No TELEGRAM_BOT_TOKEN found. Running without Telegram.")
        
        
        # START BACKGROUND TASKS
        
        asyncio.create_task(self.orchestrator.process_messages())
        asyncio.create_task(coo.start_health_monitoring())
        
        self.logger.info("✅ Ord v3.0 Initialized Successfully!")
        self.logger.info(f"   Agents: {len(self.orchestrator.agents)}")
        self.logger.info(f"   Memory: {self.memory.get_stats()}")
    
    async def run_demo(self):
        """Run demonstration of Ord capabilities"""
        self.logger.info("🎬 Starting Demo...")
        
        # Get PM agent
        pm = self.orchestrator.agents.get("ord-pm")
        
        if not pm:
            self.logger.error("PM agent not found!")
            return
        
        # Demo 1: Product Building Request
        self.logger.info("\n" + "="*60)
        self.logger.info("DEMO 1: Product Building")
        self.logger.info("="*60)
        
        result = await pm.process_ceo_request(
            "Build a Linear-style project management tool",
            input_type="text"
        )
        self.logger.info(f"Result: {result}")
        
        await asyncio.sleep(2)
        
        # Demo 2: Status Check
        self.logger.info("\n" + "="*60)
        self.logger.info("DEMO 2: Status Check")
        self.logger.info("="*60)
        
        result = await pm.process_ceo_request("What's the company status?")
        self.logger.info(f"Result: {result}")
        
        await asyncio.sleep(2)
        
        # Demo 3: Agent Status
        self.logger.info("\n" + "="*60)
        self.logger.info("DEMO 3: Agent Status")
        self.logger.info("="*60)
        
        status = self.orchestrator.get_agent_status()
        for agent_id, info in status.items():
            self.logger.info(f"  {info['name']} (Layer {info['layer']}): {info['status']}")
        
        # Demo 4: Memory Stats
        self.logger.info("\n" + "="*60)
        self.logger.info("DEMO 4: Memory Stats")
        self.logger.info("="*60)
        
        stats = self.memory.get_stats()
        for tier, tier_stats in stats.items():
            self.logger.info(f"  {tier}: {tier_stats}")
    
    async def run(self):
        """Main run loop"""
        await self.initialize()
        
        # Run demo if in demo mode
        if os.getenv("ORD_DEMO_MODE", "false").lower() == "true":
            await self.run_demo()
        
        # Keep running
        self.logger.info("\n🚀 Ord v3.0 is running! Press Ctrl+C to stop.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Shutting down...")
            if self.telegram_bot:
                await self.telegram_bot.stop()


async def main():
    """Main entry point"""
    ord_company = OrdCompany()
    await ord_company.run()


if __name__ == "__main__":
    asyncio.run(main())
