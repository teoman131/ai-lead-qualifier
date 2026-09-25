# B2B AI Inbound Lead Qualifier & Automated CRM Dispatcher

An enterprise-ready AI microservice designed for high-velocity US service companies (logistics, roofing, commercial contractors, marketing agencies) to instantly qualify inbound customer inquiries, score purchasing intent, and sync records into sales pipelines in real-time.

## Business Impact
- **Instant Response SLA:** Cuts response time from hours to under 3 seconds.
- **Cost Reduction:** Eliminates 15+ hours/week of manual qualification performed by sales reps.
- **Conversion Uplift:** Flags high-intent enterprise buyers ($2k-$10k+ budget) and triggers immediate routing to stakeholders.

## Architecture & Data Flow
1. **Intake:** Inbound lead submissions via REST API (`/api/v1/qualify`).
2. **AI Evaluation:** BANT-framework scoring (Budget, Authority, Need, Urgency) powered by LLM JSON Mode.
3. **Instant Telegram Alert:** Immediate notification sent to the business owner/account executive for HOT opportunities.
4. **CRM Sync:** Real-time append to Google Sheets CRM pipeline via serverless webhook.

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn
- **AI Engine:** OpenAI GPT-4o-mini (structured JSON output)
- **Integrations:** Telegram Bot API, Google Apps Script / Google Sheets Webhook

## Quick Start

### 1. Clone & Install
```bash
git clone [https://github.com/your-username/ai-lead-qualifier.git](https://github.com/your-username/ai-lead-qualifier.git)
cd ai-lead-qualifier
pip install -r requirements.txt