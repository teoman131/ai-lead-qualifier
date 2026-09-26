import os
import re
import urllib.parse
import httpx
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEETS_WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "")
SPREADSHEET_URL = os.getenv("GOOGLE_SHEETS_SPREADSHEET_URL", "https://docs.google.com/spreadsheets")

app = FastAPI(
    title="B2B AI Lead Qualifier & Multi-Channel Dispatcher",
    description="Enterprise API to evaluate leads, generate AI outreach, and trigger 1-tap WhatsApp/Telegram/Email actions",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeadInboundRequest(BaseModel):
    contact_name: str = Field(..., example="Дмитрий Волков")
    contact_phone: Optional[str] = Field(None, example="+79991234567")
    contact_email: Optional[str] = Field(None, example="dmitry@logistics.ru")
    telegram_handle: Optional[str] = Field(None, example="@dmitry_flow")
    company_name: Optional[str] = Field("Не указано", example="Волков Логистик")
    message_text: str = Field(..., example="Нужно срочно подключить AI-обработку лидов для 15 машин. Бюджет 50 000 руб/мес.")

class LeadQualificationResult(BaseModel):
    lead_score: int
    lead_status: str
    budget_estimate: str
    timeline: str
    key_pain_points: List[str]
    recommended_action: str
    ai_reply_draft: str
    summary: str

def clean_phone_number(raw_phone: Optional[str]) -> str:
    if not raw_phone:
        return ""
    digits = re.sub(r"[^\d]", "", raw_phone)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits

def evaluate_lead(lead: LeadInboundRequest) -> LeadQualificationResult:
    text_lower = lead.message_text.lower()
    score = 65
    pain_points = []
    
    if any(k in text_lower for k in ["срочно", "asap", "быстро", "горят", "urgent", "сегодня", "сейчас"]):
        score += 15
        timeline = "Срочно (до 7 дней)"
    else:
        timeline = "В течение месяца"

    if any(k in text_lower for k in ["руб", "₽", "$", "бюджет", "budget", "тысяч", "к", "оплата"]):
        score += 15
        budget = "Подтвержденный бюджет"
    else:
        budget = "Не уточнен"

    if any(k in text_lower for k in ["лид", "заявк", "клиент", "сайт", "трафик", "конверси"]):
        pain_points.append("Потеря входящих лидов и конверсия сайта")
    if any(k in text_lower for k in ["ноч", "выходн", "24/7", "долго", "менеджер"]):
        pain_points.append("Медленный ответ менеджеров вне рабочего времени")
    if not pain_points:
        pain_points.append("Автоматизация клиентского сервиса")

    score = min(score, 98)
    status = "HOT 🔥" if score >= 80 else ("WARM ⚡" if score >= 60 else "COLD ❄️")
    action = "Срочный звонок / написать за 5 мин" if score >= 80 else "Стандартная обработка"

    name_clean = lead.contact_name.split()[0] if lead.contact_name else "Здравствуйте"
    pain_text = pain_points[0].lower()
    draft = (
        f"Здравствуйте, {name_clean}!\n\n"
        f"Увидели ваше обращение по поводу {pain_text}. "
        f"Мы можем развернуть готовую автоматизацию под ваш проект за 48 часов.\n\n"
        f"Удобно сейчас созвониться на 5 минут или показать демо прямо в мессенджере?"
    )

    return LeadQualificationResult(
        lead_score=score,
        lead_status=status,
        budget_estimate=budget,
        timeline=timeline,
        key_pain_points=pain_points,
        recommended_action=action,
        ai_reply_draft=draft,
        summary=f"Лид: {lead.contact_name} ({lead.company_name or 'Частное лицо'}). Оценка: {timeline}."
    )

async def send_telegram_alert(lead: LeadInboundRequest, eval_res: LeadQualificationResult):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    clean_phone = clean_phone_number(lead.contact_phone)
    encoded_draft = urllib.parse.quote(eval_res.ai_reply_draft)
    
    text = (
        f"{eval_res.lead_status} НОВЫЙ ЛИД (Скоринг: {eval_res.lead_score}/100)\n\n"
        f"👤 Клиент: {lead.contact_name}\n"
        f"🏢 Компания: {lead.company_name or '—'}\n"
        f"📞 Телефон: {lead.contact_phone or '—'}\n"
        f"📧 Email: {lead.contact_email or '—'}\n"
        f"✈️ Telegram: {lead.telegram_handle or '—'}\n"
        f"💰 Бюджет: {eval_res.budget_estimate}\n"
        f"⏱ Сроки: {eval_res.timeline}\n\n"
        f"🎯 Рекомендация: {eval_res.recommended_action}\n\n"
        f"✨ Готовый AI-ответ для клиента:\n"
        f"────────────────────────\n"
        f"{eval_res.ai_reply_draft}\n"
        f"────────────────────────\n\n"
        f"💬 Сообщение клиента:\n\"{lead.message_text}\""
    )

    buttons = []
    
    # 1. Кнопка WhatsApp (открывает чат со вбитым текстом)
    if clean_phone:
        buttons.append([{"text": "💬 Написать в WhatsApp", "url": f"https://wa.me/{clean_phone}?text={encoded_draft}"}])
    
    # 2. Кнопка Telegram (если передан юзернейм)
    if lead.telegram_handle:
        tg_nick = lead.telegram_handle.replace("@", "").strip()
        buttons.append([{"text": "✈️ Написать в Telegram", "url": f"https://t.me/{tg_nick}"}])

    # 3. Кнопка Gmail и CRM
    row_actions = []
    if lead.contact_email:
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={lead.contact_email}&su=Заявка+{urllib.parse.quote(lead.company_name or '')}"
        row_actions.append({"text": "✉️ Email (Gmail)", "url": gmail_url})
    
    row_actions.append({"text": "📊 CRM Таблица", "url": SPREADSHEET_URL})
    buttons.append(row_actions)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "reply_markup": {"inline_keyboard": buttons}
            }, timeout=10.0)
        except Exception as e:
            print(f"Telegram error: {e}")

