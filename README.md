# RupeeRadar

Track USD/INR exchange rates, visualize 30-day and 6-month history, and get AI-assisted transfer recommendations informed by live news sentiment.

**Live demo:** https://web-production-60300.up.railway.app

---

## What it does

- Fetches the live USD/INR rate every hour via the [Frankfurter API](https://www.frankfurter.dev/)
- Backfills historical rate data automatically on first boot (from 2026-01-01 to today), and fills any gaps on subsequent restarts
- Fetches the 5 most recent USD/INR news headlines from NewsAPI on every recommendation request
- Uses an LLM (Llama 3.3 70B via Groq) to generate a `send_now`, `wait`, or `neutral` verdict, factoring in rate position relative to the 30-day range and current news sentiment
- Supports two transfer directions — **USD → INR** (want rate high) and **INR → USD** (want rate low) — with the LLM prompt and verdict logic flipping accordingly
- Caches recommendations so the verdict only changes when the rate, stats, or headlines actually change
- Serves a single-page dashboard with a live rate card, direction toggle, AI recommendation, and an interactive chart with 30-day and 6-month views

---

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Server | Uvicorn |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| HTTP client | httpx |
| Background jobs | APScheduler |
| LLM inference | Groq (Llama 3.3 70B Versatile) |
| News data | NewsAPI |
| Rate data | Frankfurter API |
| Frontend | Vanilla JS + Chart.js (served inline) |

---

## Project structure

```
rupeeradar/
└── backend/
    ├── main.py                  # FastAPI app, lifespan, HTML UI
    ├── .env                     # Environment variables (not committed)
    ├── requirements.txt
    └── app/
        ├── api/
        │   └── rates.py         # API routes
        ├── core/
        │   ├── config.py        # Loads DATABASE_URL from env
        │   └── db.py            # SQLAlchemy engine, session, Base
        ├── models/
        │   └── models.py        # ExchangeRate, RateAlert, Recommendation
        └── services/
            ├── forex.py         # Frankfurter rate fetching + backfill
            ├── llm.py           # Groq recommendation + in-memory cache
            ├── news.py          # NewsAPI headline fetching
            └── scheduler.py     # APScheduler hourly refresh job
```

---

## Getting started

### Prerequisites

- Python 3.9+
- PostgreSQL running locally (or a connection string to a hosted instance)
- A [Groq API key](https://console.groq.com/)
- A [NewsAPI key](https://newsapi.org/)

### 1. Clone and install

```bash
git clone https://github.com/RajnandiniSen/rupeeradar.git
cd rupeeradar
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configure environment

Create `backend/.env`:

```env
DATABASE_URL=postgresql://rupeeradar:rupeeradar123@localhost:5432/rupeeradar
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_newsapi_key
```

### 3. Create the database

```bash
psql postgres -c "CREATE USER rupeeradar WITH PASSWORD 'rupeeradar123';"
psql postgres -c "CREATE DATABASE rupeeradar OWNER rupeeradar;"
```

Tables are created automatically on first boot via SQLAlchemy.

### 4. Run

```bash
PYTHONPATH=backend uvicorn backend.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

On first boot, the app detects an empty database and automatically backfills historical rates from 2026-01-01 to today. On subsequent restarts it only fills any gap since the last stored date.

---

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Dashboard UI |
| `GET` | `/health` | Health check |
| `GET` | `/vibe` | Latest rate with a plain-English assessment |
| `GET` | `/api/rates/history?days=30` | Rate history for the last N days |
| `GET` | `/api/rates/recommend?direction=usd_to_inr` | AI recommendation (`usd_to_inr` or `inr_to_usd`) |
| `POST` | `/api/rates/refresh` | Manually trigger a rate fetch and store |
| `POST` | `/api/rates/backfill?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | Backfill a date range |

---

## How the recommendation works

1. The latest rate and 30-day high/low/avg are pulled from the database
2. Five recent headlines about USD/INR are fetched live from NewsAPI
3. The direction parameter determines whether a high or low rate is favorable
4. All inputs are hashed — if the hash matches the last call, the cached result is returned immediately
5. On a cache miss, the prompt is sent to Llama 3.3 70B via Groq with `temperature=0` for deterministic output
6. The LLM is instructed to cite at least one headline in its reasoning and return a structured `VERDICT` / `REASON` response

---

## Deployment notes

- Set `DATABASE_URL`, `GROQ_API_KEY`, and `NEWS_API_KEY` as environment variables in your hosting platform
- The app uses `python-dotenv` so a `.env` file also works in non-containerized environments
- The in-memory recommendation cache resets on each restart — this is intentional, as fresh headlines should be re-evaluated on boot
- The backfill on startup is idempotent: it only requests date ranges not already in the database