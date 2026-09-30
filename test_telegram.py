"""
Quick Telegram Alert Tester:
Run this script to test the enhanced Telegram Bot alerts with previous trade PnL & breaking news.
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
        "<b>🟢 BITCOIN 5M SCALP TRADE ALERT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Direction:</b> 🟢 <code>LONG</code>\n"
        "<b>Entry Price:</b> <code>$83,750.00</code>\n"
        "<b>Stop Loss (Safety Net):</b> <code>$83,590.00</code>\n"
        "<b>Target 1 (Take Profit):</b> <code>$84,015.00</code>\n"
        "<b>Target 2 (Runner):</b> <code>$84,230.00</code>\n"
        "<b>Risk/Reward Ratio:</b> <code>1.65 R</code>\n"
        "<b>AI Confidence:</b> <code>85.0%</code>\n\n"
        "<b>🧠 Quantitative Setup Triggers:</b>\n"
        "• 5m EMA 9 crossed above EMA 21 (Bullish Momentum)\n"
        "• Price bouncing from 5m VWAP ($83,710)\n"
        "• Orderbook $4.2M Bid wall at $83,590 (+0.26 OBI)\n\n"
        "📊 <b>Previous Trade Result:</b> 🟢 <b>WIN (+$165.00 | +1.65 R)</b>\n"
        "• <b>Reason:</b> <i>Strong buyer absorption at VWAP support pushed price smoothly into Target 1.</i>\n\n"
        "📰 <b>Latest Breaking Market News:</b>\n"
        "• 🟢 [Global] <i>Global institutional crypto ETF volume surpasses $1.2B in morning trading</i>\n\n"
        "💡 <b>Non-Trader Guide:</b> <i>PLAIN-ENGLISH TRADER GUIDE: We placed a BUY (Long) trade at $83,750.00 because we expect Bitcoin price to go UP in the next 5 to 15 minutes. Key triggers detected by AI: 5m EMA 9 crossed above EMA 21 with heavy buyer order flow.</i>"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            data = res.json()
            if res.status_code == 200 and data.get("ok"):
                print("🎉 SUCCESS! An enriched test alert with previous trade PnL & news has been sent to your Telegram.")
                print("📱 Check your Telegram app!\n")
            else:
                desc = data.get('description', res.text)
                print(f"[-] Telegram API Error: {desc}")
    except Exception as e:
        print(f"[-] Connection Failed: {e}")

if __name__ == "__main__":
    bot_token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        print("\n[!] Missing Bot Token or Chat ID in .env file!")
    else:
        asyncio.run(test_telegram_alert(bot_token, chat_id))
