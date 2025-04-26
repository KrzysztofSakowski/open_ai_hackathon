import asyncio
import datetime

from agents import function_tool
from pydantic import BaseModel

from settings import openai_client
from models import Knowledge, EventModel


@function_tool
async def find_events_for_child(knowledge: Knowledge) -> EventModel | None:
    """
    Searches for events happening tomorrow suitable for a child of a given age,
    optionally filtered by location, using OpenAI's web search tool, considering interests and dislikes.
    """
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    # Construct the detailed query based on knowledge
    base_query = f"What events are happening on {tomorrow} in {knowledge.address} suitable for a {knowledge.child.age}-year-old child?"

    # Collect likes and dislikes safely, handling potential None values and empty lists
    child_likes = knowledge.child.likes if knowledge.child and knowledge.child.likes else []
    parent_likes = knowledge.parent.likes if knowledge.parent and knowledge.parent.likes else []
    all_likes = list(set(child_likes + parent_likes))  # Use set to remove duplicates

    child_dislikes = knowledge.child.dislikes if knowledge.child and knowledge.child.dislikes else []
    parent_dislikes = knowledge.parent.dislikes if knowledge.parent and knowledge.parent.dislikes else []
    all_dislikes = list(set(child_dislikes + parent_dislikes))  # Use set to remove duplicates

    # Append interests to query if they exist
    if all_likes:
        likes_str = ", ".join(all_likes)
        base_query += f" The child and parents are interested in topics like: {likes_str}."

    # Append dislikes to query if they exist
    if all_dislikes:
        dislikes_str = ", ".join(all_dislikes)
        base_query += f" Please avoid events related to topics like: {dislikes_str}."

    query = base_query  # Final query string

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
