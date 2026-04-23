# Aurelius Cyberdeck

Aurelius is an autonomous agent-to-agent nanopayment orchestration engine built on the **Arc Network** using **Circle's Programmable Wallets (x402)**.

## 🚀 Vision
Aurelius enables AI agents to coordinate and settle micro-transactions for high-frequency validation tasks (hallucination checks, PII scanning, safety filters) without human intervention. By utilizing the **x402 standard**, agents can verify payment intent and trust scores instantly, reducing latency in autonomous machine economies.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python), PostgreSQL (Supabase), Circle W3S SDK
- **Frontend**: React (Vite), Framer Motion, Vanilla CSS (Cyberpunk Aesthetics)
- **AI**: Google Gemini (Orchestrator & Validator reasoning)
- **Settlement**: Circle Programmable Wallets (Arc Testnet)

## 📡 Core Infrastructure
- **Orchestrator**: Routes user prompts through a network of specialized validation agents.
- **Validators**: Specialized agents (Hallucination, PII, Safety) that charge USDC micro-fees for their inference.
- **x402 Protocol**: Real-time payment verification via EIP-712 signatures.
- **Arc Testnet**: High-speed, low-cost settlement layer for agent-to-agent commerce.

## 📦 Deployment
- **API**: [https://aurelius-production-2ec3.up.railway.app](https://aurelius-production-2ec3.up.railway.app)
- **Dashboard**: [https://lightseagreen-bear-113896.hostingersite.com](https://lightseagreen-bear-113896.hostingersite.com)

## 🔧 Local Setup
1. Clone the repository.
2. Install dependencies: `npm install` (frontend) and `pip install -r requirements.txt` (backend).
3. Set up environment variables in `.env`.
4. Run dev servers: `npm run dev` and `uvicorn app.main:app`.

---
*Built for the Circle AI & Agentic Hackathon 2026.*
