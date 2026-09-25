import os
import json
import urllib.request
import urllib.parse
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(
    title="B2B AI Lead Qualifier API",
    description="Automated inbound lead evaluation and qualification system for US service businesses",
    version="1.0.0"
)

# --- SCHEMAS ---
class LeadInput(BaseModel):
    contact_name: str = Field(..., example="John Miller")
    contact_email: str = Field(..., example="john@millerlogistics.com")
    company_name: Optional[str] = Field(None, example="Miller Freight LLC")
    message_text: str = Field(
        ..., 
        example="Hi, we run 15 trucks in Texas. We are losing leads on weekends and need an AI booking agent ASAP. Budget is around $2,500."
    )

class LeadQualification(BaseModel):
    lead_score: int = Field(..., description="Score from 1 to 100")
    lead_status: str = Field(..., description="'HOT', 'WARM', or 'COLD'")
    budget_estimate: Optional[str] = Field(None, description="Extracted or inferred budget")
    timeline: Optional[str] = Field(None, description="Urgency / expected deployment")
    key_pain_points: list[str] = Field(..., description="Summary of customer problems")
    recommended_action: str = Field(..., description="'Instant Call Booking', 'Follow-up Email', 'Archive'")
    summary: str = Field(..., description="Executive summary for the business owner")

# --- INTEGRATIONS ---
def send_telegram_alert(lead: LeadInput, qualification: LeadQualification):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return

    icon = "🔥 HOT LEAD" if qualification.lead_status == "HOT" else "⚡ NEW INQUIRY"
    
    text = (
        f"{icon} (Score: {qualification.lead_score}/100)\n\n"
        f"👤 Contact: {lead.contact_name}\n"
        f"🏢 Company: {lead.company_name or 'N/A'}\n"
        f"📧 Email: {lead.contact_email}\n"
        f"💰 Budget: {qualification.budget_estimate or 'Not stated'}\n"
        f"⏱️ Urgency: {qualification.timeline or 'Flexible'}\n\n"
        f"🎯 Action: {qualification.recommended_action}\n"
        f"📝 Summary: {qualification.summary}\n\n"
        f"💬 Original Message:\n\"{lead.message_text}\""
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Telegram alert warning: {e}")

def save_to_google_sheets(lead: LeadInput, qualification: LeadQualification):
    webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL")
    if not webhook_url or "script.google.com" not in webhook_url:
        return

    sheet_payload = {
        "name": lead.contact_name,
        "company": lead.company_name or "N/A",
        "email": lead.contact_email,
        "score": qualification.lead_score,
        "status": qualification.lead_status,
        "budget": qualification.budget_estimate or "N/A",
        "action": qualification.recommended_action,
        "summary": qualification.summary
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(sheet_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f"Google Sheets warning: {e}")

# --- QUALIFICATION LOGIC ---
def qualify_with_ai(lead: LeadInput) -> LeadQualification:
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key or api_key == "your_openai_api_key_here":
        text_lower = lead.message_text.lower()
        is_hot = any(w in text_lower for w in ["asap", "budget", "urgent", "$", "need", "hire"])
        score = 92 if is_hot else 45
        status = "HOT" if is_hot else "WARM"
        action = "Instant Call Booking" if is_hot else "Follow-up Email"
        
        return LeadQualification(
            lead_score=score,
            lead_status=status,
            budget_estimate="$2,500" if "$2,500" in lead.message_text else "$2,000 - $3,000",
            timeline="Immediate (ASAP)" if "asap" in text_lower else "Within 30 days",
            key_pain_points=["Losing prospective clients during off-hours", "Manual lead response bottleneck"],
            recommended_action=action,
            summary=f"High-intent inquiry from {lead.contact_name} ({lead.company_name or 'N/A'}). Ready to deploy AI tooling."
        )

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system_prompt = """
    You are an elite B2B Sales Operations AI for US service agencies.
    Analyze incoming customer inquiries using the BANT framework.
    Output strictly a valid JSON matching this schema:
    {
        "lead_score": int (1-100),
        "lead_status": "HOT" | "WARM" | "COLD",
        "budget_estimate": string or null,
        "timeline": string or null,
        "key_pain_points": [string],
        "recommended_action": "Instant Call Booking" | "Follow-up Email" | "Archive",
        "summary": string
    }
    """

    user_prompt = f"Name: {lead.contact_name}\nCompany: {lead.company_name}\nEmail: {lead.contact_email}\nText: {lead.message_text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        return LeadQualification(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

# --- ENDPOINTS ---
@app.get("/")
def health_check():
    return {"status": "active", "service": "AI Lead Qualifier Engine"}

@app.post("/api/v1/qualify", response_model=LeadQualification)
def process_lead(lead: LeadInput):
    result = qualify_with_ai(lead)
    
    # 1. Alert in Telegram
    send_telegram_alert(lead, result)
    
    # 2. Record in Google Sheets CRM
    save_to_google_sheets(lead, result)
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)