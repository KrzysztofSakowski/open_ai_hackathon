import asyncio
import base64
import io
import os
import tempfile
import uuid
import json

from fastapi import FastAPI, Form, HTTPException, Path, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import Address, PersonEntry, Knowledge, FinalOutput, InteractiveTurnOutput, ConvoInfo
from fastapi.staticfiles import StaticFiles

from settings import env_settings
from typing import Literal, Any


class MessageToUser(BaseModel):
    type: Literal["audio", "output"]


class AudioMessageToUser(MessageToUser):
    type: str = "audio"
    audio_message: str


class OutputMessageToUser(MessageToUser):
    type: str = "output"
    final_output: dict


class Conversation(BaseModel):
    messages_to_user: list[MessageToUser]
    messages_to_agent: list[str]
    outputs: list[FinalOutput] = []
    knowledge: Knowledge | None = None
    story_history: list[str] = []
    final_output: dict = {}


CONVO_DB: dict[str, Conversation] = {}
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
os.makedirs("static", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")


class StartBody(BaseModel):
    conversation_id: str | None = None


@app.post("/start")
async def start(body: StartBody):
    global CONVO_DB

    CONVO_ID = body.conversation_id or str(uuid.uuid4())
    outputs = []
    knowledge = None
    if CONVO_ID in CONVO_DB:
        outputs = CONVO_DB[CONVO_ID].outputs
        knowledge = CONVO_DB[CONVO_ID].knowledge
        del CONVO_DB[CONVO_ID]
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail="Conversation ID already exists",
        # )

    CONVO_DB[CONVO_ID] = Conversation(
        messages_to_user=[],
        messages_to_agent=[],
        outputs=outputs,
        knowledge=knowledge,
        final_output={},
    )

    from main_agent import main_agent

    print("Starting main agent")
    asyncio.create_task(main_agent(CONVO_ID))
    print("CONVO_ID: ", CONVO_ID)
    return {"conversation_id": CONVO_ID}


def add_to_output(convo_id: str, item_id: str, item: dict):
    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )
    print("Adding to output...")
    CONVO_DB[convo_id].final_output[item_id] = item
    return {"message": "Item added successfully"}


def post_message(convo_id: str, message: MessageToUser):
    if env_settings.run_in_cli:
        print("Posting message without voice...")
        print("CONVO_ID: ", convo_id)
        print("Message: ", message.model_dump())
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
        msg: MessageToUser = CONVO_DB[convo_id].messages_to_user.pop(0)

        if msg.type == "audio":
            try:
                # Create a bytes buffer to store the audio
                buffer = io.BytesIO()

                # Generate speech and stream it to the buffer
                with client.audio.speech.with_streaming_response.create(
                    model="gpt-4o-mini-tts",
                    voice="coral",
                    input=msg.audio_message,
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
                    "type": "audio",
                    "audio_base64": audio_base64,
                    "text": msg.audio_message,
                    "format": "mp3",  # OpenAI returns MP3 by default
                }
            except Exception as e:
                return None
        else:
            return {
                "type": "output",
                "text": msg.final_output,
                "format": "text",
            }
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


class InteractiveStoryRequest(BaseModel):
    choice: str | None = None


@app.post("/interactive_story/{convo_id}", response_model=InteractiveTurnOutput)
async def run_interactive_story_turn(convo_id: str, request: InteractiveStoryRequest) -> InteractiveTurnOutput:
    from tools.storytime_agent import interactive_story_illustrator_agent
    from models import InteractiveTurnOutput, ConvoInfo
    from agents import Runner

    global CONVO_DB
    if convo_id not in CONVO_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation ID not found",
        )

    conversation = CONVO_DB[convo_id]
    story_history = conversation.story_history
    knowledge = conversation.knowledge
    user_choice = request.choice

    if not user_choice and not story_history:
        # First turn, use the theme from knowledge as the initial topic
        if not knowledge or not knowledge.theme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start story: Theme not found in knowledge. Please onboard first.",
            )
        chosen_path = f"Topic: {knowledge.theme}"
    elif not user_choice and story_history:
        # Subsequent turn but no choice provided
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choice is required to continue the story.",
        )
    else:
        # Subsequent turn with a choice provided
        chosen_path = user_choice

    # Prepare input for the agent
    input_prompt = f"Story History: {'\n\n'.join(story_history)}\n\n" f"Chosen Path: {chosen_path}"

    print(f"Running interactive story agent for {convo_id} with input:\n{input_prompt}")

    # Run the agent
    try:
        agent_result = await Runner.run(
            interactive_story_illustrator_agent, input_prompt, context=ConvoInfo(convo_id=convo_id, existing_convo=True)
        )
    except Exception as e:
        print(f"Error running interactive_story_illustrator_agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent failed to generate story turn: {e}"
        )

    if not agent_result or not agent_result.final_output:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent did not produce a valid output for the story turn.",
        )

    # Parse the output
    turn_output = agent_result.final_output_as(InteractiveTurnOutput)

    # Update history
    conversation.story_history.append(turn_output.scene_text)
    add_to_output(convo_id, "story_turn", turn_output.model_dump())


if __name__ == "__main__":
    from models import Knowledge, InteractiveTurnOutput
    import asyncio
    import uuid

    async def main():
        # Simulate starting a conversation and getting initial knowledge
        convo_id = str(uuid.uuid4())
        theme = "a lost astronaut exploring an alien jungle"
        knowledge = Knowledge(theme=theme)
        CONVO_DB[convo_id] = Conversation(knowledge=knowledge)
        print(f"--- Starting Story Simulation (ID: {convo_id}) ---")
        print(f"Theme: {theme}\n")

        current_choice = None
        num_turns = 3

        for turn in range(num_turns):
            print(f"--- Turn {turn + 1} ---")
            request = InteractiveStoryRequest(choice=current_choice)
            try:
                await run_interactive_story_turn(convo_id, request)
            except HTTPException as e:
                print(f"API Error: {e.detail}")
                break
            except Exception as e:
                print(f"Unexpected Error: {e}")
                break

            # Retrieve the latest output from the conversation
            if CONVO_DB[convo_id].outputs:
                latest_output_dict = CONVO_DB[convo_id].outputs[-1]["item"]
                # Ensure it's the correct output type before parsing
                if "scene_text" in latest_output_dict:  # Basic check for story output
                    turn_output = InteractiveTurnOutput(**latest_output_dict)
                    print(f"Scene:\n{turn_output.scene_text}\n")
                    print(f"Options:")
                    print(f"1. {turn_output.option_1}")
                    print(f"2. {turn_output.option_2}\n")

                    # Simulate choosing the first option for the next turn
                    current_choice = turn_output.option_1
                else:
                    print("Latest output was not a story turn.")
                    break
            else:
                print("No output generated for this turn.")
                break

            # Prevent infinite loop if no choice is made (shouldn't happen with simulation)
            if not current_choice:
                print("Stopping simulation as no choice was made.")
                break

        print("--- Story Simulation Ended ---")

    asyncio.run(main())
