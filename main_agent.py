import asyncio
import json

from agents import Agent, Runner, WebSearchTool
from pydantic import BaseModel

from images import generate_image_from_storyboard
from tools.event_tool import EventModel, find_events_for_child
from tools.generate_lesson_tool import lesson_generator_agent
from tools.onboarding_agent import ConvoInfo, Knowledge, onboard_user
from tools.storyboard_agent import get_storyboard
from tools.storytime_agent import get_story
from models import FinalOutput


parent_assistant_agent = Agent[ConvoInfo](
    name="main_agent",
    instructions="""
    You are a helpful assistant that helps parents organize their children's evening activities.
    You can suggest activities, games, and educational content based on the child's age and interests.
    You can also provide information about the latest trends in children's activities and education.
    You can search the web for the latest information on the topic, research on the children development, and the latest trends in children's activities.
    You can also provide information about the latest trends in children's activities and education.


    REMEMBER: You should first use onboarding tool to gather the preferences of the child and parent.
    Then, use the information to generate a personalized plan for the evening.

    Perfect plan should include:

    1. A list of activities that are age-appropriate and engaging.
    2. A list of educational content that is relevant to the child's interests.
    3. A list of games that are fun and interactive.
    4. A list of resources that the parent can use to learn more about the child's interests.

    Make sure to call generate_lesson_tool to generate a lesson plan based on the user's input, include full lesson plan after: "Lesson".
    Always call get_story to generate a short story based on the user's input.
    Make sure to call find_events_tool to find events for the child based on the user's input.
    Make sure to include the reasoning behind your suggestions.
    """,
    output_type=FinalOutput,
    input_guardrails=[],
    tools=[
        onboard_user,
        find_events_for_child,
        lesson_generator_agent.as_tool(
            tool_name="generate_lesson_tool",
            tool_description="Generate a lesson plan based on the user's input",
        ),
        WebSearchTool(),
        get_story,
    ],
)


async def main_agent(convo_id: str) -> None:
    from api import CONVO_DB

    final_plan = await Runner.run(
        parent_assistant_agent,
        "",
        context=ConvoInfo(convo_id=convo_id, existing_convo=convo_id in CONVO_DB),
    )
    print("Final plan:")
    print("STORY")
    print(final_plan.final_output.story)
    print("STORY IMAGE PATHS")
    print(final_plan.final_output.story_image_paths)
    print("LESSON")
    print(final_plan.final_output.lesson)
    print("REASONING")
    print(final_plan.final_output.reasoning)
    print("PLAN FOR EVENING")
    print(final_plan.final_output.plan_for_evening)
    print("EVENT")
    print(final_plan.final_output.event)
    print("KNOWLEDGE")
    print(final_plan.final_output.knowledge)
    print("END OF PLAN")

    from api import post_message, CONVO_DB
    from api import OutputMessageToUser

    final_output = {
        **CONVO_DB[convo_id].final_output,
        **final_plan.final_output.model_dump(),
    }
    print("Final output:", final_output)
    post_message(convo_id, OutputMessageToUser(final_output=final_output))
    CONVO_DB[convo_id].outputs.append(final_plan.final_output)

    print("Final output appended to CONVO_DB for convo_id:", convo_id)
    print("Main agent finished")


if __name__ == "__main__":
    from api import CONVO_DB, EntryModel
    from tools.onboarding_agent import Knowledge, PersonEntry, Address

    CONVO_ID = "test_convo_id"
    CONVO_DB[CONVO_ID] = EntryModel(
        messages_to_user=[],
        messages_to_agent=[],
        outputs=[],
        knowledge=Knowledge(
            address=Address(city="Warsaw", country="Poland"),
            parent=PersonEntry(
                name="John Doe",
                age=34,
                likes=["cheese", "running"],
                dislikes=["cats", "loud noises"],
            ),
            child=PersonEntry(
                name="Little Timmy",
                age=5,
                likes=["playing", "adventures"],
                dislikes=["bedtime", "vegetables"],
            ),
            theme="A brave little mouse",
        ),
        final_output={},
    )
    asyncio.run(main_agent(convo_id="test_convo_id"))
