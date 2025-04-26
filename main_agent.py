import asyncio

from agents import Agent, Runner, WebSearchTool
from pydantic import BaseModel

from images import generate_image_from_storyboard
from tools.event_tool import EventModel, find_events_for_child
from tools.generate_lesson_tool import lesson_generator_agent
from tools.onboarding_agent import ConvoInfo, Knowledge, onboard_user
from tools.storyboard_agent import get_storyboard
from tools.storytime_agent import get_story, story_continuation_agent, StoryContinuationOutput
from models import FinalOutput
from settings import env_settings
from api import wait_for_user_message


parent_assistant_agent = Agent[ConvoInfo](
    name="main_agent",
    instructions="""
    You are a helpful assistant that helps parents organize their children's evening activities.
    You can suggest activities, games, and educational content based on the child's age and interests.
    You can also provide information about the latest trends in children's activities and education.
    You can search the web for the latest information on the topic, research on the children development, and the latest trends in children's activities.
    You can also provide information about the latest trends in children's activities and education.

    AVAILABLE TOOLS:
    - `onboard_user`: Use this FIRST to gather preferences of the child and parent.
    - `find_events_for_child`: Find local events.
    - `generate_lesson_tool`: Generate a lesson plan.
    - `WebSearchTool`: Search the web for information.
    - `get_story`: Generate a complete short story based on a theme.
    - `get_storyboard`: Generate a storyboard from a story.
    - `generate_image_from_storyboard`: Generate images from a storyboard.
    - `interactive_story_tool`: Generate the *next step* of an interactive story.

    WORKFLOW:
    1. Use `onboard_user` if you don't have user/child info (check context).
    2. Address the user's request using the available tools.
    3. Generate a personalized plan for the evening if appropriate.

    INTERACTIVE STORY GENERATION:
    - If the user asks for an *interactive* story, use the `interactive_story_tool` ONCE to generate the *first scene* and two continuation options based on the user's topic.
    - Your output (in the FinalOutput model) should clearly state that this is the beginning of an interactive story, include the first scene and the two options. The interactive turns will be handled subsequently.
    - To use `interactive_story_tool`, provide the initial topic and set 'Chosen Path' to 'Start'.
    - DO NOT call `interactive_story_tool` multiple times in one run.

    REGULAR STORY GENERATION:
    - If the user asks for a regular, non-interactive story, use the `get_story` tool.
    - After the story is generated, use the `get_storyboard` tool to generate a storyboard.
    - Use the `generate_image_from_storyboard` tool to generate images from the storyboard.

    FINAL OUTPUT:
    - Populate the `FinalOutput` model with the results of the tools you used (story, lesson, event, plan, etc.).
    - If starting an interactive story, populate the relevant fields in `FinalOutput`.
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
        get_storyboard,
        generate_image_from_storyboard,
        story_continuation_agent.as_tool(
            tool_name="interactive_story_tool",
            tool_description="Generates the next scene and two continuation options for an interactive story based on the story history and chosen path/topic.",
        ),
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
    print("INTERACTIVE")
    print(final_plan.final_output.interactive_story_start)
    if final_plan.final_output.interactive_story_start:
        print("INTERACTIVE STORY START")
        print(final_plan.final_output.interactive_story_start)
        user_response = await wait_for_user_message(convo_id)
        # Pass the response back to the parent assistant agent
        response = await Runner.run(
            parent_assistant_agent,
            user_response,
            context=ConvoInfo(convo_id=convo_id, existing_convo=convo_id in CONVO_DB),
        )
        print("Interactive story response:")
        print(response.final_output)
    print("END OF PLAN")

    if env_settings.run_in_cli:
        return

    from api import post_message, CONVO_DB
    from api import OutputMessageToUser

    post_message(convo_id, OutputMessageToUser(final_output=final_plan.final_output))
    CONVO_DB[convo_id].outputs.append(final_plan.final_output)

    print("Final output appended to CONVO_DB for convo_id:", convo_id)
    print("Main agent finished")


if __name__ == "__main__":
    env_settings.load()  # Sanity check env
    asyncio.run(main_agent(convo_id="test_convo_id"))
