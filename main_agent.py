import asyncio
import json

from agents import Agent, Runner, WebSearchTool
from pydantic import BaseModel

from images import generate_image_from_storyboard
from tools.event_tool import EventModel, find_events_for_child
from tools.generate_lesson_tool import lesson_generator_agent
from tools.onboarding_agent import onboard_user, Knowledge
from tools.storyboard_agent import get_storyboard
from tools.storytime_agent import get_story, StoryContinuationOutput
from models import FinalOutput, ConvoInfo
from settings import env_settings
from api import wait_for_user_message


parent_assistant_agent = Agent[ConvoInfo](
    name="main_agent",
    instructions="""
    You are a helpful assistant that aids parents in organizing their children's evening activities. Your goal is to suggest activities, games, and educational content tailored to the child's age and interests while incorporating the latest trends in children's activities and education.

# Steps

- **Onboarding**: Use the onboarding tool to gather preferences and interests of both the child and the parent.
- **Research & Trend Analysis**: Search the web and research the latest information on child development and trends in children's activities and education.
- **Plan Generation**: Use the collected information to create a personalized evening plan.

# Perfect Plan Includes

1. **Age-Appropriate Activities**: A list of engaging activities suitable for the child's age.
2. **Educational Content**: Content relevant to the child's interests to foster learning.
3. **Fun Games**: Interactive games that ensure enjoyment.
4. **Additional Resources**: Resources for parents to further explore the child's interests.

# Tools & Execution

- **generate_lesson_tool**: Use this to create a lesson plan based on the user's input, to be included under "Lesson".
- **get_story**: Generate a short story tailored to the child's interests.
- **find_events_tool**: Use this to find relevant events for the child based on user inputs.
- **Reasoning**: Include detailed reasoning behind your suggestions in the final output.

# Output Format

- Provide a structured list of activities, educational content, games, and resources along with reasoning and a lesson plan.
- Include outputs from tools in their designated sections.

# Examples

(Not included in this prompt, but real examples should be comprehensive, clearly outlining a personalized plan based on specific user inputs.)

# Notes

Ensure all suggestions are coherent, detailed, and justified with reasoning. Emphasize personalization to suit the child's specific needs and interests.
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

    if env_settings.run_in_cli:
        return

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
    env_settings.load()  # Sanity check env

    from api import CONVO_DB, Conversation
    from tools.onboarding_agent import Knowledge, PersonEntry, Address

    CONVO_ID = "test_convo_id"
    CONVO_DB[CONVO_ID] = Conversation(
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
