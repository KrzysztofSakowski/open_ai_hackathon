CONVO_DB = {}
CONVO_ID = 0

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

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
async def get_state():
    return {}


@app.post("/message")
async def send_message():
    return {}
