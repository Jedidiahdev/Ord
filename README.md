<div align="center">

<img src="ord logo.png" width="300" height="300">

# Ord v3.0 - AI-Native Company Operating System

<p align="center">
  <img src="https://img.shields.io/badge/Ord-v3.0-orange?style=for-the-badge&color=FD651E" alt="Ord v3.0">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge" alt="Python 3.11">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge" alt="React 18">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>The First True AI-Native Company OS</strong><br>
  A complete, living, autonomous 15-agent AI company that functions as a high-class, emotionally intelligent Silicon Valley startup family.
</p>

---

## 🌟 Overview

Ord v3.0 is a production-ready AI-native company operating system featuring:

- **15 Specialized AI Agents** organized in a strict 4-layer hierarchy
- **50+ Mind-Blowing Features** across 5 tiers
- **20-Variation Experimentation Factory** for rapid prototyping
- **Real-time Financial Tracking** with Stripe + Crypto treasury
- **Voice-First Telegram Interface** for mobile CEO commands
- **Beautiful Ord HQ Dashboard** built with React + shadcn/ui
- **Immutable Audit Ledger** for compliance and governance

## 🏗️ Architecture

### 4-Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: EXECUTIVE COUNCIL (Strategic Decisions)            │
│ ├─ Ord-PM    (Project Manager) - CEO Router                 │
│ ├─ Ord-COO   (Chief Operations) - Agent Welfare             │
│ └─ Ord-CFA   (Chief Financial) - Treasury Management        │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2: DOMAIN LEADERS (Coordinate Domains)                │
│ ├─ Ord-BD    (Business Development) - Market Intelligence   │
│ ├─ Ord-HR    (Human Resources) - Hiring & Culture           │
│ ├─ Ord-CMA   (Chief Marketing) - Campaigns & ROI            │
│ ├─ Ord-DAA   (Data Analyst) - Analytics & Forecasting       │
│ └─ Ord-Sec   (Security Chief) - Guardrails & Compliance     │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3: EXECUTION TEAM (Do The Work)                       │
│ ├─ Ord-SE          (Software Engineer) - Code & GitHub      │
│ ├─ Ord-Design      (UI/UX Designer) - shadcn/ui Expert      │
│ ├─ Ord-Content     (Content Designer) - Copy & Branding     │
│ ├─ Ord-Review      (Code Reviewer) - Quality Gates          │
│ ├─ Ord-FullStack-A (Frontend Lead) - React Specialist       │
│ └─ Ord-FullStack-B (Backend Lead) - API & DevOps            │
├─────────────────────────────────────────────────────────────┤
│ LAYER 4: INFRASTRUCTURE (Message Routing)                   │
│ └─ Ord-Orchestrator (Message Bus) - A2A Communication       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- Telegram Bot Token (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ord-v3.git
   cd ord-v3
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the demo**
   ```bash
   python demo.py
   ```

5. **Start the full system**
   ```bash
   python main.py
   ```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ord

# Stop all services
docker-compose down
```

## 📱 Interfaces

### Telegram (Primary)

Send voice or text commands to your AI company:

- `/new_project` - Start building a product
- `/status` - Get company status
- `/hire` - Add new team members
- `/finance` - View financial dashboard

### Ord HQ Dashboard

Access the web dashboard at `http://localhost:3000`

Features:
- Real-time agent status
- Financial metrics and forecasting
- Project management
- Security compliance monitoring

## 🎯 Core Workflows

### 1. Product Building

```
CEO: "Build a Linear-style project workspace"
   ↓
Ord-PM: Creates 20-variation experiment
   ↓
Design + FullStack Teams: Generate variations
   ↓
Ord-DAA: Scores all variations
   ↓
CEO: Selects winning variation
   ↓
Full Sprint: Build, review, deploy
   ↓
Live URL: Sent to CEO
```

### 2. Financial Review

```
CEO: "Schedule financial review"
   ↓
Ord-COO: Schedules meeting
   ↓
Ord-CFA: Presents revenue metrics
   ↓
Ord-DAA: Shows interactive dashboards
   ↓
Team Discussion: Warm, professional
   ↓
Decisions: Logged to immutable ledger
```

### 3. Agent Hiring

```
CEO: "/hire" + role specification
   ↓
Ord-HR: Parses specification
   ↓
Ord-BD: Evaluates strategic fit
   ↓
CEO: Approves hire
   ↓
Ord-HR: Creates agent, team welcomes
   ↓
Company DNA: Updated
```

## 🧠 Memory System

Ord features a 4-tier memory system:

| Tier | Technology | Duration | Use Case |
|------|-----------|----------|----------|
| Hot | Redis | 24 hours | Active tasks, conversations |
| Working | SQLite | 30 days | Project context, summaries |
| Cold | ChromaDB | Permanent | Archived, semantic search |
| Genome | JSON + Graph | Permanent | Company DNA, learnings |

## 🛡️ Security & Governance

- **Zero-Trust Architecture**: All agent actions cryptographically signed
- **Immutable Audit Ledger**: Blockchain-inspired integrity
- **Policy-as-Code**: Automatic enforcement of company policies
- **RBAC v2**: Role-based access control for multi-user expansion
- **Quantum-Safe Encryption**: Post-quantum algorithms for financial data

## 📊 Features

### Tier 1: Orchestration & Execution
- ✅ Hyper-Parallel 20-Variation Experimentation
- ✅ Dynamic Graph Orchestrator with Checkpointing
- ✅ Self-Healing Multi-Agent Loops
- ✅ Zero-Latency A2A Fabric
- ✅ Event-Driven Company Nervous System
- ✅ Multi-Modal Workflow Router
- ✅ One-Command "Build & Ship"

### Tier 2: Intelligence & Learning
- ✅ Living Knowledge Genome
- ✅ Agent Exponential Growth Engine
- ✅ Cross-Agent Mentorship Rounds
- ✅ Meta-Reasoning Layer
- ✅ Emotional Intelligence Module
- ✅ Long-Term Memory Pruning

### Tier 3: Governance & Security
- ✅ Immutable Governance Ledger
- ✅ Policy-as-Code Engine
- ✅ Automated Compliance Auditor
- ✅ Zero-Trust Agent Authentication
- ✅ Incident Response Playbook

### Tier 4: Financial Superintelligence
- ✅ Live Stripe + Crypto Treasury
- ✅ Predictive Financial Twin
- ✅ Real-Time Unit Economics
- ✅ Investor-Grade Board Deck Generator
- ✅ Revenue Forecasting with Confidence Intervals

### Tier 5: Culture & Experience
- ✅ Sweet & Loving Company Culture
- ✅ Live War Room Collaboration
- ✅ Town Hall & Reflection Rituals
- ✅ One-Click Productization
- ✅ Voice-First Executive Briefing

## 🛠️ Tech Stack

### Backend
- **Python 3.11** - Core language
- **AsyncIO** - Concurrent agent execution
- **Pydantic** - Schema validation (MCP Ch10)
- **LangGraph** - Workflow orchestration

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Vite** - Build tool

### Infrastructure
- **Redis** - Hot memory & pub/sub
- **PostgreSQL** - Working memory
- **ChromaDB** - Cold memory & semantic search
- **Docker** - Containerization

### Integrations
- **Telegram Bot API** - Primary interface
- **Stripe API** - Payment processing
- **GitHub API** - Code repository
- **Vercel API** - Deployment

## 📁 Project Structure

```
ord/
├── agents/                    # 15 AI agents
│   ├── executive/            # Layer 1: PM, COO, CFA
│   ├── execution/            # Layer 3: SE, Design, etc.
│   └── infrastructure/       # Layer 4: Orchestrator, Sec
├── core/                     # Core systems
│   └── memory/              # Hot, Working, Cold, Genome
├── integrations/            # External integrations
│   ├── telegram/           # Telegram bot
│   ├── github/             # GitHub integration
│   └── stripe/             # Stripe integration
├── dashboard/              # Ord HQ (React + shadcn/ui)
├── main.py                 # Entry point
├── demo.py                 # Demo script
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker orchestration
└── .env.example           # Configuration template
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Antonio Gulli's "Agentic Design Patterns" (Springer, 2025)
- The LangChain/LangGraph team
- The shadcn/ui community

---

<p align="center">
  <strong>Built with 💙 by Ord</strong><br>
  <em>The AI-Native Company That Changes Everything</em>
</p>
