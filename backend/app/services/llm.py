import os
from typing import Optional, List

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


def get_recommendation(
    current_rate,
    high_30d,
    low_30d,
    avg_30d,
    headlines: Optional[List[str]] = None,
    direction: str = "usd_to_inr",
):
    headlines_section = ""
    headlines_instruction = ""
    if headlines:
        formatted = "\n".join(f"- {h}" for h in headlines)
        headlines_section = f"\nRecent news headlines about USD/INR:\n{formatted}\n"
        headlines_instruction = " You MUST reference at least one of the headlines above in your REASON."

    if direction == "usd_to_inr":
        context = "someone sending USD to INR (e.g. remitting money to India). They receive MORE rupees when the rate is HIGH, so a high rate is favorable."
        favorable = "near its 30-day high"
    else:
        context = "someone sending INR to USD (e.g. remitting money to the US). They get MORE dollars when the rate is LOW, so a low rate is favorable."
        favorable = "near its 30-day low"

    prompt = f"""
You are a USD/INR exchange rate assistant.

The current USD/INR rate is {current_rate}.
Over the last 30 days:
- The highest rate was {high_30d}
- The lowest rate was {low_30d}
- The average rate was {avg_30d}
{headlines_section}
You are advising {context}

Based on this context, give a recommendation. A rate {favorable} is the best time to act.{headlines_instruction}
Return a verdict of exactly one of these values: "send_now", "wait", or "neutral".
Respond in this exact format:
VERDICT: send_now
REASON: The current rate is near its 30-day high, making this a favorable time to send money.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content
    verdict = "neutral"
    reasoning = text

    for line in text.splitlines():
        if line.startswith("VERDICT:"):
            verdict = line.replace("VERDICT:", "", 1).strip()
        elif line.startswith("REASON:"):
            reasoning = line.replace("REASON:", "", 1).strip()

    return {"verdict": verdict, "reasoning": reasoning}
