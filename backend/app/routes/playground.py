from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from app.db import db
import json

router = APIRouter()

class QueryRequest(BaseModel):
    collection: str
    query_type: str  # "find" or "aggregate"
    params: Dict[str, Any]

@router.post("/query")
async def playground_query(request: QueryRequest):
    """
    Executes a query for the MongoDB playground.
    """
    try:
        coll = getattr(db, request.collection)
        
        if request.query_type == "find":
            filter_query = request.params.get("filter", {})
            limit = request.params.get("limit", 10)
            sort = request.params.get("sort", None)
            
            cursor = coll.find(filter_query)
            if sort:
                # Expecting sort like {"field": 1}
                sort_list = [(k, v) for k, v in sort.items()]
                cursor = cursor.sort(sort_list)
            
            results = await cursor.limit(limit).to_list(length=limit)
            # Serialize ObjectIds
            for r in results:
                if "_id" in r:
                    r["_id"] = str(r["_id"])
            return {"results": results, "count": len(results)}
            
        elif request.query_type == "aggregate":
            pipeline = request.params.get("pipeline", [])
            results = await coll.aggregate(pipeline).to_list(length=100)
            for r in results:
                if "_id" in r:
                    r["_id"] = str(r["_id"])
            return {"results": results, "count": len(results)}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid query type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections")
async def get_collections():
    """
    Returns list of collections in the database.
    """
    try:
        # In motor, list_collection_names() is a coroutine on the database object
        # Note: 'db' in app.db is the Motor client[DB_NAME] or the AsyncMockDB
        if hasattr(db, "list_collection_names"):
            names = await db.list_collection_names()
        else:
            # Fallback for mock or specific wrapper issues
            names = ["payment_events", "validation_requests", "prompt_runs", "agents", "users"]
        return {"collections": names}
    except Exception as e:
        return {"collections": ["payment_events", "validation_requests", "prompt_runs", "agents", "users"], "error": str(e)}
