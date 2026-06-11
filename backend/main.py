from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from app.api.rates import router as rates_router
from app.core.db import engine, Base, get_db
from app.models.models import ExchangeRate, RateAlert, Recommendation
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rates_router)

def get_rate_vibe(db: Session):
    latest_rate = (
        db.query(ExchangeRate)
        .order_by(ExchangeRate.fetched_at.desc())
        .first()
    )

    if latest_rate is None:
        return {
            "message": "No rate vibes yet. Hit /api/rates/refresh first and let the rupee radar warm up."
        }

    if latest_rate.rate >= 84:
        message = "Big send-home energy. USD is looking strong against INR right now."
    elif latest_rate.rate >= 82:
        message = "Pretty decent vibes. Not fireworks, but a respectable time to send money home."
    else:
        message = "Maybe sip some chai and wait. The rate is not especially exciting right now."

    return {
        "rate": latest_rate.rate,
        "fetched_at": latest_rate.fetched_at,
        "message": message,
    }

@app.get("/health")
def health_status():
    return {"status" : "ok"}

@app.get("/vibe")
def rate_vibe(db: Session = Depends(get_db)):
    return get_rate_vibe(db)

@app.get("/", response_class=HTMLResponse)
@app.get("/vibe-ui", response_class=HTMLResponse)
def vibe_ui():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>RupeeRadar Vibe</title>
      <style>
        :root {
          color-scheme: light;
          --ink: #23322c;
          --muted: #60736a;
          --paper: #fffaf1;
          --mint: #bfe8d4;
          --rose: #f8bfc4;
          --saffron: #f9c66a;
          --blue: #95c8e8;
        }

        * {
          box-sizing: border-box;
        }

        body {
          min-height: 100vh;
          margin: 0;
          display: grid;
          place-items: center;
          padding: 24px;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(191, 232, 212, 0.9), transparent 34%),
            radial-gradient(circle at bottom right, rgba(249, 198, 106, 0.72), transparent 32%),
            linear-gradient(135deg, #fffaf1 0%, #f7fbf7 52%, #edf7ff 100%);
        }

        main {
          width: min(720px, 100%);
          padding: 32px;
          border: 1px solid rgba(35, 50, 44, 0.14);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.78);
          box-shadow: 0 24px 70px rgba(35, 50, 44, 0.16);
          backdrop-filter: blur(18px);
        }

        .topline {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 30px;
        }

        .brand {
          display: grid;
          gap: 4px;
        }

        h1 {
          margin: 0;
          font-size: clamp(2rem, 5vw, 4rem);
          line-height: 0.95;
          letter-spacing: 0;
        }

        .label {
          margin: 0;
          color: var(--muted);
          font-size: 0.95rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        button {
          min-height: 44px;
          border: 0;
          border-radius: 8px;
          padding: 0 18px;
          color: var(--ink);
          background: var(--saffron);
          font: inherit;
          font-weight: 800;
          cursor: pointer;
          box-shadow: inset 0 -2px 0 rgba(35, 50, 44, 0.12);
        }

        button:disabled {
          cursor: wait;
          opacity: 0.72;
        }

        .rate {
          display: flex;
          align-items: baseline;
          gap: 10px;
          margin: 0 0 18px;
          color: #175f43;
        }

        .rate strong {
          font-size: clamp(3rem, 13vw, 6.5rem);
          line-height: 0.9;
          letter-spacing: 0;
        }

        .rate span {
          color: var(--muted);
          font-weight: 800;
        }

        .message {
          margin: 0;
          font-size: clamp(1.2rem, 4vw, 2rem);
          line-height: 1.2;
          font-weight: 850;
        }

        .meta {
          margin: 24px 0 0;
          color: var(--muted);
          font-size: 0.95rem;
        }

        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 28px;
        }

        .chip {
          border-radius: 999px;
          padding: 8px 12px;
          background: var(--mint);
          font-size: 0.9rem;
          font-weight: 800;
        }

        .chip:nth-child(2) {
          background: var(--rose);
        }

        .chip:nth-child(3) {
          background: var(--blue);
        }

        @media (max-width: 560px) {
          main {
            padding: 24px;
          }

          .topline {
            align-items: stretch;
            flex-direction: column;
          }

          button {
            width: 100%;
          }
        }
      </style>
    </head>
    <body>
      <main>
        <div class="topline">
          <div class="brand">
            <p class="label">RupeeRadar</p>
            <h1>Send-home vibe check</h1>
          </div>
          <button id="refresh" type="button">Refresh rate</button>
        </div>

        <p class="rate"><strong id="rate">...</strong><span>INR per USD</span></p>
        <p class="message" id="message">Loading the latest vibe...</p>
        <p class="meta" id="meta"></p>

        <div class="chips" aria-label="Vibe scale">
          <span class="chip">82+ decent</span>
          <span class="chip">84+ strong</span>
          <span class="chip">Fresh from /vibe</span>
        </div>
      </main>

      <script>
        const rateEl = document.querySelector("#rate");
        const messageEl = document.querySelector("#message");
        const metaEl = document.querySelector("#meta");
        const refreshButton = document.querySelector("#refresh");

        async function loadVibe() {
          const response = await fetch("/vibe");
          const vibe = await response.json();

          rateEl.textContent = vibe.rate ? Number(vibe.rate).toFixed(2) : "--";
          messageEl.textContent = vibe.message;
          metaEl.textContent = vibe.fetched_at
            ? `Last checked ${new Date(vibe.fetched_at).toLocaleString()}`
            : "No saved rate yet.";
        }

        refreshButton.addEventListener("click", async () => {
          refreshButton.disabled = true;
          refreshButton.textContent = "Refreshing...";

          try {
            await fetch("/api/rates/refresh", { method: "POST" });
            await loadVibe();
          } finally {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh rate";
          }
        });

        loadVibe().catch(() => {
          rateEl.textContent = "--";
          messageEl.textContent = "Could not load the vibe. Check that the backend and database are running.";
          metaEl.textContent = "";
        });
      </script>
    </body>
    </html>
    """
