import asyncio

import uvicorn

from main_agent import main_agent
from settings import RUN_WITHOUT_VOICE

if __name__ == "__main__":
    if not RUN_WITHOUT_VOICE:
        uvicorn.run("api:app", host="localhost", port=8000, reload=True)
    else:
        asyncio.run(main_agent(convo_id="test_convo_id"))
