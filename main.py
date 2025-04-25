import asyncio
from settings import openai_client
from tools.event_tool import find_events_for_child


async def main() -> None:
    events = await find_events_for_child(child_age=7, location="Warsaw")
    print(events)


if __name__ == "__main__":
    asyncio.run(main())
