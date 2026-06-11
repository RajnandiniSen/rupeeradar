from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from app.api.rates import router as rates_router
from app.core.db import engine, Base, get_db
from app.models.models import ExchangeRate, RateAlert, Recommendation
from app.services.forex import backfill_rates
from app.services.scheduler import start_scheduler
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    try:
        is_empty = db.query(ExchangeRate).first() is None
        if is_empty:
            start_date = str(date.today() - timedelta(days=183))
            end_date = str(date.today())
            await backfill_rates(db, start_date, end_date)
    finally:
        db.close()

    scheduler = start_scheduler()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(rates_router)

def get_rate_vibe(db: Session):
    latest_rate = (
        db.query(ExchangeRate)
        .order_by(ExchangeRate.fetched_at.desc())
        .first()
    )

    if latest_rate is None:
        return {
            "message": "No exchange rate has been saved yet. Refresh the rate to begin tracking USD/INR."
        }

    if latest_rate.rate >= 84:
        message = "USD is currently strong against INR based on the latest saved rate."
    elif latest_rate.rate >= 82:
        message = "The current USD/INR rate is within a reasonable transfer range."
    else:
        message = "The current USD/INR rate is below the stronger recent transfer levels."

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
      <title>RupeeRadar Dashboard</title>
      <style>
        :root {
          color-scheme: light;
          --stage: #d8e2dc;
          --sheet: #ffe5d9;
          --ink: #221316;
          --muted: #6f4f58;
          --alabaster: #d8e2dc;
          --powder: #ffe5d9;
          --pastel-pink: #ffcad4;
          --cherry: #f4acb7;
          --dusty-mauve: #9d8189;
          --report-blue: #9fc7e8;
          --custard: #efe9ae;
          --tea-green: #cdeac0;
          --salmon: #ff928b;
          --pale: #fff7f2;
          --dark: #221316;
        }

        * {
          box-sizing: border-box;
        }

        html {
          overflow-x: hidden;
        }

        body {
          min-height: 100vh;
          margin: 0;
          padding: 34px 18px;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--ink);
          background: #ffffff;
          overflow-x: hidden;
        }

        .app-shell {
          width: min(960px, 100%);
          margin: 0 auto;
          padding: 22px;
          border-radius: 14px;
          background: var(--sheet);
          box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
        }

        .site-header-inner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          margin-bottom: 24px;
        }

        .brand-mark {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 1.5rem;
          font-weight: 900;
        }

        .brand-dot {
          width: 28px;
          height: 28px;
          border-radius: 999px;
          background: var(--cherry);
          box-shadow: inset 0 0 0 7px var(--sheet), 0 0 0 1px var(--ink);
        }

        button {
          min-height: 28px;
          border: 0;
          border-radius: 999px;
          padding: 0 16px;
          color: var(--ink);
          background: var(--pale);
          font: inherit;
        }

        button {
          background: var(--dark);
          color: var(--pale);
          cursor: pointer;
        }

        button:disabled {
          cursor: wait;
          opacity: 0.72;
        }

        main {
          display: grid;
          gap: 22px;
        }

        .hero-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
        }

        .rate-card,
        .recommendation,
        .chart-section,
        .footer-panel {
          min-width: 0;
          border-radius: 22px;
          overflow: hidden;
        }

        .rate-card {
          padding: 26px;
          color: var(--ink);
          background: var(--report-blue);
        }

        .rate-card .label,
        .rate-card .meta {
          color: var(--muted);
        }

        .rate-card .rate strong {
          color: var(--ink);
        }

        h1 {
          margin: 0 0 18px;
          font-size: clamp(2.1rem, 4vw, 3.35rem);
          line-height: 0.98;
          letter-spacing: 0;
        }

        .label {
          margin: 0 0 8px;
          color: var(--muted);
          font-size: 0.76rem;
          font-weight: 850;
          text-transform: uppercase;
        }

        .rate {
          display: grid;
          gap: 2px;
          margin: 0 0 16px;
          color: var(--ink);
        }

        .rate strong {
          font-size: clamp(4rem, 9vw, 6.25rem);
          line-height: 0.84;
          letter-spacing: 0;
        }

        .rate span {
          font-size: 0.92rem;
          font-weight: 850;
        }

        .message {
          margin: 0;
          font-size: 0.94rem;
          line-height: 1.35;
          font-weight: 750;
        }

        .meta {
          margin: 16px 0 0;
          color: var(--muted);
          font-size: 0.82rem;
          font-weight: 750;
        }

        .recommendation {
          padding: 26px;
          background: var(--custard);
        }

        .recommendation.neutral {
          background: var(--custard);
        }

        .recommendation.wait {
          background: var(--salmon);
        }

        .recommendation.yes {
          background: var(--tea-green);
        }

        .recommendation-label {
          margin: 0 0 16px;
          color: var(--muted);
          font-size: 0.78rem;
          font-weight: 850;
          text-transform: uppercase;
        }

        .recommendation-verdict {
          margin: 0;
          color: var(--ink);
          font-size: clamp(2.4rem, 5vw, 4rem);
          line-height: 0.95;
          font-weight: 900;
          text-transform: capitalize;
        }

        .recommendation-reasoning {
          margin: 18px 0 0;
          color: var(--muted);
          font-size: 0.95rem;
          line-height: 1.45;
          font-weight: 700;
        }

        .direction-toggle {
          display: flex;
          gap: 6px;
          margin-bottom: 16px;
        }

        .dir-button {
          min-height: 30px;
          border: 1px solid rgba(34, 19, 22, 0.14);
          border-radius: 999px;
          padding: 0 13px;
          color: var(--ink);
          background: rgba(255,255,255,0.45);
          font-size: 0.8rem;
          font-weight: 850;
          cursor: pointer;
        }

        .dir-button.active {
          color: var(--pale);
          background: var(--dark);
          border-color: var(--dark);
        }

        .chart-section {
          padding: 24px;
          background: var(--powder);
        }

        .chart-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 10px;
        }

        .chart-title {
          margin: 0;
          font-size: clamp(1.55rem, 4vw, 2.35rem);
          font-weight: 900;
        }

        .chart-note {
          margin: 0;
          color: var(--muted);
          font-size: 0.82rem;
          font-weight: 850;
        }

        .range-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 16px;
        }

        .range-button {
          min-height: 34px;
          border: 1px solid rgba(34, 19, 22, 0.14);
          border-radius: 999px;
          padding: 0 14px;
          color: var(--ink);
          background: var(--pastel-pink);
          font-size: 0.82rem;
          font-weight: 850;
          cursor: pointer;
        }

        .range-button.active {
          color: var(--pale);
          background: var(--dark);
        }

        .chart-wrap {
          position: relative;
          height: 300px;
          width: 100%;
          max-width: 100%;
          overflow: hidden;
        }

        #history-chart {
          display: block;
          width: 100% !important;
          max-width: 100% !important;
          height: 100% !important;
        }

        .footer-panel {
          padding: 24px;
          color: var(--pale);
          background: var(--dark);
        }

        .footer-panel strong {
          display: block;
          color: var(--cherry);
          font-size: clamp(1.8rem, 5vw, 3rem);
          line-height: 0.95;
          letter-spacing: 0;
        }

        .footer-panel span {
          display: block;
          max-width: 520px;
          margin-top: 12px;
          color: rgba(255,248,216,0.78);
          font-size: 0.85rem;
          line-height: 1.4;
        }

        @media (max-width: 820px) {
          body {
            padding: 16px;
          }

          .app-shell {
            padding: 16px;
          }

          .site-header-inner {
            align-items: center;
            flex-direction: row;
            margin-bottom: 22px;
          }

          .hero-grid {
            grid-template-columns: 1fr;
          }

          .rate-card,
          .recommendation,
          .chart-section {
            padding: 20px;
          }

          .chart-head {
            align-items: flex-start;
            flex-direction: column;
            gap: 4px;
          }

          .chart-wrap {
            height: 250px;
          }
        }
      </style>
    </head>
    <body>
      <div class="app-shell">
        <header class="site-header">
          <div class="site-header-inner">
            <div class="brand-mark">
              <span class="brand-dot" aria-hidden="true"></span>
              <span>RupeeRadar</span>
            </div>
            <button id="refresh" type="button">Refresh</button>
          </div>
        </header>

        <main>
          <section class="hero-grid" aria-label="USD to INR overview">
            <div class="rate-card">
              <h1>USD/INR report</h1>
              <p class="label">Current rate</p>
              <p class="rate"><strong id="rate">...</strong><span>INR per USD</span></p>
              <p class="message" id="message">Loading the latest rate assessment...</p>
              <p class="meta" id="meta"></p>
            </div>

            <section class="recommendation neutral" id="recommendation-card" aria-label="AI recommendation">
              <div class="direction-toggle" aria-label="Transfer direction">
                <button class="dir-button active" type="button" data-direction="usd_to_inr">USD → INR</button>
                <button class="dir-button" type="button" data-direction="inr_to_usd">INR → USD</button>
              </div>
              <p class="recommendation-label">Recommendation</p>
              <p class="recommendation-verdict" id="recommendation-verdict">Loading...</p>
              <p class="recommendation-reasoning" id="recommendation-reasoning"></p>
            </section>
          </section>

          <section class="chart-section" aria-label="USD to INR history">
            <div class="chart-head">
              <h2 class="chart-title" id="chart-title">Last 30 days</h2>
              <p class="chart-note" id="chart-note">Loading history...</p>
            </div>
            <div class="range-controls" aria-label="History range">
              <button class="range-button active" type="button" data-days="30" data-label="Last 30 days">30 days</button>
              <button class="range-button" type="button" data-days="183" data-label="Last 6 months">6 months</button>
            </div>
            <div class="chart-wrap">
              <canvas id="history-chart"></canvas>
            </div>
          </section>

          <section class="footer-panel" aria-label="RupeeRadar summary">
            <strong>RupeeRadar</strong>
            <span>Track recent USD to INR movement, compare the latest rate against the 30-day range, and review an AI-assisted transfer recommendation.</span>
          </section>
        </main>
      </div>

      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <script>
        const rateEl = document.querySelector("#rate");
        const messageEl = document.querySelector("#message");
        const metaEl = document.querySelector("#meta");
        const refreshButton = document.querySelector("#refresh");
        const chartTitleEl = document.querySelector("#chart-title");
        const chartNoteEl = document.querySelector("#chart-note");
        const historyChartEl = document.querySelector("#history-chart");
        const rangeButtons = document.querySelectorAll(".range-button");
        const dirButtons = document.querySelectorAll(".dir-button");
        const recommendationCardEl = document.querySelector("#recommendation-card");
        const recommendationVerdictEl = document.querySelector("#recommendation-verdict");
        const recommendationReasoningEl = document.querySelector("#recommendation-reasoning");
        let historyChart;
        let historyRequestId = 0;
        let selectedHistoryRange = {
          days: 30,
          label: "Last 30 days",
        };
        let selectedDirection = "usd_to_inr";

        async function loadVibe() {
          const response = await fetch("/vibe");
          const vibe = await response.json();

          rateEl.textContent = vibe.rate ? Number(vibe.rate).toFixed(2) : "--";
          messageEl.textContent = vibe.message;
          metaEl.textContent = vibe.fetched_at
            ? `Last checked ${new Date(vibe.fetched_at).toLocaleString()}`
            : "No saved rate yet.";
        }

        function formatVerdict(verdict) {
          return verdict
            ? verdict.replaceAll("_", " ")
            : "neutral";
        }

        function recommendationClass(verdict) {
          if (verdict === "wait") {
            return "wait";
          }
          if (verdict === "send_now" || verdict === "yes") {
            return "yes";
          }
          return "neutral";
        }

        async function loadRecommendation() {
          const response = await fetch(`/api/rates/recommend?direction=${selectedDirection}`);
          if (!response.ok) {
            throw new Error("Could not load recommendation");
          }

          const recommendation = await response.json();
          recommendationCardEl.className = `recommendation ${recommendationClass(recommendation.verdict)}`;
          recommendationVerdictEl.textContent = formatVerdict(recommendation.verdict);
          recommendationReasoningEl.textContent = recommendation.reasoning;
        }

        async function loadHistory(days = selectedHistoryRange.days, label = selectedHistoryRange.label) {
          const requestId = historyRequestId + 1;
          historyRequestId = requestId;
          const response = await fetch(`/api/rates/history?days=${days}`);
          const history = await response.json();

          if (requestId !== historyRequestId) {
            return;
          }

          const labels = history.map((row) =>
            new Date(row.fetched_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })
          );
          const rates = history.map((row) => Number(row.rate));

          chartTitleEl.textContent = label;
          if (history.length) {
            const firstDate = new Date(history[0].fetched_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric",
            });
            const lastDate = new Date(history[history.length - 1].fetched_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric",
            });
            chartNoteEl.textContent = `${history.length} data points, ${firstDate} to ${lastDate}`;
          } else {
            chartNoteEl.textContent = `No ${label.toLowerCase()} history available`;
          }

          if (historyChart) {
            historyChart.data.labels = labels;
            historyChart.data.datasets[0].data = rates;
            historyChart.update();
            return;
          }

          historyChart = new Chart(historyChartEl, {
            type: "line",
            data: {
              labels,
              datasets: [
                {
                  label: "USD/INR",
                  data: rates,
                  borderColor: "#9d8189",
                  backgroundColor: "rgba(255, 202, 212, 0.5)",
                  borderWidth: 3,
                  pointBackgroundColor: "#f4acb7",
                  pointBorderColor: "#221316",
                  pointRadius: 4,
                  pointHoverRadius: 6,
                  tension: 0.28,
                  fill: true,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                intersect: false,
                mode: "index",
              },
              plugins: {
                legend: {
                  display: false,
                },
                tooltip: {
                  callbacks: {
                    label: (context) => `USD/INR ${Number(context.parsed.y).toFixed(2)}`,
                  },
                },
              },
              scales: {
                x: {
                  grid: {
                    display: false,
                  },
                  ticks: {
                    color: "#6f4f58",
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 6,
                  },
                },
                y: {
                  ticks: {
                    color: "#6f4f58",
                    callback: (value) => Number(value).toFixed(1),
                  },
                  grid: {
                    color: "rgba(157, 129, 137, 0.22)",
                  },
                },
              },
            },
          });
        }

        dirButtons.forEach((button) => {
          button.addEventListener("click", async () => {
            selectedDirection = button.dataset.direction;
            dirButtons.forEach((b) => b.classList.toggle("active", b === button));
            recommendationVerdictEl.textContent = "Loading...";
            recommendationReasoningEl.textContent = "";
            recommendationCardEl.className = "recommendation neutral";
            try {
              await loadRecommendation();
            } catch {
              recommendationVerdictEl.textContent = "Unavailable";
            }
          });
        });

        rangeButtons.forEach((button) => {
          button.addEventListener("click", async () => {
            selectedHistoryRange = {
              days: Number(button.dataset.days),
              label: button.dataset.label,
            };

            rangeButtons.forEach((rangeButton) => {
              rangeButton.classList.toggle("active", rangeButton === button);
            });

            chartNoteEl.textContent = "Loading history...";
            try {
              await loadHistory();
            } catch {
              chartNoteEl.textContent = "History unavailable";
            }
          });
        });

        refreshButton.addEventListener("click", async () => {
          refreshButton.disabled = true;
          refreshButton.textContent = "Refreshing...";

          try {
            await fetch("/api/rates/refresh", { method: "POST" });
            await loadVibe();
            await loadRecommendation();
            await loadHistory();
          } finally {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh rate";
          }
        });

        loadVibe().catch(() => {
          rateEl.textContent = "--";
          messageEl.textContent = "Unable to load the latest exchange rate. Check that the backend and database are running.";
          metaEl.textContent = "";
        });

        loadHistory().catch(() => {
          chartNoteEl.textContent = "History unavailable";
        });

        loadRecommendation().catch(() => {
          recommendationCardEl.className = "recommendation neutral";
          recommendationVerdictEl.textContent = "Unavailable";
          recommendationReasoningEl.textContent = "A recommendation is not available yet. Confirm that recent rate history and the LLM service are configured.";
        });
      </script>
    </body>
    </html>
    """
