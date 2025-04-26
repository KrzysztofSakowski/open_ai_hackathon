import os
import tempfile
from main_agent import main_agent
import asyncio
import uuid
from fastapi import FastAPI, HTTPException, Depends, status, Query, Form, UploadFile
from pydantic import BaseModel

CONVO_DB = {}
CONVO_ID = 0

import uuid
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel


class EntryModel(BaseModel):
    messages_to_user: list[str]
    messages_to_agent: list[str]


CONVO_DB: dict[str, EntryModel] = {}
# Initialize FastAPI app
app = FastAPI(
    title="My FastAPI Application",
    description="A sample FastAPI application",
    version="0.1.0",
)


@app.post("/start")
async def start():
    global CONVO_DB

    CONVO_ID = str(uuid.uuid4())
    if CONVO_ID in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation ID already exists",
        )

    CONVO_DB[CONVO_ID] = EntryModel(messages_to_user=[], messages_to_agent=[])

    asyncio.create_task(main_agent(CONVO_ID))

    return {"conversation_id": CONVO_ID}


def post_message(convo_id: str, message: str):
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )

    CONVO_DB[convo_id].messages_to_user.append(message)
    return {"message": "Message added successfully"}


async def wait_for_user_message(convo_id: str):
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )

    while True:
        if CONVO_DB[convo_id].messages_to_agent:
            return CONVO_DB[convo_id].messages_to_agent.pop(0)
        await asyncio.sleep(5)


@app.get("/state")
async def get_state(convo_id: uuid.UUID) -> str:
    convo = CONVO_DB.get(str(convo_id))
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation with ID {convo_id} not found",
        )
    if CONVO_DB[convo_id].messages_to_user:
        return CONVO_DB[convo_id].messages_to_user.pop(0)
    return None


from openai import OpenAI

client = OpenAI()


@app.post("/message/audio/{convo_id}")
async def send_message(convo_id: str = Query(), audio: UploadFile = Form()):
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        # Write the uploaded file content to the temporary file
        content = await audio.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Open the temporary file and send to OpenAI for transcription
        with open(temp_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe", file=file
            )

        # Return the transcription result
        CONVO_DB[convo_id].messages_to_user.append(transcription.text)
        return {"transcription": transcription.text}

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
    return {"message": "Message sent successfully"}
