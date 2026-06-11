import os
import httpx
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = (
    "https://newsapi.org/v2/everything"
    "?q=USD+INR+rupee&language=en&sortBy=publishedAt&pageSize=5"
    "&apiKey={key}"
)

async def fetch_headlines() -> list[str]:
    url = NEWS_API_URL.format(key=NEWS_API_KEY)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    response.raise_for_status()
    articles = response.json().get("articles", [])
    return [article["title"] for article in articles if article.get("title")]
