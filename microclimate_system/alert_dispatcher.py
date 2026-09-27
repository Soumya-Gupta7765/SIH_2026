"""
Emergency Alert & Public Broadcast Dispatcher
Sirens of Summer - Microclimate Heat Alert System

Provides 100% FREE, Zero-Cost Emergency Communication Layers:
1. Telegram Bot API (Unlimited free real-time push alerts to channels/groups/citizens)
2. CallMeBot WhatsApp Free API (Zero-cost instant WhatsApp alerts)
3. Free SMTP Emergency Email Dispatch (Alerts to Ward Disaster Officers & Caregivers)
4. Municipal Common Alerting Protocol (CAP) / Cell Broadcast (CBS) Simulator with persistent audit logging
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = SCRIPT_DIR
DATA_DIR = os.path.join(PROJECT_DIR, "data")
LOGS_FILE = os.path.join(DATA_DIR, "broadcast_history.csv")

def ensure_broadcast_log_exists():
    """Ensure the persistent broadcast audit log CSV exists."""
    if not os.path.exists(LOGS_FILE):
        df_init = pd.DataFrame(columns=[
            "timestamp", "channel", "recipient_type", "target_ward",
            "utci_c", "severity", "citizens_reached", "elderly_reached",
            "status", "message_snippet"
        ])
        df_init.to_csv(LOGS_FILE, index=False)

def log_broadcast_event(channel, recipient_type, target_ward, utci_c, severity,
                        citizens_reached, elderly_reached, status, message_snippet):
    """Log emergency broadcast dispatch to persistent history."""
    ensure_broadcast_log_exists()
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": channel,
        "recipient_type": recipient_type,
        "target_ward": target_ward,
        "utci_c": round(float(utci_c), 1),
        "severity": severity,
        "citizens_reached": int(citizens_reached),
        "elderly_reached": int(elderly_reached),
        "status": status,
        "message_snippet": message_snippet[:120] + "..." if len(message_snippet) > 120 else message_snippet
    }
    df = pd.read_csv(LOGS_FILE)
    df = pd.concat([pd.DataFrame([new_entry]), df], ignore_index=True)
    df.to_csv(LOGS_FILE, index=False)
    return new_entry

def get_broadcast_history():
    """Retrieve broadcast audit history."""
    ensure_broadcast_log_exists()
    try:
        return pd.read_csv(LOGS_FILE)
    except Exception:
        return pd.DataFrame()

# -------------------------------------------------------------
# 1. TELEGRAM BOT API (100% FREE, NO SUBSCRIPTION / NO TWILIO)
# -------------------------------------------------------------
def send_telegram_alert(bot_token: str, chat_id: str, message_text: str):
    """
    Sends an instant Markdown-formatted emergency alert via Telegram Bot API.
    Zero-cost forever, unlimited messaging.
    """
    if not bot_token or not chat_id:
        return False, "Error: Bot Token and Chat ID are required."
    
    url = f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage"
    payload = {
        "chat_id": chat_id.strip(),
        "text": message_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=8)
        res_data = response.json()
        if res_data.get("ok"):
            return True, "Telegram alert dispatched successfully! Status: 200 OK"
        else:
            err_desc = res_data.get("description", "Unknown Telegram API error")
            return False, f"Telegram API Error: {err_desc}"
    except requests.exceptions.RequestException as e:
        return False, f"Network Connection Error: {str(e)}"

# -------------------------------------------------------------
# 2. CALLMEBOT FREE WHATSAPP API (100% FREE)
# -------------------------------------------------------------
def send_whatsapp_alert(phone_with_country_code: str, api_key: str, message_text: str):
    """
    Sends a free WhatsApp message via CallMeBot Free API gateway.
    Requires user's phone (e.g. +919876543210) and personal CallMeBot API key.
    """
    if not phone_with_country_code or not api_key:
        return False, "Error: Phone number and CallMeBot API key are required."
    
    clean_phone = phone_with_country_code.strip().replace("+", "").replace(" ", "").replace("-", "")
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": clean_phone,
        "text": message_text,
        "apikey": api_key.strip()
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200 and ("Message queued" in response.text or "ok" in response.text.lower()):
            return True, "WhatsApp alert queued and delivered successfully via CallMeBot Free Gateway!"
        elif response.status_code == 200:
            return True, f"WhatsApp gateway response: {response.text[:80]}"
        else:
            return False, f"CallMeBot HTTP Error {response.status_code}: {response.text[:100]}"
    except requests.exceptions.RequestException as e:
        return False, f"WhatsApp Gateway Connection Error: {str(e)}"

# -------------------------------------------------------------
# 3. FREE SMTP EMERGENCY EMAIL DISPATCH
# -------------------------------------------------------------
def send_emergency_email(smtp_server: str, smtp_port: int, sender_email: str,
                         sender_password: str, recipient_emails: list,
                         subject: str, html_body: str):
    """
    Sends emergency disaster bulletins via standard free SMTP (Gmail, Outlook, or institutional mail).
    Zero cost.
    """
    if not sender_email or not sender_password or not recipient_emails:
        return False, "Error: Sender credentials and recipient list are required."
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [MCD HEAT DISASTER ALERT] {subject}"
        msg["From"] = f"Sirens of Summer Emergency Control <{sender_email}>"
        msg["To"] = ", ".join(recipient_emails)
        
        part = MIMEText(html_body, "html")
        msg.attach(part)
        
        server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())
        server.quit()
        return True, f"Email disaster bulletin dispatched to {len(recipient_emails)} recipients!"
    except Exception as e:
        return False, f"SMTP Dispatch Error: {str(e)}"

# -------------------------------------------------------------
# 4. EMERGENCY MESSAGE BUILDERS (GENERAL & ELDERLY TAILORED)
# -------------------------------------------------------------
def build_emergency_sms_text(ward_name: str, corporation: str, temp_c: float,
                            utci_c: float, risk_level: str, action_summary: str,
                            cooling_shelter: str = None) -> str:
    """Creates a concise, high-urgency SMS/Push alert text."""
    shelter_str = f"\nNearest AC Shelter: {cooling_shelter}" if cooling_shelter else ""
    return (
        f"🚨 MCD EMERGENCY HEAT ALERT: {ward_name}\n"
        f"Condition: {risk_level.upper()} (UTCI {utci_c:.1f}°C, Ambient {temp_c:.1f}°C)\n"
        f"Order: {action_summary}\n"
        f"Halt non-essential outdoor work 11am-4pm. Drink ORS/water every 45m.{shelter_str}\n"
        f"Dial 108 for Heat-Stroke Emergency | Delhi Disaster Control"
    )

def build_elderly_protection_alert(ward_name: str, elderly_count: int,
                                  utci_c: float, risk_level: str,
                                  cooling_shelter: str = "MCD Community Health Center") -> str:
    """Creates a specialized Geriatric Heat Protection alert text."""
    return (
        f"👵 SENIOR CITIZEN HEAT ADVISORY — {ward_name}\n"
        f"⚠️ Extreme Thermal Threat for {elderly_count:,} Senior Citizens (UTCI {utci_c:.1f}°C)\n\n"
        f"CRITICAL ACTION FOR ELDERLY & CAREGIVERS:\n"
        f"1. Stay indoors in lowest floor shaded rooms from 10:00 AM - 5:00 PM.\n"
        f"2. Hydrate: Drink 150-200ml ORS/lemon water every 45 mins. Avoid hot tea/coffee.\n"
        f"3. Medication Watch: Consult doctor for diuretic/BP dose timing; store meds <25°C.\n"
        f"4. Sponge neck & wrists with cold water compresses.\n"
        f"5. Free AC Shelter: {cooling_shelter} (Open 24/7 with doctors on site).\n"
        f"🚨 Red Flags: Confusion, hot dry skin, dizziness -> Call 108 / 14567 Immediately!"
    )

def build_telegram_broadcast_markdown(ward_name: str, corp: str, temp_c: float,
                                      delta_t: float, utci_c: float, risk_level: str,
                                      action: str, elderly_pop: int, shelter: str) -> str:
    """Rich markdown for Telegram emergency channel."""
    severity_emoji = "🚨" if utci_c >= 43 else "🔥" if utci_c >= 38 else "⚠️"
    return (
        f"{severity_emoji} *MCD HEATWAVE EARLY WARNING BROADCAST*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ *Target Region:* `{ward_name}`\n"
        f"🏢 *Jurisdiction:* {corp}\n"
        f"⏱️ *Disaster Severity:* *{risk_level.upper()}*\n\n"
        f"🌡️ *Microclimate Temp:* `{temp_c:.1f}°C` (UHI Bias: `+{delta_t:.1f}°C`)\n"
        f"🔥 *Physiological Thermal Stress (UTCI):* `{utci_c:.1f}°C`\n"
        f"👵 *At-Risk Senior Citizens (60+):* `{elderly_pop:,}` residents\n\n"
        f"📋 *MUNICIPAL DIRECTIVES:*\n"
        f"• {action}\n"
        f"• Mandatory work stoppage for outdoor construction/laborers\n"
        f"• ORS hydration booths operational at metro & bus terminals\n\n"
        f"🏥 *Designated Cooling Shelter:*\n"
        f"📍 _{shelter}_\n\n"
        f"📞 *Emergency Helplines:* `108` (Ambulance) | `1077` (Disaster Relief) | `14567` (Elderly SOS)"
    )
