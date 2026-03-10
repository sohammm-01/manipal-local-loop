```
  __  __             _             _   _                 _
 |  \/  | __ _ _ __ (_)_ __   __ _| | | |    ___   ___  _ __
 | |\/| |/ _` | '_ \| | '_ \ / _` | | | |   / _ \ / _ \| '_ \
 | |  | | (_| | | | | | |_) | (_| | | | |__| (_) | (_) | |_) |
 |_|  |_|\__,_|_| |_|_| .__/ \__,_|_| |_____\___/ \___/| .__/
                       |_|                               |_|
```

# 🌀 Manipal Local Loop

**Your hyperlocal news loop for Manipal — power cuts, traffic, events, and more, delivered straight to Telegram.**

[![CI](https://github.com/your-username/manipal-local-loop/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/manipal-local-loop/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-orange.svg)](https://flake8.pycqa.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)](https://t.me/)

---

## ✨ Features

- ⚡ **Power Cut Alerts** — MESCOM-sourced scheduled outage notices
- 🌦 **Weather Warnings** — OpenWeatherMap real-time alerts for heavy rain, storms & heat
- 🚗 **Traffic Updates** — Road blocks and NH66 congestion from Twitter/X & news
- 🎓 **Academic Notices** — MAHE official circulars and exam schedules
- 🎉 **Campus Events** — Hackathons, fests, workshops scraped from multiple sources
- 🚨 **Emergency Alerts** — Fires, police activity, evacuation notices
- 📰 **City News** — Google News RSS for Manipal, Udupi & Mangaluru (last 24 h)
- 💬 **Campus Chatter** — r/manipal and r/udupi Reddit threads
- 🤖 **AI Summaries** — Gemini Pro daily briefings
- 📬 **Subscriptions** — Per-category push notifications

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Manipal Local Loop                      │
├────────────────┬───────────────────┬────────────────────────┤
│   Scrapers     │   Processing      │   Delivery             │
│                │                   │                        │
│ Google News    │ Dedup (SHA-256)   │ Telegram Bot           │
│ MAHE Notices   │ Translator        │  ├─ Commands           │
│ Reddit         │ Classifier        │  ├─ Push Notifications │
│ Twitter/Nitter │ Urgency Scorer    │  └─ Daily Digest       │
│ Power Cuts     │                   │                        │
│ Weather (OWM)  │   Summarizer      │   Scheduler            │
│                │   (Gemini Pro)    │  ├─ Scrape (30 min)    │
│                │                   │  ├─ Notify (30 min)    │
│                │   Database        │  ├─ Digest (08:00 IST) │
│                │   (SQLite WAL)    │  └─ Cleanup (23:00 IST)│
└────────────────┴───────────────────┴────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Bot Framework | python-telegram-bot v20 (async) |
| Scraping | feedparser, BeautifulSoup4, requests |
| AI Summaries | Google Gemini Pro |
| Database | SQLite (WAL mode) |
| Scheduling | APScheduler (AsyncIO) |
| Translation | googletrans |
| Weather | OpenWeatherMap API |
| CI | GitHub Actions |
| Container | Docker / Docker Compose |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A [Telegram Bot Token](https://core.telegram.org/bots/tutorial) from @BotFather
- (Optional) [Google Gemini API key](https://ai.google.dev/)
- (Optional) [OpenWeatherMap API key](https://openweathermap.org/api)

### 1. Clone & install

```bash
git clone https://github.com/your-username/manipal-local-loop.git
cd manipal-local-loop
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Run

```bash
python main.py
```

### 4. Docker

```bash
docker-compose up -d
```

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Register and receive a welcome message |
| `/help` | Show all available commands |
| `/powercut` | Latest MESCOM power cut notices |
| `/weather` | Current weather & severe weather alerts |
| `/events` | Upcoming events in and around Manipal |
| `/news` | Latest city news (last 24 h) |
| `/traffic` | Traffic updates and road blocks |
| `/campus` | Campus chatter from Reddit |
| `/alerts` | High-urgency alerts (last 12 h) |
| `/digest` | Today's full news digest |
| `/subscribe <cat>` | Subscribe to a category's push notifications |
| `/unsubscribe <cat>` | Unsubscribe from a category |
| `/mystatus` | View your subscription settings |
| `/report` | Report a local issue |

---

## 📁 Project Structure

```
manipal-local-loop/
├── .github/workflows/ci.yml     # GitHub Actions CI
├── src/manipal_loop/
│   ├── config.py                # Environment-based config
│   ├── scrapers/                # Six source scrapers
│   ├── database/                # SQLite models & access layer
│   ├── processing/              # Dedup, translation, classify, urgency
│   ├── summarizer/              # Gemini Pro summariser
│   ├── bot/                     # Telegram bot & command handlers
│   └── scheduler/               # APScheduler jobs
├── tests/                       # pytest test suite
├── main.py                      # Entry point
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚙️ How It Works

1. **Every 30 minutes** the scheduler triggers all scrapers in parallel.
2. Each item is hashed (SHA-256) for deduplication before storage.
3. Items are classified by category and scored for urgency (1–5).
4. Urgency ≥ 4 items trigger immediate push notifications to subscribers.
5. **Every morning at 8:00 AM IST** a Gemini-generated daily digest is sent.
6. Updates older than 7 days are pruned nightly at 11:00 PM IST.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Make your changes with tests
4. Ensure `pytest` and `flake8` pass
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

---

## 👤 Author

Built with ❤️ for the Manipal community.

> *Stay informed. Stay local.*
