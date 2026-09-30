"""
24/7 Mobile Cloud Alert Notification Service (Telegram & Discord):
Sends instant trade signal alerts directly to your phone 24x7 when hosted in the cloud.
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ALERT_BOT")

class CloudAlertService:
    def __init__(self):
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        self.last_sent_trade_id: Optional[str] = None

    async def broadcast_trade_signal(self, trade: Dict[str, Any]):
        """Send formatted trade notification to Telegram and Discord on new signal."""
        t_id = trade.get("id")
        if not t_id or t_id == self.last_sent_trade_id:
            return

        self.last_sent_trade_id = t_id
        
        direction = trade.get("type", "LONG")
        dir_emoji = "🟢" if direction == "LONG" else "🔴"
        entry = trade.get("entry_price", 0.0)
        sl = trade.get("stop_loss", 0.0)
        tp1 = trade.get("target_1", 0.0)
        tp2 = trade.get("target_2", 0.0)
        rr = trade.get("risk_reward", 1.65)
        conf = trade.get("confidence", 80.0)
        reasons = trade.get("reasons", [])
        reasons_text = "\n• " + "\n• ".join(reasons[:3]) if reasons else "• Momentum & VWAP alignment"
        nn_exp = trade.get("nn_explanation", "")

        # 1. Telegram Message (HTML formatted)
        telegram_msg = (
            f"<b>{dir_emoji} BITCOIN 5M SCALP TRADE ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Direction:</b> {dir_emoji} <code>{direction}</code>\n"
            f"<b>Entry Price:</b> <code>${entry:,.2f}</code>\n"
            f"<b>Stop Loss (Safety Net):</b> <code>${sl:,.2f}</code>\n"
            f"<b>Target 1 (Take Profit):</b> <code>${tp1:,.2f}</code>\n"
            f"<b>Target 2 (Runner):</b> <code>${tp2:,.2f}</code>\n"
            f"<b>Risk/Reward Ratio:</b> <code>{rr} R</code>\n"
            f"<b>AI Confidence:</b> <code>{conf}%</code>\n\n"
            f"<b>🧠 Quantitative Setup Triggers:</b>{reasons_text}\n\n"
            f"<i>💡 Non-Trader Guide: {nn_exp[:200]}...</i>"
        )

        # 2. Discord Embed Message
        discord_payload = {
            "embeds": [{
                "title": f"{dir_emoji} BITCOIN 5M SCALP TRADE ALERT: {direction}",
                "color": 65280 if direction == "LONG" else 16711680,
                "fields": [
                    {"name": "Entry Price", "value": f"${entry:,.2f}", "inline": True},
                    {"name": "Stop Loss", "value": f"${sl:,.2f}", "inline": True},
                    {"name": "Target 1", "value": f"${tp1:,.2f}", "inline": True},
                    {"name": "Risk / Reward", "value": f"{rr} R", "inline": True},
                    {"name": "Confidence", "value": f"{conf}%", "inline": True},
                    {"name": "Why Trade Was Taken", "value": reasons_text, "inline": False}
                ],
                "footer": {"text": "Bitcoin AI Quantitative Intelligence System • 24/7 Cloud Stream"}
            }]
        }

        # Send asynchronously
        tasks = []
        if self.telegram_bot_token and self.telegram_chat_id:
            tasks.append(self._send_telegram(telegram_msg))
        if self.discord_webhook_url:
            tasks.append(self._send_discord(discord_payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, text: str):
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info("24/7 Telegram trade alert sent successfully.")
                else:
                    logger.warning(f"Telegram alert error: {res.text}")
        except Exception as e:
            logger.debug(f"Telegram notification network error: {e}")

    async def _send_discord(self, payload: Dict[str, Any]):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(self.discord_webhook_url, json=payload)
                if res.status_code in [200, 204]:
                    logger.info("24/7 Discord trade alert sent successfully.")
                else:
                    logger.warning(f"Discord alert error: {res.text}")
        except Exception as e:
            logger.debug(f"Discord notification network error: {e}")

cloud_alert_service = CloudAlertService()
