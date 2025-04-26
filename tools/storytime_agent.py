import asyncio

from pydantic import BaseModel

from agents import (
    Agent,
    Runner,
    function_tool,
    input_guardrail,
    RunContextWrapper,
    TResponseInputItem,
    GuardrailFunctionOutput,
)
from tools.onboarding_agent import Knowledge, PersonEntry, Address
from api import post_message
from models import ConvoInfo
from tools.storyboard_agent import _get_storyboard


class ViolentStoryOutput(BaseModel):
    reasoning: str
    is_violent_story: bool


guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking you to do generate a violent story.",
    output_type=ViolentStoryOutput,
)


@input_guardrail
async def violent_story_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """This is an input guardrail function, which happens to call an agent to check if the input
    is a violent story request.
    """
    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(ViolentStoryOutput)

    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=final_output.is_violent_story,
    )


story_agent = Agent(
    name="story_agent",
    instructions="Write a short story based on the given outline.",
    output_type=str,
    input_guardrails=[violent_story_guardrail],
)


storytime_agent = Agent(
    name="storytime_agent",
    instructions="""
    This agent is responsible for generating a children story based on the user's input.
    """,
)


class StoryOutput(BaseModel):
    story: str
    theme: str


@function_tool
async def get_story(wrapper: RunContextWrapper[ConvoInfo], knowledge: Knowledge, theme: str) -> StoryOutput:
    return await _get_story(wrapper, knowledge, theme)


async def _get_story(wrapper: RunContextWrapper[ConvoInfo], knowledge: Knowledge, theme: str) -> StoryOutput:
    input_prompt = f"""
    Here is some helpful data: {knowledge.model_dump_json()}.
    Please make sure that story incorporates that knowledge.

    Remember: Generate a story with the theme: {theme}.
"""

    # Ensure the entire workflow is a single trace
    # 1. Generate an outline
    outline_result = await Runner.run(
        story_outline_agent,
        input_prompt,
    )
    print("Outline generated")
    # 4. Write the story
    story_result = await Runner.run(
        story_agent,
        outline_result.final_output,
    )
    print(f"Story: {story_result.final_output}")

    storyboard_output = await _get_storyboard(wrapper, story_result.final_output)
    print("Storyboard generated: " + storyboard_output.model_dump_json())

    return StoryOutput(
        story=story_result.final_output,
        theme=theme,
    )


story_outline_agent = Agent(
    name="story_outline_agent",
    instructions="Generate a very short children story outline based on the user's input.",
)


if __name__ == "__main__":
    asyncio.run(
        _get_story(
            Knowledge(
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
            "A brave little mouse",
        ),
    )
