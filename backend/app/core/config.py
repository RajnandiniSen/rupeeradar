import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rupeeradar:rupeeradar123@localhost:5432/rupeeradar")
