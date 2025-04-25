import asyncio
import datetime

from agents import function_tool
from pydantic import BaseModel

from settings import openai_client


class EventModel(BaseModel):
    name: str
    description: str
    estimated_cost: str | float | None = None
    url: str | None = None
    book_ticket_url: str | None = None
    address: str | None = None


@function_tool
async def find_events_for_child(child_age: int, location: str) -> EventModel | None:
    """
    Searches for events happening tomorrow suitable for a child of a given age,
    optionally filtered by location, using OpenAI's web search tool.
    """
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"What events are happening on {tomorrow} in {location} that are suitable for a {child_age}-year-old child?"

    try:
        search_results = await openai_client.responses.parse(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=query,
            text_format=EventModel,
        )
        return search_results.output_parsed

    except Exception as e:
        print(f"An error occurred during the search: {e}")
        return None


if __name__ == "__main__":
    # Run it with python -m tools.event_tool
    result = asyncio.run(find_events_for_child())
    print(result)
