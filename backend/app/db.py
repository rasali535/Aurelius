from pymongo import MongoClient
from app.config import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]
