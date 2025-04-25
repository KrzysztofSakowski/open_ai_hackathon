CONVO_DB = {}
CONVO_ID = 0

from typing import List, Optional
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="My FastAPI Application",
    description="A sample FastAPI application",
    version="0.1.0",
)


@app.post("/start")
async def start():
    return {}


@app.get("/state")
async def get_state(convo_id: uuid4) -> str:
    convo = CONVO_DB.get(str(convo_id))
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Conversation with ID {convo_id} not found"
        )
    return convo.from_system_to_user


@app.post("/message")
async def send_message():
    return {}
