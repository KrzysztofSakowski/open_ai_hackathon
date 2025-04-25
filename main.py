import asyncio
from settings import openai_client

import asyncio

from pydantic import BaseModel
from tools.generate_lesson_tool import lesson_generator_agent
from tools.storytime_agent import get_story


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


parent_assistant_agent = Agent(
    name="main_agent",
    instructions="""
    You are a helpful assistant that helps parents organize their children's evening activities.
    You can suggest activities, games, and educational content based on the child's age and interests.
    You can also provide information about the latest trends in children's activities and education.
    You can search the web for the latest information on the topic, research on the children development, and the latest trends in children's activities.
    You can also provide information about the latest trends in children's activities and education.

    First, use the tool to gather the preferences of the child and parent.
    Then, use the information to generate a personalized plan for the evening.

    Perfect plan should include:

    1. A list of activities that are age-appropriate and engaging.
    2. A list of educational content that is relevant to the child's interests.
    3. A list of games that are fun and interactive.
    4. A list of resources that the parent can use to learn more about the child's interests.

    Make sure to call generate_lesson_tool to generate a lesson plan based on the user's input, include full lesson plan after: "Lesson".
    Make sure to call get_story to generate a short story based on the user's input.
    """,
    output_type=FinalOutput,
    input_guardrails=[],
    tools=[
        lesson_generator_agent.as_tool(
            tool_name="generate_lesson_tool",
            tool_description="Generate a lesson plan based on the user's input",
        ),
        WebSearchTool(),
        get_story,
    ],
)


async def main() -> None:
    final_plan = await Runner.run(
        parent_assistant_agent,
        "Child is 5 years old, and the theme is dinosaurs.",
        context=None,
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
    print("END OF PLAN")


if __name__ == "__main__":
    asyncio.run(main())
