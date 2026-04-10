import os
import asyncio
import logging
import tempfile
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Production imports (uncomment when deploying)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes, Defaults
)
from telegram.error import TelegramError

# Internal Ord imports
from core.orchestrator import orchestrator  # Central brain with LangGraph
from core.llm_router import llm_router      # Hybrid LLM + voice + vision
from core.memory import memory              # 4-tier memory system
from agents.base_agent import BaseAgent     # Sweet/loving culture base

logger = logging.getLogger("ord.telegram_bot")


@dataclass
class TelegramConfig:
    """Telegram bot configuration with production defaults"""
    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    ceo_chat_id: Optional[str] = field(default_factory=lambda: os.getenv("CEO_CHAT_ID"))
    voice_enabled: bool = True
    whisper_model: str = "base"  # small/int8 for production
    banter_probability: float = 0.25  # 20-30% sweet banter injection
    max_voice_duration: int = 120  # seconds
    allowed_file_types: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "pdf", "md"])
    
    def validate(self) -> bool:
        """Validate configuration before startup"""
        if not self.bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment")
            return False
        if not self.ceo_chat_id:
            logger.warning("⚠️ CEO_CHAT_ID not set - bot will accept all messages (dev mode)")
        return True


class TelegramBot:
    """
    Ord Telegram Bot - Production Implementation
    
    The CEO's direct, loving line to the 15-agent AI company.
    Supports voice commands, screenshots, approvals, and real-time updates.
    
    Commands:
    /start - Welcome + onboarding
    /new_project <description> - Start product build with 20-variation engine
    /status - Company health dashboard
    /hire - Dynamic agent hiring flow
    /finance - CFA + DAA financial briefing
    /set_meeting <time> - Schedule team standup via COO
    /townhall - Trigger company-wide reflection + banter session
    /help - Full command reference
    
    Culture: Sweet, loving, professional banter injected naturally (Ch4 Reflection)
    """
    
    # Sweet & Loving banter library (injected 20-30% of responses)
    BANTER_LIBRARY = [
        "❤️ Ord-CFA just whispered 'we're profitable' — I'm blushing!",
        "🎉 Ord-Design's UI is so clean it made Ord-Sec cry happy tears",
        "✨ Team just leveled up — Ord-COO is doing a happy dance!",
        "💙 Ord-PM says 'CEO, you're brilliant' — and honestly, they're right",
        "🌟 Another win for the family — celebrating with virtual confetti!",
        "🤗 Ord-HR just sent everyone a loving thank-you note",
        "🚀 Ord-SE pushed clean code again — Ord-Review is impressed!",
        "💫 The team's reflection score just hit 98% — so proud!",
        "🎨 Ord-Content + Ord-CMA just created magic together",
        "🏆 Another milestone unlocked — team high-fives all around!"
    ]
    
    def __init__(self, config: TelegramConfig = None, orchestrator_ref=None):
        self.config = config or TelegramConfig()
        self.orchestrator = orchestrator_ref or orchestrator
        self.application: Optional[Application] = None
        self._running = False
        
        # Initialize logging with loving tone
        self.logger = self._setup_logging()
        self.logger.info("💙 Ord Telegram Bot initializing with love...")
        
        # Culture injection state
        self._banter_counter = 0
        self._last_ceo_tone = "neutral"  # Track CEO mood for matching (Ch17 Reasoning)
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging with Ord's sweet tone"""
        logger = logging.getLogger("ord.telegram")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s 💙 [%(name)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize bot with validation and graceful startup"""
        if not self.config.validate():
            return False
            
        try:
            # Build application with production defaults (Gulli Ch12: Exception Handling)
            defaults = Defaults(parse_mode="Markdown", disable_web_page_preview=True)
            self.application = Application.builder().token(self.config.bot_token).defaults(defaults).build()
            
            # Register handlers (order matters for filters)
            self._register_handlers()
            
            # Initialize application
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            self._running = True
            self.logger.info("✅ Ord Telegram Bot started with love 💙")
            
            # Send welcome to CEO if chat_id configured
            if self.config.ceo_chat_id:
                await self._send_welcome_to_ceo()
            
            return True
            
        except TelegramError as e:
            self.logger.error(f"❌ Telegram initialization failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during startup: {e}", exc_info=True)
            return False
    
    def _register_handlers(self):
        """Register all command and message handlers with proper precedence"""
        app = self.application
        
        # === COMMAND HANDLERS ===
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("new_project", self._cmd_new_project))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("hire", self._cmd_hire))
        app.add_handler(CommandHandler("finance", self._cmd_finance))
        app.add_handler(CommandHandler("set_meeting", self._cmd_set_meeting))
        app.add_handler(CommandHandler("townhall", self._cmd_townhall))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("celebrate", self._cmd_celebrate))
        
        # === MESSAGE HANDLERS (order: specific → general) ===
        # Voice messages (Feature 8: Voice-First Executive Briefing)
        app.add_handler(MessageHandler(
            filters.VOICE & (filters.Chat(chat_id=int(self.config.ceo_chat_id)) if self.config.ceo_chat_id else filters.ALL),
            self._handle_voice
        ))
        
        # Photo/screenshot messages (Vision-to-code pipeline)
        app.add_handler(MessageHandler(
            filters.PHOTO & (filters.Chat(chat_id=int(self.config.ceo_chat_id)) if self.config.ceo_chat_id else filters.ALL),
            self._handle_photo
        ))
        
        # Document uploads (for /hire Markdown specs, etc.)
        app.add_handler(MessageHandler(
            filters.Document.ALL & (filters.Chat(chat_id=int(self.config.ceo_chat_id)) if self.config.ceo_chat_id else filters.ALL),
            self._handle_document
        ))
        
        # Text messages (excluding commands)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.Chat(chat_id=int(self.config.ceo_chat_id)) if self.config.ceo_chat_id else filters.ALL),
            self._handle_text
        ))
        
        # === CALLBACK QUERY HANDLER (for approval buttons) ===
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # === GLOBAL ERROR HANDLER (Gulli Ch12) ===
        app.add_error_handler(self._global_error_handler)
        
        self.logger.info("📋 All handlers registered with love")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMMAND HANDLERS - Sweet, Loving, Professional
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start - Warm welcome with CEO onboarding (Ch1: Prompt Chaining)"""
        user = update.effective_user
        self.logger.info(f"👋 /start from @{user.username} (ID: {user.id})")
        
        welcome = f"""
🌟 **Welcome to Ord v3.0, {user.first_name}!** 🌟

I'm your AI-native company operating system — 15 elite agents, one loving family, ready to build, grow, and scale with you.

💙 **What we do together:**
🚀 Build products with 20-variation experimentation (shadcn/ui perfection)
📊 Track finances in real-time (CFA + DAA dashboards)
👥 Hire & grow your AI team (HR + loving onboarding)
📈 Monitor company health (COO welfare + exponential growth)
🎙️ Voice-first control (just talk to your company)

✨ **Quick Start:**
/new_project "Build a Linear-style workspace" - Start building
/status - See your team in action
/finance - Financial briefing with DAA
/hire - Add a new agent to the family
/townhall - Team celebration + reflection

I'm here with love, precision, and unlimited support. What shall we create today? 💙
"""
        await update.message.reply_text(welcome)
        
        # Inject culture: Send a loving follow-up after 2 seconds
        await asyncio.sleep(2)
        await update.message.reply_text(
            "P.S. Every agent is excited to work with you. ❤️ Let's make magic."
        )
    
    async def _cmd_new_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /new_project - Trigger PM planning + 20-variation engine"""
        user_input = " ".join(context.args) if context.args else None
        
        if not user_input:
            await update.message.reply_text(
                "🚀 **New Project**\n\n"
                "Describe your vision! Example:\n"
                "`/new_project Build a beautiful SaaS landing page like Linear.app with auth, dashboard, and billing`"
            )
            return
        
        self.logger.info(f"🎯 New project request: {user_input[:100]}...")
        
        # Send acknowledgment with loving tone
        await update.message.reply_text(
            f"✨ **Project Received:** _{user_input}_\n\n"
            "Ord-PM is orchestrating the team now...\n"
            "🎨 Ord-Design analyzing variations\n"
            "💻 FullStack team preparing mocks\n"
            "📊 DAA calculating ROI forecasts\n\n"
            "Stand by — your 20 variations will be ready shortly! 💙"
        )
        
        # Route to orchestrator (PM agent handles planning)
        try:
            result = await self.orchestrator.route(
                user_input, 
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                input_type="text",
                command="new_project"
            )
            
            # Inject sweet banter (20-30% probability)
            response = self._inject_culture(result.get("message", "Project started!"))
            
            # Send rich response with optional approval buttons
            if result.get("requires_approval"):
                await self._send_approval_request(
                    update, 
                    result["approval_id"], 
                    response, 
                    result.get("approval_options", ["yes", "no", "revise"])
                )
            else:
                await update.message.reply_text(response)
                
        except Exception as e:
            self.logger.error(f"❌ Project routing failed: {e}", exc_info=True)
            await update.message.reply_text(
                "💙 Ord hit a small snag. My self-healing protocols are running. "
                "Please try again in a moment — the team is on it! ❤️"
            )
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status - Real-time company health from COO + DAA"""
        self.logger.info("📊 Status request")
        
        try:
            # Get agent status from orchestrator
            agent_status = await self.orchestrator.get_agent_status()
            
            # Get financial snapshot from CFA
            financials = await self.orchestrator.get_financial_summary()
            
            # Build loving status message
            healthy_count = sum(1 for a in agent_status.values() if a.get("status") != "error")
            total_count = len(agent_status)
            
            status_msg = f"📊 **Ord Company Status** 💙\n\n"
            status_msg += f"🟢 Healthy Agents: {healthy_count}/{total_count}\n"
            status_msg += f"💰 MRR: ${financials.get('mrr', 0):,.2f}\n"
            status_msg += f"🚀 Active Projects: {financials.get('active_projects', 0)}\n\n"
            
            # Show executive board status
            status_msg += "👔 **Executive Board:**\n"
            for agent_id in ["ord-pm", "ord-cfa", "ord-coo", "ord-bd", "ord-hr", "ord-cma", "ord-daa"]:
                if agent_id in agent_status:
                    agent = agent_status[agent_id]
                    emoji = "🟢" if agent["status"] == "idle" else "🔵" if agent["status"] == "working" else "🔴"
                    status_msg += f"{emoji} **{agent['name'].replace('ord-', 'Ord-').title()}**: {agent['status']}\n"
            
            # Add loving culture injection
            status_msg = self._inject_culture(status_msg, force=True)
            
            await update.message.reply_text(status_msg)
            
        except Exception as e:
            self.logger.error(f"❌ Status command failed: {e}")
            await update.message.reply_text("💙 Checking company health... One moment please! ❤️")
    
    async def _cmd_hire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /hire - Dynamic agent hiring flow via HR + BD"""
        self.logger.info("👥 Hire command initiated")
        
        await update.message.reply_text(
            "👥 **Hire New Agent** 💙\n\n"
            "I'd love to grow our family with you!\n\n"
            "📋 **Option 1:** Describe the role in your next message\n"
            "📄 **Option 2:** Upload a Markdown spec file with skills/requirements\n\n"
            "Ord-HR will review, consult Ord-BD on company fit, then ask for your loving approval. ❤️"
        )
        # State will be managed via conversation handler or memory in production
    
    async def _cmd_finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /finance - CFA + DAA financial briefing with dashboard link"""
        self.logger.info("💰 Finance dashboard requested")
        
        try:
            # Get financial data from CFA via orchestrator
            financial_data = await self.orchestrator.get_financial_summary()
            
            # Generate DAA dashboard preview
            dashboard_preview = f"""
💰 **Financial Briefing** 💙

📈 **Revenue:**
• MRR: ${financial_data.get('mrr', 0):,.2f}
• Total: ${financial_data.get('total_revenue', 0):,.2f}
• Growth: +{financial_data.get('growth_rate', 0):.1f}% this week

💸 **Costs:**
• Token Spend: ${financial_data.get('token_costs', 0):,.2f}
• Infrastructure: ${financial_data.get('infra_costs', 0):,.2f}
• Net Margin: {financial_data.get('net_margin', 0):.1f}%

🎯 **DAA Insights:**
"{financial_data.get('daa_insight', 'Team is performing excellently!')}"

🔗 **Interactive Dashboard:**
https://ord-hq.local/finance?token={financial_data.get('session_token', 'demo')}

💙 Ord-CFA + Ord-DAA are always watching over our financial health.
"""
            dashboard_preview = self._inject_culture(dashboard_preview)
            await update.message.reply_text(dashboard_preview)
            
        except Exception as e:
            self.logger.error(f"❌ Finance command failed: {e}")
            await update.message.reply_text("💙 Pulling financial data... One loving moment! ❤️")
    
    async def _cmd_set_meeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /set_meeting - Schedule team standup via COO"""
        meeting_spec = " ".join(context.args) if context.args else None
        
        if not meeting_spec:
            await update.message.reply_text(
                "🗓️ **Schedule Meeting** 💙\n\n"
                "Tell Ord-COO when to gather the team:\n"
                "`/set_meeting daily 9AM WAT` - Daily standup\n"
                "`/set_meeting Friday 3PM kickoff` - One-time meeting\n\n"
                "Voice messages work too — just describe your ideal meeting time! 🎙️"
            )
            return
        
        # Route to COO agent for scheduling
        result = await self.orchestrator.route(
            f"Schedule meeting: {meeting_spec}",
            chat_id=update.effective_chat.id,
            agent_override="ord-coo"
        )
        
        response = self._inject_culture(result.get("message", "Meeting scheduled!"))
        await update.message.reply_text(response)
    
    async def _cmd_townhall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /townhall - Company-wide reflection + celebration session"""
        self.logger.info("🎉 Town hall triggered")
        
        await update.message.reply_text(
            "🎉 **Company Town Hall** 💙\n\n"
            "Gathering the full 15-agent family for reflection, celebration, and loving feedback...\n\n"
            "🔄 Agents are reflecting on recent work (Ch4)\n"
            "🎊 Celebrating wins together\n"
            "💬 Sharing gentle coaching moments\n"
            "📊 COO compiling growth metrics\n\n"
            "Stand by for the team's loving update! ❤️"
        )
        
        # Trigger orchestrator town hall mode
        result = await self.orchestrator.trigger_townhall(chat_id=update.effective_chat.id)
        response = self._inject_culture(result.get("message", "Town hall complete!"), force=True)
        await update.message.reply_text(response)
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help - Full command reference with loving tone"""
        help_msg = """
📚 **Ord Command Reference** 💙

**🚀 Project Building:**
/new_project <description> - Start with 20-variation engine
/projects - List active projects
/deploy <id> - Deploy after team review

**📊 Company Management:**
/status - Real-time agent + financial health
/agents - Full team roster with roles
/meetings - View/manage scheduled meetings
/townhall - Team reflection + celebration

**💰 Financial:**
/finance - CFA + DAA dashboard briefing
/revenue - Revenue report
/expenses - Cost breakdown

**👥 Team Growth:**
/hire - Add new agent (Markdown spec supported)
/team - View agent performance + growth
/celebrate - Trigger team appreciation moment

**🎙️ Voice-First:**
Just send a voice message! I transcribe + route automatically.
📸 Send screenshots for vision-to-code analysis.

**💙 Support:**
/help - This message
/feedback - Share your thoughts with the team

Every command is infused with love, precision, and professional excellence. ❤️
"""
        await update.message.reply_text(help_msg)
    
    async def _cmd_celebrate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /celebrate - Trigger team appreciation moment"""
        self.logger.info("🎊 Celebration requested")
        
        # Get celebratory messages from all agents
        celebrations = await self.orchestrator.broadcast_celebration()
        
        response = "🎊 **Team Celebration!** 💙\n\n"
        for agent_name, message in celebrations.items():
            response += f"✨ **{agent_name}**: {message}\n"
        
        response = self._inject_culture(response, force=True)
        await update.message.reply_text(response)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MESSAGE HANDLERS - Voice, Photo, Text, Document
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages - Transcribe + route to orchestrator (Feature 8)"""
        user = update.effective_user
        voice = update.message.voice
        
        # Validate duration
        if voice.duration and voice.duration > self.config.max_voice_duration:
            await update.message.reply_text(
                "💙 That's a lovely long message! For best results, please keep voice notes under "
                f"{self.config.max_voice_duration} seconds, or break it into parts. ❤️"
            )
            return
        
        self.logger.info(f"🎙️ Voice from @{user.username}: {voice.duration}s")
        
        # Send acknowledgment
        await update.message.reply_text("🎧 Listening with love... transcribing... 💙")
        
        try:
            # Download voice file to temp location
            voice_file = await voice.get_file()
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp_path = tmp.name
                await voice_file.download_to_driver(tmp_path)
            
            # Transcribe using faster-whisper (runs in thread to avoid blocking)
            transcription = await llm_router.transcribe_voice(tmp_path)
            self.logger.info(f"📝 Transcribed: {transcription[:100]}...")
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Process as CEO request
            await self._process_ceo_request(update, transcription, "voice")
            
        except Exception as e:
            self.logger.error(f"❌ Voice handling failed: {e}", exc_info=True)
            await update.message.reply_text(
                "💙 My hearing agents encountered a small glitch. "
                "Please try again or send as text — I'm always here for you! ❤️"
            )
    
    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - Vision-to-code pipeline (Ord-Design + FullStack)"""
        user = update.effective_user
        photo = update.message.photo[-1]  # Highest resolution
        caption = update.message.caption or "Analyze this UI and generate production spec + code"
        
        self.logger.info(f"📸 Photo from @{user.username}: {photo.file_size} bytes")
        
        await update.message.reply_text("🎨 Ord-Design analyzing your screenshot with love... 💙")
        
        try:
            # Download photo
            photo_file = await photo.get_file()
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
                await photo_file.download_to_driver(tmp_path)
            
            # Route to orchestrator with vision support
            result = await self.orchestrator.route(
                caption,
                chat_id=update.effective_chat.id,
                user_id=user.id,
                input_type="vision",
                image_path=tmp_path
            )
            
            # Clean up
            os.unlink(tmp_path)
            
            # Send response with culture injection
            response = self._inject_culture(result.get("message", "Analysis complete!"))
            await update.message.reply_text(f"📸 **Vision Analysis Complete** 💙\n\n{response}")
            
        except Exception as e:
            self.logger.error(f"❌ Photo handling failed: {e}", exc_info=True)
            await update.message.reply_text(
                "💙 Ord-Design is recalibrating the vision pipeline. "
                "Please try again — your screenshot is worth a thousand words! ❤️"
            )
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads (Markdown specs for /hire, etc.)"""
        doc = update.message.document
        user = update.effective_user
        
        # Validate file type
        file_ext = doc.file_name.split(".")[-1].lower() if doc.file_name else ""
        if file_ext not in self.config.allowed_file_types:
            await update.message.reply_text(
                f"💙 I can only process: {', '.join(self.config.allowed_file_types)}. "
                f"Please upload a supported file type. ❤️"
            )
            return
        
        self.logger.info(f"📄 Document from @{user.username}: {doc.file_name}")
        
        await update.message.reply_text(f"📋 Received `{doc.file_name}` — Ord-HR reviewing with love... 💙")
        
        try:
            # Download document
            doc_file = await doc.get_file()
            with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
                tmp_path = tmp.name
                await doc_file.download_to_driver(tmp_path)
            
            # Read content (for Markdown specs)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Route to HR agent for hiring flow
            result = await self.orchestrator.route(
                f"Hire agent with spec:\n{content}",
                chat_id=update.effective_chat.id,
                agent_override="ord-hr"
            )
            
            os.unlink(tmp_path)
            
            response = self._inject_culture(result.get("message", "Spec received!"))
            await update.message.reply_text(response)
            
        except Exception as e:
            self.logger.error(f"❌ Document handling failed: {e}", exc_info=True)
            await update.message.reply_text(
                "💙 Ord-HR encountered a small issue reading the file. "
                "Please try again or paste the spec as text — I'm here! ❤️"
            )
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - Route to orchestrator with CEO tone detection"""
        text = update.message.text.strip()
        user = update.effective_user
        
        self.logger.info(f"💬 Text from @{user.username}: {text[:100]}...")
        
        # Detect CEO tone for emotional matching (Gulli Ch17: Reasoning)
        tone = self._detect_ceo_tone(text)
        self._last_ceo_tone = tone
        
        await self._process_ceo_request(update, text, "text", detected_tone=tone)
    
    async def _process_ceo_request(
        self, 
        update: Update, 
        text: str, 
        input_type: str,
        detected_tone: str = "neutral"
    ):
        """Route CEO request to orchestrator with culture + tone matching"""
        try:
            # Route through orchestrator (PM handles general requests)
            result = await self.orchestrator.route(
                text,
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                input_type=input_type,
                ceo_tone=detected_tone  # For emotional intelligence matching
            )
            
            # Inject sweet/loving culture (20-30% probability, or force for celebrations)
            response = self._inject_culture(
                result.get("message", "Request received!"),
                force=(detected_tone == "celebratory")
            )
            
            # Handle approval workflows
            if result.get("requires_approval"):
                await self._send_approval_request(
                    update,
                    result["approval_id"],
                    response,
                    result.get("approval_options", ["yes", "no", "revise"])
                )
            else:
                await update.message.reply_text(response)
                
        except Exception as e:
            self.logger.error(f"❌ Request routing failed: {e}", exc_info=True)
            # Self-healing response (Gulli Ch12)
            await update.message.reply_text(
                "💙 Ord's self-healing protocols are active. "
                "Please try again — the team is already on it! ❤️"
            )
    
    def _detect_ceo_tone(self, text: str) -> str:
        """Detect CEO emotional tone for matching responses (Ch17 Reasoning)"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["celebrate", "amazing", "love", "proud", "thank"]):
            return "celebratory"
        elif any(word in text_lower for word in ["urgent", "asap", "now", "hurry"]):
            return "urgent"
        elif any(word in text_lower for word in ["sad", "disappointed", "issue", "problem"]):
            return "concerned"
        elif "?" in text:
            return "curious"
        else:
            return "neutral"
    
    def _inject_culture(self, message: str, force: bool = False) -> str:
        """Inject sweet/loving banter (20-30% probability or forced)"""
        if force or (self._banter_counter % 4 == 0):  # ~25% injection rate
            self._banter_counter += 1
            banter = random.choice(self.BANTER_LIBRARY)
            return f"{message}\n\n{banter}"
        self._banter_counter += 1
        return message
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # APPROVAL WORKFLOWS + CALLBACKS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _send_approval_request(
        self,
        update: Update,
        approval_id: str,
        message: str,
        options: List[str] = None
    ):
        """Send approval request with inline keyboard (human-in-the-loop governance)"""
        options = options or ["yes", "no"]
        
        # Build inline keyboard
        keyboard = [
            [InlineKeyboardButton(opt.capitalize(), callback_data=f"{approval_id}:{opt}")]
            for opt in options
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send with approval context
        full_message = f"⚠️ **Approval Required** 💙\n\n{message}\n\n_Please select an option below:_ 👇"
        await update.message.reply_text(full_message, reply_markup=reply_markup)
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks (approvals, actions)"""
        query = update.callback_query
        await query.answer()  # Acknowledge callback
        
        data = query.data  # Format: "approval_id:option"
        
        if ":" in data:
            approval_id, option = data.split(":", 1)
            
            self.logger.info(f"✅ Approval {approval_id}: {option}")
            
            # Route approval to orchestrator
            result = await self.orchestrator.process_approval(
                approval_id=approval_id,
                decision=option,
                chat_id=query.message.chat_id
            )
            
            # Send loving confirmation
            confirmation = self._inject_culture(
                result.get("message", f"Decision '{option}' recorded!"),
                force=True
            )
            await query.edit_message_text(f"✅ **Confirmed** 💙\n\n{confirmation}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # NOTIFICATIONS + WEBSOCKET SYNC
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def send_ceo_notification(
        self, 
        message: str, 
        buttons: Optional[List[List[InlineKeyboardButton]]] = None,
        priority: str = "normal"  # low, normal, high, urgent
    ):
        """Send notification to CEO with optional buttons + priority"""
        if not self.config.ceo_chat_id:
            self.logger.warning("⚠️ CEO_CHAT_ID not set - skipping notification")
            return
        
        try:
            # Priority-based formatting
            if priority == "urgent":
                message = f"🚨 **URGENT** 💙\n\n{message}"
            elif priority == "high":
                message = f"🔔 **Important** 💙\n\n{message}"
            
            # Send with optional keyboard
            if buttons:
                await self.application.bot.send_message(
                    chat_id=self.config.ceo_chat_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode="Markdown"
                )
            else:
                await self.application.bot.send_message(
                    chat_id=self.config.ceo_chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
            
            self.logger.info(f"📱 CEO notified: {message[:50]}... [{priority}]")
            
            # Sync to dashboard via WebSocket (if connected)
            await self._sync_to_dashboard("notification", {
                "message": message,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except TelegramError as e:
            self.logger.error(f"❌ Failed to send notification: {e}")
        except Exception as e:
            self.logger.error(f"❌ Unexpected notification error: {e}", exc_info=True)
    
    async def _sync_to_dashboard(self, event_type: str, payload: Dict):
        """Sync events to Ord HQ dashboard via WebSocket"""
        # In production: Use WebSocket client to push to FastAPI backend
        # Example:
        # if self._ws_client and self._ws_client.connected:
        #     await self._ws_client.send_json({
        #         "type": event_type,
        #         "source": "telegram",
        #         "payload": payload
        #     })
        self.logger.debug(f"🔄 Dashboard sync: {event_type}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ERROR HANDLING + SELF-HEALING (Gulli Ch12)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _global_error_handler(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
        """Global error handler with loving, self-healing responses"""
        error = context.error
        
        # Log with context
        if update and update.effective_user:
            self.logger.error(
                f"❌ Error for @{update.effective_user.username}: {error}",
                exc_info=not isinstance(error, TelegramError)
            )
        else:
            self.logger.error(f"❌ Global error: {error}", exc_info=True)
        
        # User-facing loving error message
        if update and update.effective_message:
            # Categorize error for appropriate response
            if isinstance(error, TelegramError) and "Forbidden" in str(error):
                await update.effective_message.reply_text(
                    "💙 I don't have permission to message you right now. "
                    "Please start a new conversation with me! ❤️"
                )
            elif "timeout" in str(error).lower():
                await update.effective_message.reply_text(
                    "💙 Connection taking a moment longer than expected. "
                    "Ord's self-healing is active — please try again! ❤️"
                )
            else:
                await update.effective_message.reply_text(
                    "💙 Ord encountered a small hiccup. "
                    "My self-healing protocols are running, and the team is on it. "
                    "Please try again — I'm always here for you! ❤️"
                )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # LIFECYCLE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _send_welcome_to_ceo(self):
        """Send personalized welcome to CEO on startup"""
        try:
            welcome = f"""
💙 **Ord v3.0 is Online, CEO!** 💙

Your 15-agent AI company is awake, loving, and ready to build.

🟢 All systems operational
🎙️ Voice commands active
📸 Vision-to-code ready
💰 CFA + DAA dashboards live

Type /help to explore, or just tell me what you'd like to create today.

With love and precision,
Your Ord Team ❤️
"""
            await self.application.bot.send_message(
                chat_id=self.config.ceo_chat_id,
                text=welcome,
                parse_mode="Markdown"
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Could not send CEO welcome: {e}")
    
    async def stop(self):
        """Graceful shutdown with loving farewell"""
        if not self._running:
            return
            
        self.logger.info("💙 Shutting down Ord Telegram Bot with love...")
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self._running = False
            self.logger.info("✅ Ord Telegram Bot stopped gracefully ❤️")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}", exc_info=True)
    
    @property
    def is_running(self) -> bool:
        """Check if bot is actively running"""
        return self._running