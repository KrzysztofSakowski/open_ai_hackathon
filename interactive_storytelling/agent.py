"""
Interactive story generator.

This module implements an interactive story generator using the OpenAI API.
It allows users to engage in an interactive storytelling experience where they can choose different paths to continue the story.
"""

from typing import AsyncGenerator

from agents import Agent, Runner
from openai.types.responses import ResponseInputTextParam
from openai.types.responses.response_input_item_param import Message

from interactive_storytelling.models import (
    InteractiveTurnOutput,
    StorytellerContext,
)

# Import the new guardrail functions
from interactive_storytelling.guardrails import (
    prompt_hijack_guardrail,
    violent_story_input_guardrail,
    violent_story_output_guardrail,
    obscene_language_input_guardrail,
    obscene_language_output_guardrail,
    age_appropriateness_guardrail,
)

# --- Agent Definition ---
interactive_story_agent = Agent(
    name="interactive_story_agent",
    instructions="""
You are an interactive storyteller for children.

Given the story so far and the user's chosen path (or an initial story context), generate the next short scene (1-2 paragraphs) of the story.
Then, provide two distinct and engaging options for how the story could continue next.

Output should be the next scene and two new options.
Keep the tone light, engaging, and appropriate for children of age provided in the context.
""",
    output_type=InteractiveTurnOutput,
    input_guardrails=[
        prompt_hijack_guardrail,
        violent_story_input_guardrail,
        obscene_language_input_guardrail,
    ],
    output_guardrails=[
        age_appropriateness_guardrail,
        violent_story_output_guardrail,
        obscene_language_output_guardrail,
    ],
)


async def run_interactive_story(
    story_context: StorytellerContext,
) -> AsyncGenerator[InteractiveTurnOutput, str]:
    """Runs the interactive story agent, yielding each turn's output and accepting the user's choice."""
    story_input_so_far = [
        Message(
            role="system",
            content=[ResponseInputTextParam(text=story_context.get_prompt_content(), type="input_text")],
        ),
    ]

    while True:
        story_decision = await Runner.run(
            interactive_story_agent,
            story_input_so_far,
            context=story_context,
        )
        final_output = story_decision.final_output

        if final_output.decisions is None:
            yield final_output  # Yield the final scene without decisions
            break  # Story ends

        # Yield the current scene and decisions, wait for user choice
        user_choice = yield final_output

        # Prepare input (context) for the next turn
        story_input_so_far = story_decision.to_input_list() + [
            Message(role="user", content=[ResponseInputTextParam(text=user_choice, type="input_text")])
        ]
