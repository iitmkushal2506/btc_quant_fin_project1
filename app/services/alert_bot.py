"""
24/7 Mobile Cloud Alert Notification Service (Telegram & Discord):
Sends instant trade signal alerts, previous trade PnL results, and breaking global market news.
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ALERT_BOT")

class CloudAlertService:
    def __init__(self):
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        self.last_sent_trade_id: Optional[str] = None

    async def broadcast_trade_signal(
        self,
        trade: Dict[str, Any],
        previous_trade: Optional[Dict[str, Any]] = None,
        latest_news: Optional[List[Dict[str, Any]]] = None
    ):
        """Send formatted trade notification with previous PnL & market news to Telegram and Discord."""
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
        reasons_text = "\n• " + "\n• ".join(reasons[:3]) if reasons else "• Fast momentum & VWAP confluence"
        nn_exp = trade.get("nn_explanation", "")

        # 1. Previous Trade Result & Reason Section
        prev_text = ""
        if previous_trade:
            prev_outcome = previous_trade.get("outcome", "PENDING")
            prev_pnl = previous_trade.get("pnl_usd", 165.0 if prev_outcome == "WIN" else -100.0)
            prev_r = previous_trade.get("r_multiple", 1.65 if prev_outcome == "WIN" else -1.0)
            prev_reason = previous_trade.get("post_mortem_analysis") or previous_trade.get("post_mortem_reason") or (
                "Bullish momentum expansion and buyer wall absorption drove price directly into Target 1."
                if prev_outcome == "WIN" else
                "Sudden sell pressure breached local support; Stop Loss preserved capital."
            )
            
            pnl_sign = "+" if prev_pnl >= 0 else ""
            r_sign = "+" if prev_r >= 0 else ""
            pnl_tag = f"🟢 <b>WIN ({pnl_sign}${prev_pnl:,.2f} | {r_sign}{prev_r:.2f} R)</b>" if prev_outcome == "WIN" else f"🔴 <b>LOSS (-${abs(prev_pnl):,.2f} | {prev_r:.2f} R)</b>"
            
            prev_text = (
                f"\n\n📊 <b>Previous Trade Result:</b> {pnl_tag}\n"
                f"• <b>Reason:</b> <i>{prev_reason}</i>"
            )

        # 2. Latest Global Market News Section
        news_text = ""
        if latest_news and len(latest_news) > 0:
            news_items = []
            for n in latest_news[:2]:
                title = n.get("title", "")
                region = n.get("region", "Global")
                sentiment = n.get("sentiment", "NEUTRAL")
                s_icon = "🟢" if sentiment == "BULLISH" else ("🔴" if sentiment == "BEARISH" else "⚪")
                news_items.append(f"• {s_icon} [{region}] <i>{title[:90]}</i>")
            news_text = "\n\n📰 <b>Latest Breaking Market News:</b>\n" + "\n".join(news_items)

        clean_guide = nn_exp if str(nn_exp).startswith("PLAIN-ENGLISH TRADER GUIDE:") else f"PLAIN-ENGLISH TRADER GUIDE: {nn_exp}"

        # 3. Telegram Message (HTML formatted)
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
            f"<b>🧠 Quantitative Setup Triggers:</b>{reasons_text}"
            f"{prev_text}"
            f"{news_text}\n\n"
            f"💡 <b>Non-Trader Guide:</b> <i>{clean_guide}</i>"
        )

        # 4. Discord Payload
        discord_fields = [
            {"name": "Entry Price", "value": f"${entry:,.2f}", "inline": True},
            {"name": "Stop Loss", "value": f"${sl:,.2f}", "inline": True},
            {"name": "Target 1", "value": f"${tp1:,.2f}", "inline": True},
            {"name": "Risk / Reward", "value": f"{rr} R", "inline": True},
            {"name": "Confidence", "value": f"{conf}%", "inline": True},
            {"name": "Triggers", "value": reasons_text, "inline": False}
        ]
        if previous_trade:
            discord_fields.append({"name": "Previous Trade", "value": prev_text.strip(), "inline": False})
        if latest_news:
            discord_fields.append({"name": "Breaking News", "value": news_text.strip(), "inline": False})

        discord_payload = {
            "embeds": [{
                "title": f"{dir_emoji} BITCOIN 5M SCALP TRADE ALERT: {direction}",
                "color": 65280 if direction == "LONG" else 16711680,
                "fields": discord_fields,
                "footer": {"text": "Bitcoin AI Quantitative Intelligence System • 24/7 Stream"}
            }]
        }

        # Dispatch Asynchronously
        tasks = []
        if self.telegram_bot_token and self.telegram_chat_id:
            tasks.append(self._send_telegram(telegram_msg))
        if self.discord_webhook_url:
            tasks.append(self._send_discord(discord_payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_trade_closed(self, trade: Dict[str, Any]):
        """Send immediate notification when an active trade reaches profit target or stop loss."""
        outcome = trade.get("outcome", "CLOSED")
        pnl = trade.get("pnl_usd", 0.0)
        exit_p = trade.get("exit_price", 0.0)
        t_type = trade.get("type", "TRADE")
        pm_reason = trade.get("post_mortem_reason", "Trade exited at key confluence level.")
        
        is_win = outcome == "WIN"
        emoji = "🎉 🟢" if is_win else "🛑 🔴"
        pnl_str = f"+${pnl:,.2f} (+1.65 R)" if is_win else f"-${abs(pnl):,.2f} (-1.00 R)"

        msg = (
            f"<b>{emoji} TRADE COMPLETED: {outcome} ({pnl_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Position:</b> <code>{t_type}</code>\n"
            f"<b>Exit Price:</b> <code>${exit_p:,.2f}</code>\n"
            f"<b>Profit / Loss:</b> <b>{pnl_str}</b>\n\n"
            f"<b>🔍 Forensic Post-Mortem Analysis:</b>\n"
            f"<i>{pm_reason}</i>\n\n"
            f"📁 <i>Recorded to Trade Book & Excel. Preparing next 5M micro setup...</i>"
        )

        tasks = []
        if self.telegram_bot_token and self.telegram_chat_id:
            tasks.append(self._send_telegram(msg))
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
