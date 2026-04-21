import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "aurelius")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY")
    CIRCLE_ENTITY_SECRET = os.getenv("CIRCLE_ENTITY_SECRET")
    CIRCLE_ENTITY_PUBLIC_KEY = os.getenv("CIRCLE_ENTITY_PUBLIC_KEY")
    CIRCLE_ENTITY_SECRET_CIPHERTEXT = os.getenv("CIRCLE_ENTITY_SECRET_CIPHERTEXT")
    CIRCLE_MASTER_WALLET_ID = os.getenv("CIRCLE_MASTER_WALLET_ID")
    CIRCLE_USDC_CONTRACT = os.getenv("CIRCLE_USDC_CONTRACT")
    CIRCLE_API_URL = os.getenv("CIRCLE_API_URL", "https://api-sandbox.circle.com")
    ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")
    CIRCLE_APP_ID = os.getenv("CIRCLE_APP_ID")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
    AIML_API_KEY = os.getenv("AIML_API_KEY")
    AIML_API_URL = os.getenv("AIML_API_URL", "https://api.aimlapi.com/v1")
    MOCK_PAYMENTS = os.getenv("MOCK_PAYMENTS", "false").lower() == "true"

settings = Settings()
