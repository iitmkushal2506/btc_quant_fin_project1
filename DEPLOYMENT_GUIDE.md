# 🌐 24/7 Cloud Deployment & Mobile Signal Alerts Guide

This guide explains how to deploy your **Bitcoin AI Quantitative Trading & Market Intelligence System** to the cloud so it runs **24 hours a day, 7 days a week continuously without needing your personal computer or machine turned on**.

---

## 🌟 How 24/7 Cloud Execution Works

1. **Self-Contained Architecture**: The application uses **100% free and publicly accessible REST & WebSocket APIs** (Binance, Mempool.space, Alternative.me, Yahoo Finance, RSS news feeds) with zero paid subscriptions.
2. **Always-On Cloud Server**: When hosted on a cloud provider (like Render, Railway, or a Linux VPS), the cloud server runs the Python engine 24/7 in the background.
3. **Anywhere Access**: You can open the live web dashboard from your smartphone, tablet, or laptop from anywhere in the world.
4. **24/7 Phone Push Notifications**: You can connect a free **Telegram Bot** or **Discord Webhook** so you receive instant trade signals directly on your phone the moment they are generated.

---

## 🚀 Option 1: 100% Free 1-Click Deployment on Render.com (Easiest)

[Render.com](https://render.com) provides free cloud hosting with automatic GitHub integration.

### Step 1: Upload Code to GitHub
1. Create a free account on [GitHub.com](https://github.com).
2. Create a new repository (e.g. `bitcoin-ai-trading-system`).
3. Push your project code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Bitcoin AI system"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/bitcoin-ai-trading-system.git
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Sign up for free at [Render.com](https://render.com).
2. Click **New +** → **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your GitHub repository.
4. Configure the service:
   - **Name**: `bitcoin-ai-trading`
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt, Singapore)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Click **Create Web Service**.
6. In ~2 minutes, your dashboard will be live at:
   `https://bitcoin-ai-trading.onrender.com`

---

## 📱 Option 2: 24/7 Telegram Phone Notifications Setup

To receive trade signals on your phone while your computer is off:

### Step 1: Create a Free Telegram Bot
1. Open the **Telegram** app on your phone.
2. Search for `@BotFather` and click **Start**.
3. Send the command: `/newbot`
4. Follow the prompts to name your bot (e.g., `MyBitcoinQuantAlertsBot`).
5. `@BotFather` will give you an **API Token** (e.g. `7123456789:AAH...`). Copy this token.

### Step 2: Get Your Telegram Chat ID
1. Search for `@userinfobot` on Telegram and click **Start**.
2. It will reply with your personal **Id** (e.g. `123456789`). Copy this number.
3. Send a quick message (e.g. "Hello") to your newly created bot so it has permission to message you.

### Step 3: Add Environment Variables to Cloud Provider
In your Render / Railway / VPS dashboard, add these two Environment Variables:
- `TELEGRAM_BOT_TOKEN` = `your_bot_token_from_botfather`
- `TELEGRAM_CHAT_ID` = `your_chat_id_from_userinfobot`

Now, whenever a 5-minute scalp or institutional trade setup is generated, your Telegram bot will instantly send you a message like this:

```
🟢 BITCOIN 5M SCALP TRADE ALERT
━━━━━━━━━━━━━━━━━━━━
Direction: 🟢 LONG
Entry Price: $84,150.00
Stop Loss (Safety Net): $83,990.00
Target 1 (Take Profit): $84,415.00
Risk/Reward Ratio: 1.65 R
AI Confidence: 84.5%

🧠 Quantitative Setup Triggers:
• 5m EMA 9 crossed above EMA 21 (Bullish Momentum)
• Price bouncing from 5m VWAP ($84,120)
• Orderbook $4.2M Bid wall at $83,950 (+0.26 OBI)
```

---

## 🐳 Option 3: Free Always-On Linux VPS (Oracle Cloud / AWS / DigitalOcean)

If you have a Linux server (e.g. Oracle Cloud Always-Free ARM VM, AWS EC2 Free Tier, or a $4/month DigitalOcean droplet):

### Step 1: Install Docker on the Server
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
```

### Step 2: Clone and Start the 24/7 Container
```bash
git clone https://github.com/YOUR_USERNAME/bitcoin-ai-trading-system.git
cd bitcoin-ai-trading-system

# Start container in background with auto-restart on reboot
sudo docker-compose up -d --build
```

### Step 3: Check Status
```bash
sudo docker ps
sudo docker logs -f bitcoin_ai_engine
```

Your system is now running 24/7 at `http://YOUR_SERVER_IP:8000`!

---

## 📊 Summary of Deployment Files Included in the Project

| File | Purpose |
| :--- | :--- |
| [`requirements.txt`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/requirements.txt) | Python production package dependencies. |
| [`Dockerfile`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/Dockerfile) | Container definition for Docker & cloud hosting. |
| [`docker-compose.yml`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/docker-compose.yml) | 24/7 auto-restarting multi-container config. |
| [`render.yaml`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/render.yaml) | 1-click infrastructure as code for Render.com. |
| [`Procfile`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/Procfile) | Process launcher for PaaS cloud platforms. |
| [`app/services/alert_bot.py`](file:///c:/Users/kusha/Desktop/ANTIGRAVITY/bit_coint_experiment/app/services/alert_bot.py) | 24/7 Telegram and Discord phone notification dispatcher. |
