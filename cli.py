"""
Terminal Quantitative Trading & Market Intelligence CLI Monitor
"""

import sys
import time
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live

from app.main import system_engine

console = Console()

def generate_dashboard_view(data: dict) -> Panel:
    if not data or "ticker" not in data:
        return Panel(Text("Ingesting live market data and calculating quantitative confluence...", style="bold yellow"))

    ticker = data.get("ticker", {})
    decision = data.get("decision", {})
    confluence = data.get("confluence", {})
    pillars = confluence.get("pillars", {})
    risk = data.get("risk_management", {})
    regime = data.get("regime", {})
    macro = data.get("macro", {})
    news = data.get("news", {})

    # Price & Change formatting
    price = ticker.get("last_price", 0.0)
    chg = ticker.get("price_change_percent", 0.0)
    chg_color = "green" if chg >= 0 else "red"
    chg_arrow = "▲" if chg >= 0 else "▼"

    # Decision Badge Styling
    d_badge = decision.get("badge_text", "🔴 NO TRADE")
    if "VALID (LONG)" in d_badge:
        badge_style = "bold white on green"
    elif "VALID (SHORT)" in d_badge:
        badge_style = "bold white on red"
    elif "WAIT" in d_badge:
        badge_style = "bold black on yellow"
    else:
        badge_style = "bold white on dark_red"

    # Layout Construction
    header_text = Text()
    header_text.append(f"  BTC/USDT  ${price:,.2f}  ", style="bold cyan")
    header_text.append(f" {chg_arrow} {chg:+.2f}%  ", style=f"bold {chg_color}")
    header_text.append(f" | Regime: {regime.get('regime_name', 'Ranging')} ", style="bold magenta")
    header_text.append(f" | Confluence: {confluence.get('master_confluence_score', 0):+.1f} ", style="bold yellow")
    header_text.append(f" | Conviction: {confluence.get('conviction_pct', 0):.0f}%  ", style="bold white")

    # 1. 7-Pillars Table
    pillar_table = Table(title="7-Pillar Quantitative Confluence Matrix", title_style="bold blue", expand=True, border_style="dim")
    pillar_table.add_column("Pillar Dimension", style="cyan", no_wrap=True)
    pillar_table.add_column("Weight", justify="center", style="dim")
    pillar_table.add_column("Score (-100 to +100)", justify="right")
    pillar_table.add_column("Bias", justify="center")
    pillar_table.add_column("Key Evidence", style="white")

    for key, p in pillars.items():
        sc = p.get("score", 0.0)
        bias = p.get("bias", "NEUTRAL")
        sc_color = "green" if sc > 15 else ("red" if sc < -15 else "yellow")
        bias_style = "bold green" if bias == "BULLISH" else ("bold red" if bias == "BEARISH" else "dim yellow")
        evidence = "; ".join(p.get("key_factors", [])[:2])
        pillar_table.add_row(
            p.get("name", key),
            f"{p.get('weight', 0)*100:.0f}%",
            f"[{sc_color}]{sc:+.1f}[/{sc_color}]",
            f"[{bias_style}]{bias}[/{bias_style}]",
            evidence
        )

    # 2. Risk & Trade Setup Table
    risk_table = Table(title="Institutional Financial Risk Management", title_style="bold yellow", expand=True, border_style="dim")
    risk_table.add_column("Direction", style="bold cyan")
    risk_table.add_column("Entry Zone", style="white")
    risk_table.add_column("Stop Loss", style="red")
    risk_table.add_column("Take Profit 1", style="green")
    risk_table.add_column("Take Profit 2", style="green")
    risk_table.add_column("Risk / Reward", style="bold yellow")
    risk_table.add_column("Position Size (BTC)", style="white")

    tp_levels = risk.get("take_profit_levels", [])
    tp1_str = f"${tp_levels[0]['price']:,.1f}" if len(tp_levels) > 0 else "N/A"
    tp2_str = f"${tp_levels[1]['price']:,.1f}" if len(tp_levels) > 1 else "N/A"
    entry_zone = risk.get("entry_zone", {})
    entry_str = f"${entry_zone.get('min_entry', price):,.0f} - ${entry_zone.get('max_entry', price):,.0f}" if entry_zone.get("min_entry") else "Stand Aside"
    sl_str = f"${risk.get('stop_loss', 0):,.1f} (-{risk.get('stop_loss_distance_pct', 0):.2f}%)" if risk.get("stop_loss") else "N/A"

    risk_table.add_row(
        risk.get("direction", "NO_TRADE"),
        entry_str,
        sl_str,
        tp1_str,
        tp2_str,
        f"{risk.get('risk_reward_ratio', 0):.2f}R",
        f"{risk.get('position_sizing', {}).get('position_size_btc', 0):.4f} BTC"
    )

    # Combined Layout Text
    decision_panel = Panel(
        Text(f"\n   DECISION:  {d_badge}   \n\n   {decision.get('summary_reason', '')}\n\n   Directive: {decision.get('action_directive', '')}\n", style=badge_style),
        title="Authoritative Trading Decision",
        border_style="bold cyan"
    )

    full_text = Layout()
    full_text.split_column(
        Layout(decision_panel, size=7),
        Layout(pillar_table, size=11),
        Layout(risk_table, size=6)
    )

    return Panel(full_text, title=f"Bitcoin AI Trading & Market Intelligence Terminal v1.0", subtitle="Real-Time Public Data Engine | Preserving Capital Over Trade Frequency", border_style="cyan")

async def run_cli_loop():
    console.print("[bold cyan]Initializing Bitcoin AI Trading & Market Intelligence Engine...[/bold cyan]")
    await system_engine.update_pipeline()

    with Live(console=console, screen=True, refresh_per_second=1) as live:
        while True:
            await system_engine.update_pipeline()
            live.update(generate_dashboard_view(system_engine.latest_assessment))
            await asyncio.sleep(4.0)

if __name__ == "__main__":
    try:
        asyncio.run(run_cli_loop())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]System halted safely by user.[/bold yellow]")
        sys.exit(0)
