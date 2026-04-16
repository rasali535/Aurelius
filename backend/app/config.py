import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "aurelius")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY")
    CIRCLE_ENTITY_SECRET_CIPHERTEXT = os.getenv("CIRCLE_ENTITY_SECRET_CIPHERTEXT")
    CIRCLE_USDC_CONTRACT = os.getenv("CIRCLE_USDC_CONTRACT")
    CIRCLE_API_URL = os.getenv("CIRCLE_API_URL", "https://api-sandbox.circle.com")

settings = Settings()
