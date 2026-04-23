import asyncio
import httpx
from postgrest import AsyncPostgrestClient
from app.config import settings

class SupabaseCursorWrapper:
    def __init__(self, data):
        self._data = data

    def sort(self, key, direction=1):
        reverse = direction == -1
        try:
            self._data.sort(key=lambda x: x.get(key) or "", reverse=reverse)
        except:
            pass
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    async def to_list(self, length=None):
        if length is not None:
            return self._data[:length]
        return self._data

class SupabaseCollectionWrapper:
    def __init__(self, client: AsyncPostgrestClient, table_name: str):
        self._client = client
        self._table_name = table_name

    def _map_id(self, data):
        if not data: return data
        if isinstance(data, list):
            return [self._map_id(item) for item in data]
        if "id" in data:
            data["_id"] = data["id"]
        elif "_id" in data:
            data["id"] = data["_id"]
        return data

    async def insert_one(self, document):
        doc = document.copy()
        if "_id" in doc:
            if "id" not in doc:
                doc["id"] = doc.pop("_id")
            else:
                doc.pop("_id")
        
        resp = await self._client.table(self._table_name).insert(doc).execute()
        return self._map_id(resp.data[0] if resp.data else None)

    async def find_one(self, filter):
        query = self._client.table(self._table_name).select("*")
        for k, v in filter.items():
            key = "id" if k == "_id" else k
            query = query.eq(key, v)
        
        resp = await query.limit(1).execute()
        data = resp.data[0] if resp.data else None
        return self._map_id(data)

    def find(self, filter=None, projection=None):
        query = self._client.table(self._table_name).select("*")
        if filter:
            for k, v in filter.items():
                key = "id" if k == "_id" else k
                query = query.eq(key, v)
        
        class AsyncCursor:
            def __init__(self, query_builder, map_fn):
                self.query_builder = query_builder
                self.map_fn = map_fn

            def sort(self, key, direction=1):
                desc = direction == -1
                self.query_builder = self.query_builder.order(key, desc=desc)
                return self

            def limit(self, n):
                self.query_builder = self.query_builder.limit(n)
                return self

            async def to_list(self, length=None):
                resp = await self.query_builder.execute()
                data = self.map_fn(resp.data)
                if length:
                    return data[:length]
                return data

        return AsyncCursor(query, self._map_id)

    async def update_one(self, filter, update, upsert=False):
        data_to_update = update.get("$set", update)
        
        if upsert:
            # For upsert, we need to merge filter and data
            upsert_doc = data_to_update.copy()
            for k, v in filter.items():
                key = "id" if k == "_id" else k
                upsert_doc[key] = v
            
            # Postgrest upsert uses on_conflict if needed, 
            # but by default it uses the primary key.
            resp = await self._client.table(self._table_name).upsert(upsert_doc).execute()
            return self._map_id(resp.data[0] if resp.data else None)

        query = self._client.table(self._table_name).update(data_to_update)
        for k, v in filter.items():
            key = "id" if k == "_id" else k
            query = query.eq(key, v)
        
        resp = await query.execute()
        return self._map_id(resp.data[0] if resp.data else None)

    async def count_documents(self, filter=None):
        query = self._client.table(self._table_name).select("*", count="exact")
        if filter:
            for k, v in filter.items():
                key = "id" if k == "_id" else k
                query = query.eq(key, v)
        
        resp = await query.limit(0).execute()
        return resp.count or 0

    def aggregate(self, pipeline):
        field_to_sum = None
        for stage in pipeline:
            if "$group" in stage:
                group = stage["$group"]
                for k, v in group.items():
                    if isinstance(v, dict) and "$sum" in v:
                        val = v["$sum"]
                        if isinstance(val, str) and val.startswith("$"):
                            field_to_sum = val[1:]
        
        class SumCursor:
            def __init__(self, client, table, field):
                self.client = client
                self.table = table
                self.field = field
            
            async def to_list(self, length=None):
                if not self.field: return []
                resp = await self.client.table(self.table).select(self.field).execute()
                total = sum(item.get(self.field, 0) or 0 for item in resp.data)
                return [{"total": total}]

        return SumCursor(self._client, self._table_name, field_to_sum)

class SupabaseDBWrapper:
    def __init__(self, client: AsyncPostgrestClient):
        self._client = client

    def __getitem__(self, name):
        return SupabaseCollectionWrapper(self._client, name)
    
    def __getattr__(self, name):
        return SupabaseCollectionWrapper(self._client, name)

async def init_db():
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            rest_url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1"
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}"
            }
            client = AsyncPostgrestClient(rest_url, headers=headers)
            print(f"Connected to Supabase Postgrest at {rest_url}")
            return SupabaseDBWrapper(client)
        except Exception as e:
            print(f"Supabase connection failed: {e}. Falling back to mongomock.")
    
    import mongomock
    from app.db_mock import AsyncMockDB
    print("Supabase not configured. Falling back to AsyncMock (mongomock).")
    client = mongomock.MongoClient()
    mock_db = client["aurelius"]
    return AsyncMockDB(mock_db)

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
