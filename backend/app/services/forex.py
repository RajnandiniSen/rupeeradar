import httpx
async def fetch_current_rate():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.frankfurter.dev/v1/latest?from=USD&to=INR")
    return response.json()["rates"]["INR"]