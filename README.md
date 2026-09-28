# ⚡ AI B2B Lead Qualifier & Multi-Tenant Routing Engine

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Production%20Ready-009688.svg)
![Railway](https://img.shields.io/badge/Railway-Deployed-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-ready AI microservice designed for high-velocity B2B service companies (logistics, equipment rental, construction, legal) to instantly qualify inbound customer inquiries, score purchasing intent using BANT heuristics, and trigger 1-tap WhatsApp/Telegram follow-ups.

🚀 **Live Interactive Demo:** https://ai-lead-qualifier-production-fa3b.up.railway.app/demo

---

## 💼 Business Impact

- **Instant Response SLA:** Reduces lead reaction time from hours to under 3 seconds.
- **1-Tap WhatsApp Closing:** Equips sales reps with pre-generated AI response drafts and direct deep-links (`wa.me` / `t.me`).
- **Multi-Tenant Routing:** Connect multiple client websites to a single backend cluster using dynamic webhook parameters (`?chat_id=...`).
- **Conversion Uplift:** Prioritizes high-ticket enterprise buyers and eliminates manual triage overhead.

---

## 🏗 System Architecture & Workflow

- **Inbound Lead Form** (Tilda, WordPress, Webhook)
  └──> **FastAPI Gateway** (/api/v1/webhook/form)
       └──> **BANT Heuristic & AI Scoring**
            ├──> **Telegram 1-Tap Action Card** (WhatsApp, Telegram, Gmail direct links)
            └──> **Google Sheets / CRM Webhook Sync**

---

## 🛠 Tech Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, HTTPX
- **Cloud Infrastructure:** Railway PaaS (24/7 Production Deploy)
- **Frontend Demo:** Tailwind CSS Responsive Sandbox (`/demo`)
- **Integrations:** Telegram Bot API, WhatsApp Deep Linking, Google Sheets CRM Webhooks

---

## 🚀 Quick Start

### 1. Clone & Setup
    git clone https://github.com/teoman131/ai-lead-qualifier.git
    cd ai-lead-qualifier
    pip install -r requirements.txt

### 2. Environment Variables
Create a `.env` file in the root folder:

    TELEGRAM_BOT_TOKEN="your_bot_token"
    TELEGRAM_CHAT_ID="your_default_chat_id"
    CRM_WEBHOOK_URL="optional_google_sheets_webhook_url"

### 3. Run Locally
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Visit `http://127.0.0.1:8000/demo` for the test portal or `http://127.0.0.1:8000/docs` for Swagger UI.

---

## 🌐 Multi-Tenant Integration Example

To connect an external website form to a specific Telegram chat, submit lead data via POST to:

    https://ai-lead-qualifier-production-fa3b.up.railway.app/api/v1/webhook/form?chat_id=YOUR_CLIENT_CHAT_ID&company_name=SpecTechnika147
https://ai-lead-qualifier-production-fa3b.up.railway.app/api/v1/webhook/form?chat_id=YOUR_CLIENT_CHAT_ID&company_name=SpecTechnika147
