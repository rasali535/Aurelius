"""
PostgreSQL-backed database layer for Aurelius.

Provides a MongoDB-style async API (find_one, insert_one, update_one, etc.)
over asyncpg so that existing service code requires minimal changes.
"""

import json
from typing import Optional, List
import os
import asyncio
import asyncpg
from app.config import settings
from app.utils import generate_id

# ---------------------------------------------------------------------------
# Cursor / query builder
# ---------------------------------------------------------------------------

class PGCursor:
    """Lazy cursor returned by collection.find() — supports chaining."""

    def __init__(self, pool, table: str, filter_doc: dict, projection: dict = None):
        self._pool = pool
        self._table = table
        self._filter = filter_doc or {}
        self._projection = projection 
        self._sort_field: Optional[str] = None
        self._sort_dir: int = 1 
        self._limit_val: Optional[int] = None
        self._skip_val: int = 0

    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            self._sort_field, self._sort_dir = key_or_list[0]
        else:
            self._sort_field = key_or_list
            self._sort_dir = direction if direction is not None else 1
        return self

    def limit(self, n):
        self._limit_val = n
        return self

    def skip(self, n):
        self._skip_val = n
        return self

    async def to_list(self, length=None):
        effective_limit = length or self._limit_val
        rows = await _query_rows(
            self._pool, self._table, self._filter,
            sort_field=self._sort_field,
            sort_dir=self._sort_dir,
            limit=effective_limit,
            skip=self._skip_val,
        )
        return rows


# ---------------------------------------------------------------------------
# Internal SQL helpers
# ---------------------------------------------------------------------------

def _build_where(filter_doc: dict):
    if not filter_doc:
        return "", []

    clauses = []
    params = []
    idx = 1

    for key, value in filter_doc.items():
        if key == "_id":
            if isinstance(value, dict) and "$in" in value:
                placeholders = ", ".join(f"${i}" for i in range(idx, idx + len(value["$in"])))
                clauses.append(f"id IN ({placeholders})")
                params.extend(value["$in"])
                idx += len(value["$in"])
            else:
                clauses.append(f"id = ${idx}")
                params.append(str(value))
                idx += 1
        else:
            if isinstance(value, dict) and "$in" in value:
                placeholders = ", ".join(f"${i}" for i in range(idx, idx + len(value["$in"])))
                clauses.append(f"data->>'{key}' IN ({placeholders})")
                params.extend([str(v) for v in value["$in"]])
                idx += len(value["$in"])
            else:
                clauses.append(f"data->>'{key}' = ${idx}")
                params.append(str(value))
                idx += 1

    return " AND ".join(clauses), params


def _row_to_doc(row) -> dict:
    data = row["data"]
    if isinstance(data, str):
        doc = json.loads(data)
    else:
        doc = dict(data) if data else {}
    doc["_id"] = row["id"]
    return doc


