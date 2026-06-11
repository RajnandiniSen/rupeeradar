import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


def get_recommendation(current_rate, high_30d, low_30d, avg_30d):

    prompt = f"""
You are a USD to INR exchange rate assistant.

The current USD/INR rate is {current_rate}.
Over the last 30 days:
- The highest rate was {high_30d}
- The lowest rate was {low_30d}
- The average rate was {avg_30d}

Based on this context, give a recommendation for someone deciding whether to send USD to INR now.
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
