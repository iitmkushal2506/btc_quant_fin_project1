"""
Quick Telegram Alert Tester:
Run this script to test your Telegram Bot Token & Chat ID.
"""

import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

# Force utf-8 stdout on windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

async def test_telegram_alert(token: str, chat_id: str):
    print("\n[+] Connecting to Telegram API...")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    msg = (
        "🟢 <b>BITCOIN AI QUANT TERMINAL - TEST NOTIFICATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Status:</b> Telegram Bot Connected Successfully!\n"
        "📈 <b>Asset:</b> BTC/USDT Perpetual\n"
        "🎯 <b>Signal Stream:</b> 24/7 Scalp & Institutional Signals Active\n"
        "💡 <i>You will now receive all live trade setups and profit/loss updates directly on your phone!</i>"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            data = res.json()
            if res.status_code == 200 and data.get("ok"):
                print("🎉 SUCCESS! A test notification has been sent to your Telegram app.")
                print("📱 Check your phone right now!\n")
            else:
                desc = data.get('description', res.text)
                print(f"[-] Telegram API Error: {desc}")
                print("\n[TIP]:")
                if "chat not found" in desc.lower() or "blocked" in desc.lower():
                    print(f"👉 You MUST open your bot ( https://t.me/karan_btc_signals_ex1_bot ) and click 'START' or send 'Hi' once so the bot has permission to message you!")
                else:
                    print("Please check that your Bot Token and Chat ID match your Telegram profile.")
    except Exception as e:
        print(f"[-] Connection Failed: {e}")

if __name__ == "__main__":
    bot_token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        print("\n[!] Missing Bot Token or Chat ID in .env file!")
    else:
        asyncio.run(test_telegram_alert(bot_token, chat_id))
