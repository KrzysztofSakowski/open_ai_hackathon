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
from models import StoryContinuationOutput, InteractiveTurnOutput


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
async def get_story(knowledge: Knowledge, theme: str) -> StoryOutput:
    return await _get_story(knowledge, theme)


async def _get_story(knowledge: Knowledge, theme: str) -> StoryOutput:
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

    return StoryOutput(
        story=story_result.final_output,
        theme=theme,
    )


story_outline_agent = Agent(
    name="story_outline_agent",
    instructions="Generate a very short children story outline based on the user's input.",
)

# --- Interactive Story Components ---
story_continuation_agent = Agent(
    name="story_continuation_agent",
    instructions="""
You are an interactive storyteller for children.
Given the story so far and the user's chosen path (or an initial topic), generate the next short scene (1-2 paragraphs) of the story.
Then, provide two distinct and engaging options for how the story could continue next.

Input will be structured as:
- Topic: [Initial topic if starting]
- Story History: [The story generated so far]
- Chosen Path: [The option chosen by the user in the previous step, or 'Start' if beginning]

Output should be the next scene and two new options.
Keep the tone light, engaging, and appropriate for children.
""",
    output_type=StoryContinuationOutput,
    input_guardrails=[violent_story_guardrail],  # Reuse the violence check
)

# --- New Interactive Story + Illustrator Agent ---

from tools.storyboard_agent import get_storyboard
from images import generate_image_from_storyboard

interactive_story_illustrator_agent = Agent(
    name="interactive_story_illustrator_agent",
    instructions="""
You are an interactive storyteller and illustrator for children.

Your goal is to perform ONE turn of an interactive story:
1. Generate the next story scene and two continuation options based on the provided story history and the user's chosen path (or initial topic). Use the 'story_continuation_agent' tool for this.
2. Generate a storyboard based ONLY on the *newly generated scene text*. Use the 'get_storyboard' tool.
3. Generate images based on the storyboard. Use the 'generate_image_from_storyboard' tool.
4. Return the newly generated scene text, the paths to the generated images, and the continuation options.

Input format expected:
- Story History: [Text of the story generated so far]
- Chosen Path: [The option chosen by the user in the previous step, or the initial 'Topic: <topic>' if starting]

Output format MUST be InteractiveTurnOutput.
Keep the tone light, engaging, and appropriate for children.
""",
    output_type=InteractiveTurnOutput,
    tools=[
        story_continuation_agent.as_tool(
            tool_name="story_continuation_agent",
            tool_description="Generates the next story scene and two options based on history and choice.",
        ),
        get_storyboard,
        generate_image_from_storyboard,
    ],
    input_guardrails=[violent_story_guardrail],
)


# --- End Interactive Story Components ---


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
