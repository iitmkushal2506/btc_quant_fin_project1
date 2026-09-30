"""
Bitcoin AI Trading & Market Intelligence System - Unified Launcher
"""

import sys
import time
import webbrowser
import threading
import uvicorn

from app.config import HOST, PORT, APP_NAME, VERSION

def open_browser():
    time.sleep(1.8)
    url = f"http://localhost:{PORT}"
    print(f"\n[🚀] Opening Web Intelligence Dashboard at {url} ...\n")
    webbrowser.open(url)

if __name__ == "__main__":
    print("=" * 75)
    print(f"  {APP_NAME} v{VERSION}")
    print("  Quantitative Data Science + Machine Learning + Confluence Engine")
    print("  100% Free Public Market Data: Binance, Mempool, Fear & Greed, Macro")
    print("=" * 75)
    print(f"\n[*] Starting FastAPI Server on http://{HOST}:{PORT} ...")

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False, log_level="info")
    except KeyboardInterrupt:
        print("\n[*] Server shutdown gracefully.")