async def _ensure_table(pool, table: str):
    async with pool.acquire() as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id   TEXT PRIMARY KEY,
                data JSONB NOT NULL DEFAULT '{{}}'::jsonb
            )
        """)


async def _query_rows(pool, table: str, filter_doc: dict,
                      sort_field=None, sort_dir=1,
                      limit=None, skip=0) -> List[dict]:
    where, params = _build_where(filter_doc)
    sql = f"SELECT id, data FROM {table}"
    if where:
        sql += f" WHERE {where}"

    if sort_field:
        direction = "ASC" if sort_dir >= 0 else "DESC"
        if sort_field == "_id":
            sql += f" ORDER BY id {direction}"
        else:
            sql += f" ORDER BY data->>'{sort_field}' {direction}"

    if skip:
        sql += f" OFFSET {skip}"
    if limit is not None:
        sql += f" LIMIT {limit}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
    return [_row_to_doc(r) for r in rows]


# ---------------------------------------------------------------------------
# Collection wrapper
# ---------------------------------------------------------------------------

class PGCollection:
    def __init__(self, pool, table: str):
        self._pool = pool
        self._table = table

    async def find_one(self, filter_doc: dict = None) -> Optional[dict]:
        rows = await _query_rows(self._pool, self._table, filter_doc or {}, limit=1)
        return rows[0] if rows else None

    def find(self, filter_doc: dict = None, projection: dict = None) -> PGCursor:
        return PGCursor(self._pool, self._table, filter_doc or {}, projection)

    async def count_documents(self, filter_doc: dict = None) -> int:
        where, params = _build_where(filter_doc or {})
        sql = f"SELECT COUNT(*) FROM {self._table}"
        if where:
            sql += f" WHERE {where}"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
        return row[0]

    def aggregate(self, pipeline: list) -> "PGAggregateCursor":
        return PGAggregateCursor(self._pool, self._table, pipeline)

    async def insert_one(self, document: dict):
        doc = dict(document)
        doc_id = str(doc.pop("_id", None) or "")
        if not doc_id:
            doc_id = generate_id("doc")

        data_json = json.dumps(doc)
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self._table} (id, data) VALUES ($1, $2::jsonb) "
                f"ON CONFLICT (id) DO NOTHING",
                doc_id, data_json
            )
        return type("InsertResult", (), {"inserted_id": doc_id})()

    async def update_one(self, filter_doc: dict, update_doc: dict, upsert: bool = False):
        existing = await self.find_one(filter_doc)
        set_fields = update_doc.get("$set", {})

        if existing:
            doc_id = existing["_id"]
            merged = {k: v for k, v in existing.items() if k != "_id"}
            merged.update(set_fields)
            data_json = json.dumps(merged)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE {self._table} SET data = $1::jsonb WHERE id = $2",
                    data_json, doc_id
                )
        elif upsert:
            doc_id = str(filter_doc.get("_id", ""))
            if not doc_id:
                doc_id = generate_id("doc")
            data_json = json.dumps(set_fields)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"INSERT INTO {self._table} (id, data) VALUES ($1, $2::jsonb) "
                    f"ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
                    doc_id, data_json
                )

    async def delete_many(self, filter_doc: dict):
        where, params = _build_where(filter_doc or {})
        sql = f"DELETE FROM {self._table}"
        if where:
            sql += f" WHERE {where}"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, *params)


class PGAggregateCursor:
    def __init__(self, pool, table: str, pipeline: list):
        self._pool = pool
        self._table = table
        self._pipeline = pipeline

    async def to_list(self, length=None) -> list:
        for stage in self._pipeline:
            if "$group" in stage:
                group = stage["$group"]
                results = {}
                for out_field, expr in group.items():
                    if out_field == "_id":
                        continue
                    if isinstance(expr, dict) and "$sum" in expr:
                        sum_field = expr["$sum"]
                        if isinstance(sum_field, str) and sum_field.startswith("$"):
                            col = sum_field[1:]
                            sql = (
                                f"SELECT COALESCE(SUM((data->>'{col}')::numeric), 0) "
                                f"FROM {self._table}"
                            )
                            async with self._pool.acquire() as conn:
                                row = await conn.fetchrow(sql)
                            results[out_field] = float(row[0])
                if results:
                    return [results]
        return []


# ---------------------------------------------------------------------------
# Database wrapper
# ---------------------------------------------------------------------------

_TABLES = [
    "prompt_runs",
    "validation_requests",
    "payment_events",
    "config",
    "agents",
    "inference_logs",
]


class PGDatabase:
    def __init__(self, pool):
        self._pool = pool

    def __getattr__(self, name: str) -> PGCollection:
        return PGCollection(self._pool, name)

    def __getitem__(self, name: str) -> PGCollection:
        return PGCollection(self._pool, name)


async def init_db() -> PGDatabase:
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        raise RuntimeError("DATABASE_URL not set.")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Connecting to PostgreSQL...", flush=True)
    try:
        # Supabase transaction pooler (port 6543) often requires ssl='require' 
        # which enables TLS without necessarily requiring a CA match for self-signed certificates
        # if the system CA store is incomplete.
        pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=1,
            max_size=5,
            ssl='require', 
            command_timeout=60,
            statement_cache_size=0,
        )
    except Exception as e:
        print(f"FAILED to connect to PostgreSQL: {e}", flush=True)
        raise

    for table in _TABLES:
        await _ensure_table(pool, table)

    print("PostgreSQL ready.", flush=True)
    return PGDatabase(pool)

async def seed_initial_data(db_instance):
    print("Seeding initial data...", flush=True)
    
    # 1. Seed Validators
    from app.services.validator_service import seed_validators
    try:
        await seed_validators(db_instance)
    except Exception as e:
        print(f"Validator seeding failed: {e}", flush=True)
    
    # 2. Seed Requester Wallet
    from app.services.orchestrator_service import get_or_create_requester_wallet
    try:
        await get_or_create_requester_wallet(db_instance)
        print("Requester wallet ready.", flush=True)
    except Exception as e:
        print(f"Wallet seeding failed: {e}", flush=True)

    print("Seeding complete.", flush=True)


class DBProxy:
    def __init__(self):
        self._db: Optional["PGDatabase"] = None

    def set_db(self, db: PGDatabase):
        self._db = db

    def __getattr__(self, name: str):
        if self._db is None:
            raise RuntimeError("Database not initialized.")
        return getattr(self._db, name)

    def __getitem__(self, name: str):
        if self._db is None:
            raise RuntimeError("Database not initialized.")
        return self._db[name]


db = DBProxy()
