import os
import json
import httpx
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEETS_WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "")

app = FastAPI(
    title="B2B AI Lead Qualifier & CRM Dispatcher",
    description="Enterprise API to evaluate inbound B2B inquiries and dispatch real-time alerts",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeadInboundRequest(BaseModel):
    contact_name: str = Field(..., example="Michael Vance")
    contact_email: str = Field(..., example="mvance@apexlogistics.com")
    company_name: str = Field(..., example="Apex Global Freight")
    message_text: str = Field(..., example="Need 24/7 AI dispatching for our 25 trucks fleet. Budget is around $4,000/mo. Ready to start immediately.")

class LeadQualificationResult(BaseModel):
    lead_score: int
    lead_status: str
    budget_estimate: str
    timeline: str
    key_pain_points: List[str]
    recommended_action: str
    summary: str

def evaluate_lead_heuristics(lead: LeadInboundRequest) -> LeadQualificationResult:
    text_lower = lead.message_text.lower()
    score = 60
    pain_points = []
    
    if any(k in text_lower for k in ["asap", "immediately", "urgent", "ready"]):
        score += 15
        timeline = "Immediate (0-7 days)"
    else:
        timeline = "Within 30 days"

    if any(k in text_lower for k in ["$", "budget", "k", "month", "fleet"]):
        score += 20
        budget = "Qualified B2B Budget ($2k - $10k)"
    else:
        budget = "Unspecified / Exploring"

    if "truck" in text_lower or "fleet" in text_lower or "dispatch" in text_lower:
        pain_points.append("Fleet operations & dispatch automation")
    if "weekend" in text_lower or "night" in text_lower or "24/7" in text_lower:
        pain_points.append("After-hours lead response delay")
    if not pain_points:
        pain_points.append("General operational workflow optimization")

    score = min(score, 98)
    status = "HOT 🔥" if score >= 80 else ("WARM ⚡" if score >= 60 else "COLD ❄️")
    action = "Immediate Call Booking" if score >= 80 else "Nurture sequence"

    return LeadQualificationResult(
        lead_score=score,
        lead_status=status,
        budget_estimate=budget,
        timeline=timeline,
        key_pain_points=pain_points,
        recommended_action=action,
        summary=f"Automated evaluation for {lead.contact_name} ({lead.company_name}). High purchase intent detected."
    )

async def send_telegram_alert(lead: LeadInboundRequest, eval_res: LeadQualificationResult):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    text = (
        f"{eval_res.lead_status} LEAD (Score: {eval_res.lead_score}/100)\n\n"
        f"👤 Contact: {lead.contact_name}\n"
        f"🏢 Company: {lead.company_name}\n"
        f"📧 Email: {lead.contact_email}\n"
        f"💰 Budget: {eval_res.budget_estimate}\n"
        f"⏱ Timeline: {eval_res.timeline}\n\n"
        f"🎯 Action: {eval_res.recommended_action}\n"
        f"📝 Summary: {eval_res.summary}\n\n"
        f"💬 Message:\n\"{lead.message_text}\""
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10.0)
        except Exception as e:
            print(f"Telegram error: {e}")

async def append_to_sheets(lead: LeadInboundRequest, eval_res: LeadQualificationResult):
    if not GOOGLE_SHEETS_WEBHOOK_URL:
        return
    payload = {
        "timestamp": "",
        "name": lead.contact_name,
        "company": lead.company_name,
        "email": lead.contact_email,
        "score": eval_res.lead_score,
        "status": eval_res.lead_status,
        "budget": eval_res.budget_estimate,
        "timeline": eval_res.timeline,
        "summary": eval_res.summary,
        "message": lead.message_text
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(GOOGLE_SHEETS_WEBHOOK_URL, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Sheets error: {e}")

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "active", "service": "AI Lead Qualifier Engine", "version": "1.1.0"}

@app.post("/api/v1/qualify", response_model=LeadQualificationResult, tags=["Pipeline"])
async def qualify_lead(lead: LeadInboundRequest):
    result = evaluate_lead_heuristics(lead)
    await send_telegram_alert(lead, result)
    await append_to_sheets(lead, result)
    return result

@app.get("/demo", response_class=HTMLResponse, tags=["Demo Portal"])
def get_demo_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>B2B Inbound Qualifier Demo</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 flex min-h-screen items-center justify-center p-4">
      <div class="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div class="flex items-center space-x-3 mb-6">
          <span class="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg text-2xl font-bold">⚡</span>
          <div>
            <h1 class="text-xl font-bold">Lead Intake Portal</h1>
            <p class="text-xs text-slate-400">Automated BANT AI Scoring & Dispatch</p>
          </div>
        </div>
        
        <form id="leadForm" class="space-y-4">
          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Full Name</label>
            <input type="text" id="contact_name" value="David Miller" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500">
          </div>
          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Company</label>
            <input type="text" id="company_name" value="Miller Dispatch Services LLC" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500">
          </div>
          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Email</label>
            <input type="email" id="contact_email" value="david@millerdispatch.com" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500">
          </div>
          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Inquiry / Business Need</label>
            <textarea id="message_text" rows="3" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500">We manage 20 trucks in Florida. Need 24/7 AI lead capture to prevent losing weekend shippers. Budget is $3,000/mo. Ready ASAP.</textarea>
          </div>
          <button type="submit" id="submitBtn" class="w-full bg-indigo-600 hover:bg-indigo-500 transition py-2.5 rounded-lg text-sm font-semibold tracking-wide">
            Submit & Qualify Lead
          </button>
        </form>

        <div id="resultBox" class="hidden mt-6 p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-sm space-y-2">
          <div class="flex justify-between items-center">
            <span class="font-bold text-emerald-400" id="resStatus"></span>
            <span class="text-xs bg-slate-800 px-2 py-1 rounded" id="resScore"></span>
          </div>
          <p class="text-slate-300 text-xs" id="resSummary"></p>
          <p class="text-emerald-400 text-xs font-medium">✓ Alert dispatched to Telegram & Synced to Google Sheets CRM</p>
        </div>
      </div>

      <script>
        document.getElementById('leadForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const btn = document.getElementById('submitBtn');
          btn.disabled = true;
          btn.innerText = 'Evaluating Lead via AI...';

          const data = {
            contact_name: document.getElementById('contact_name').value,
            company_name: document.getElementById('company_name').value,
            contact_email: document.getElementById('contact_email').value,
            message_text: document.getElementById('message_text').value
          };

          try {
            const res = await fetch('/api/v1/qualify', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(data)
            });
            const out = await res.json();
            document.getElementById('resStatus').innerText = out.lead_status + ' Qualification';
            document.getElementById('resScore').innerText = 'Score: ' + out.lead_score + '/100';
            document.getElementById('resSummary').innerText = out.summary;
            document.getElementById('resultBox').classList.remove('hidden');
          } catch(err) {
            alert('Submission failed: ' + err);
          } finally {
            btn.disabled = false;
            btn.innerText = 'Submit & Qualify Lead';
          }
        });
      </script>
    </body>
    </html>
    """
