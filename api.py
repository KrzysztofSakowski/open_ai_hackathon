import asyncio
import base64
import io
import os
import tempfile
import uuid

from fastapi import FastAPI, Form, HTTPException, Path, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from settings import env_settings


class EntryModel(BaseModel):
    messages_to_user: list[str]
    messages_to_agent: list[str]


CONVO_DB: dict[str, EntryModel] = {}
CONVO_ID = 0


# Initialize FastAPI app
app = FastAPI(
    title="My FastAPI Application",
    description="A sample FastAPI application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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

    from main_agent import main_agent

    print("Starting main agent")
    asyncio.create_task(main_agent(CONVO_ID))
    print("CONVO_ID: ", CONVO_ID)
    return {"conversation_id": CONVO_ID}


def post_message(convo_id: str, message: str):
    if env_settings.run_in_cli:
        print("Posting message without voice...")
        print("CONVO_ID: ", convo_id)
        print("Message: ", message)
        return
    print("Posting message...")
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )
    print("CONVO_ID: ", convo_id)
    CONVO_DB[convo_id].messages_to_user.append(message)
    return {"message": "Message added successfully"}


async def wait_for_user_message(convo_id: str):
    if env_settings.run_in_cli:
        # Run blocking input() in a separate thread
        user_input = await asyncio.to_thread(input, "Waiting for user message: ")
        return user_input
    print("Waiting for user message...")
    print("CONVO_ID: ", convo_id)
    global CONVO_DB
    if convo_id not in CONVO_DB:
        print("CONVO_ID not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )

    while True:
        print("Waiting for user message...")
        if CONVO_DB[convo_id].messages_to_agent:
            print("User message found")
            msg = CONVO_DB[convo_id].messages_to_agent.pop(0)
            print("User message: ", msg)
            return msg
        await asyncio.sleep(5)


@app.get("/state/{convo_id}")
async def get_state(convo_id: str = Path()):
    convo = CONVO_DB.get(convo_id)
    if convo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversation with ID {convo_id} not found",
        )
    if CONVO_DB[convo_id].messages_to_user:
        msg = CONVO_DB[convo_id].messages_to_user.pop(0)
        try:
            # Create a bytes buffer to store the audio
            buffer = io.BytesIO()

            # Generate speech and stream it to the buffer
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="coral",
                input=msg,
                instructions="Speak in a cheerful and positive tone.",
            ) as response:
                # Stream to our buffer instead of a file
                for chunk in response.iter_bytes():
                    buffer.write(chunk)

            # Reset buffer position to start
            buffer.seek(0)

            # Encode the entire audio buffer to base64
            audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Return the base64-encoded audio
            return {
                "audio_base64": audio_base64,
                "text": msg,
                "format": "mp3",  # OpenAI returns MP3 by default
            }

        except Exception as e:
            return None

    return None


from openai import OpenAI

client = OpenAI()


@app.post("/message/audio/{convo_id}")
async def send_message(convo_id: str = Path(), audio: UploadFile = Form()):
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
        # Write the uploaded file content to the temporary file
        content = await audio.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Open the temporary file and send to OpenAI for transcription
        with open(temp_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=file)

        print(transcription.text)
        # Return the transcription result
        CONVO_DB[convo_id].messages_to_agent.append(transcription.text)
        return {"transcription": transcription.text}

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
