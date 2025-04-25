import asyncio
from settings import openai_client
from tools.event_tool import find_events_for_child

import asyncio

from pydantic import BaseModel
from tools.generate_lesson_tool import lesson_generator_agent
from tools.storytime_agent import get_story
from tools.onboarding_agent import onboard_user, Knowledge
from tools.event_tool import EventModel

from agents import (
    Agent,
    Runner,
    WebSearchTool,
)


class FinalOutput(BaseModel):
    story: str
    lesson: str
    reasoning: str
    plan_for_evening: str
    knowledge: Knowledge
    event: EventModel | None


parent_assistant_agent = Agent(
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
    Make sure to call get_story to generate a short story based on the user's input.
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
    final_plan = await Runner.run(
        parent_assistant_agent,
        "",
        context={"conversation_id": convo_id},
    )
    print("Final plan:")
    print("STORY")
    print(final_plan.final_output.story)
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
