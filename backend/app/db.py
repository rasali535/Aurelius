import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class AsyncMockWrapper:
    """Wraps a mongomock collection to support 'await' on common methods."""
    def __init__(self, collection):
        self._collection = collection
    
    def __getattr__(self, name):
        attr = getattr(self._collection, name)
        if callable(attr):
            # Methods that should NOT be async (they return cursors or self)
            if name in ["find", "sort", "limit", "skip", "aggregate"]:
                return attr
            
            # Methods that SHOULD be async
            async def async_wrapper(*args, **kwargs):
                return attr(*args, **kwargs)
            return async_wrapper
        return attr

class AsyncMockDB:
    """Wraps a mongomock database to return AsyncMockWrapper for collections."""
    def __init__(self, db):
        self._db = db
    
    def __getitem__(self, name):
        return AsyncMockWrapper(self._db[name])
    
    def __getattr__(self, name):
        return AsyncMockWrapper(getattr(self._db, name))

async def init_db():
    try:
        # Use motor for async mongo access
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Check connection
        await client.server_info()
        db = client[settings.MONGODB_DB]
        print(f"Connected to MongoDB at {settings.MONGODB_URI} (Async)")
        return db
    except Exception as e:
        import mongomock
        print(f"MongoDB connection failed: {e}. Falling back to AsyncMock (mongomock).")
        client = mongomock.MongoClient()
        mock_db = client[settings.MONGODB_DB]
        return AsyncMockDB(mock_db)

# Since the rest of the app imports 'db' directly, we need a proxy or to initialize it
class DBProxy:
    def __init__(self):
        self._db = None

    def set_db(self, db):
        self._db = db

    def __getattr__(self, name):
        if self._db is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return getattr(self._db, name)

    def __getitem__(self, name):
        if self._db is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self._db[name]

db = DBProxy()
