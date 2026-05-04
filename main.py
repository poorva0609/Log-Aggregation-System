import os
from fastapi import FastAPI, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")


client = AsyncIOMotorClient(MONGO_URI)
db = client[os.getenv("DB_NAME")]
collection = db["logs"]

class Log(BaseModel):
    level: str
    message: str
    service: Optional[str] = "default"
    timestamp: Optional[datetime] = datetime.utcnow()


@app.post("/logs/bulk")
async def insert_logs(logs: List[Log]):
    docs = [log.dict() for log in logs]

    if not docs:
        return {"inserted": 0}

    result = await collection.insert_many(docs)

    return {
        "inserted": len(result.inserted_ids)
    }


@app.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    query = {}

    if level:
        query["level"] = level
    if service:
        query["service"] = service

    cursor = (
        collection.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)

    return results