async def append_to_sheets(lead: LeadInboundRequest, eval_res: LeadQualificationResult):
    if not GOOGLE_SHEETS_WEBHOOK_URL:
        return
    payload = {
        "timestamp": "",
        "name": lead.contact_name,
        "phone": lead.contact_phone or "",
        "telegram": lead.telegram_handle or "",
        "company": lead.company_name or "",
        "email": lead.contact_email or "",
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
    return {"status": "active", "service": "AI Lead Qualifier & Dispatcher", "version": "1.3.0"}

@app.post("/api/v1/qualify", response_model=LeadQualificationResult, tags=["Pipeline"])
async def qualify_lead(lead: LeadInboundRequest):
    result = evaluate_lead(lead)
    await send_telegram_alert(lead, result)
    await append_to_sheets(lead, result)
    return result

@app.post("/api/v1/webhook/form", tags=["Universal Webhook"])
async def form_webhook(request: Request):
    """Универсальный приемщик заявок с Tilda, WordPress, Elementor или обычных HTML-форм"""
    body = await request.body()
    try:
        data = await request.json()
    except Exception:
        data = dict(urllib.parse.parse_qsl(body.decode("utf-8")))

    name = data.get("Name") or data.get("name") or data.get("fio") or "Новый клиент"
    phone = data.get("Phone") or data.get("phone") or data.get("tel") or ""
    email = data.get("Email") or data.get("email") or ""
    tg = data.get("telegram") or data.get("tg") or ""
    company = data.get("company") or data.get("Company") or "С сайта"
    msg = data.get("message") or data.get("text") or data.get("comment") or "Запрос с сайта"

    lead = LeadInboundRequest(
        contact_name=str(name),
        contact_phone=str(phone),
        contact_email=str(email),
        telegram_handle=str(tg),
        company_name=str(company),
        message_text=str(msg)
    )
    result = evaluate_lead(lead)
    await send_telegram_alert(lead, result)
    await append_to_sheets(lead, result)
    return {"status": "ok", "lead_score": result.lead_score, "lead_status": result.lead_status}

@app.get("/demo", response_class=HTMLResponse, tags=["Demo Portal"])
def get_demo_page():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>B2B AI Lead Qualifier & Multi-Channel Actions</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 flex min-h-screen items-center justify-center p-4">
      <div class="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-7 shadow-2xl space-y-5">
        <div class="flex items-center space-x-3">
          <span class="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl text-2xl font-bold">⚡</span>
          <div>
            <h1 class="text-xl font-bold">Входящая заявка с сайта</h1>
            <p class="text-xs text-slate-400">Мгновенный AI-скоринг и быстрая связь в WhatsApp / TG</p>
          </div>
        </div>
        
        <form id="leadForm" class="space-y-3.5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Имя</label>
              <input type="text" id="contact_name" value="Алексей Смирнов" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
            </div>
            <div>
              <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Компания</label>
              <input type="text" id="company_name" value="Смирнов Карго" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Телефон (WhatsApp)</label>
              <input type="text" id="contact_phone" value="+7 999 123-45-67" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
            </div>
            <div>
              <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Telegram (юзернейм)</label>
              <input type="text" id="telegram_handle" value="@alex_cargo" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
            </div>
          </div>

          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Email</label>
            <input type="email" id="contact_email" value="alex@cargo.ru" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
          </div>

          <div>
            <label class="block text-xs uppercase font-medium text-slate-400 mb-1">Запрос клиента</label>
            <textarea id="message_text" rows="3" required class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">Срочно нужен бот для обработки заявок по грузоперевозкам на выходных. Теряем лиды. Бюджет 45 000 руб в месяц.</textarea>
          </div>

          <button type="submit" id="submitBtn" class="w-full bg-indigo-600 hover:bg-indigo-500 transition py-2.5 rounded-lg text-sm font-semibold tracking-wide">
            Отправить заявку в систему
          </button>
        </form>

        <div id="resultBox" class="hidden p-4 rounded-xl border border-indigo-500/30 bg-indigo-500/5 text-sm space-y-3">
          <div class="flex justify-between items-center border-b border-indigo-500/20 pb-2.5">
            <span class="font-bold text-emerald-400 text-base" id="resStatus"></span>
            <span class="text-xs bg-slate-800 text-indigo-300 font-semibold px-2.5 py-1 rounded-full" id="resScore"></span>
          </div>
          <div>
            <span class="text-xs uppercase font-bold text-slate-400">Оценка ИИ</span>
            <p class="text-slate-300 text-xs mt-1" id="resSummary"></p>
          </div>
          <div class="bg-slate-950/80 p-3 rounded-lg border border-slate-800">
            <span class="text-[11px] uppercase font-bold text-indigo-400 block mb-1">✨ Готовый черновик ответа</span>
            <p class="text-xs text-slate-300 whitespace-pre-line leading-relaxed" id="resDraft"></p>
          </div>
          <p class="text-emerald-400 text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Карточка отправлена в Telegram с кнопками прямого ответа клиенту
          </p>
        </div>
      </div>

      <script>
        document.getElementById('leadForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const btn = document.getElementById('submitBtn');
          btn.disabled = true;
          btn.innerText = 'Обработка и скоринг...';

          const data = {
            contact_name: document.getElementById('contact_name').value,
            company_name: document.getElementById('company_name').value,
            contact_phone: document.getElementById('contact_phone').value,
            telegram_handle: document.getElementById('telegram_handle').value,
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
            document.getElementById('resStatus').innerText = out.lead_status + ' Скоринг';
            document.getElementById('resScore').innerText = 'Балл: ' + out.lead_score + '/100';
            document.getElementById('resSummary').innerText = out.summary;
            document.getElementById('resDraft').innerText = out.ai_reply_draft;
            document.getElementById('resultBox').classList.remove('hidden');
          } catch(err) {
            alert('Ошибка отправки: ' + err);
          } finally {
            btn.disabled = false;
            btn.innerText = 'Отправить заявку в систему';
          }
        });
      </script>
    </body>
    </html>
    """
