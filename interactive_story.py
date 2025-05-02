import asyncio
from typing import AsyncGenerator

from agents import Agent, Runner, trace
from dotenv import load_dotenv
from openai.types.responses import ResponseInputTextParam
from openai.types.responses.response_input_item_param import Message
from pydantic import BaseModel


class InteractiveTurnDecisions(BaseModel):
    """
    User's choice for the next turn of the interactive story.
    """

    option1: str
    option2: str


class InteractiveTurnOutput(BaseModel):
    """
    Output for a single turn of the interactive story.

    Contains the scene text and the possible choices for the next turn.
    Decisions are optional, and lack of them denotes the end of the story.
    """

    scene_text: str
    decisions: InteractiveTurnDecisions | None


interactive_story_agent = Agent(
    name="interactive_story_agent",
    instructions="""
You are an interactive storyteller for children.
Given the story so far and the user's chosen path (or an initial topic), generate the next short scene (1-2 paragraphs) of the story.
Then, provide two distinct and engaging options for how the story could continue next.

Output should be the next scene and two new options.
Keep the tone light, engaging, and appropriate for children.
""",
    output_type=InteractiveTurnOutput,
    # input_guardrails=[violent_story_guardrail],  # Reuse the violence check
)


async def run_interactive_story_agent(
    story_topic: str,
) -> AsyncGenerator[InteractiveTurnOutput, str]:
    """Runs the interactive story agent, yielding each turn's output and accepting the user's choice."""
    story_input_so_far = [
        Message(
            role="user", content=[ResponseInputTextParam(text=f"Topic of the story: {story_topic}", type="input_text")]
        ),
    ]

    user_choice = ""  # Initialize, will be replaced by yield

    while True:
        story_decision = await Runner.run(
            interactive_story_agent,
            story_input_so_far,
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


async def main():
    load_dotenv()
    selected_story_topic = (
        input("What topic would you like the story to be about? (Leave blank for predefined): ")
        or "A brave little turtle who wants to explore the world."
    )

    story_generator = run_interactive_story_agent(selected_story_topic)
    user_choice: str | None = None  # Start with None for the first asend

    try:
        async with trace(workflow_name="interactive_story_cli", group_id=selected_story_topic):
            while True:
                current_turn = await story_generator.asend(user_choice)  # type: ignore

                print("\n--------------------\n")
                print(current_turn.scene_text)

                if current_turn.decisions is None:
                    print("\nThe story concludes here.")
                    break

                print("\nNext steps:")
                print(f"1. {current_turn.decisions.option1}")
                print(f"2. {current_turn.decisions.option2}")

                user_choice = input("\nWhich path would you like to take (enter the text)? ")

    except StopAsyncIteration:
        print("\nStory generator finished.")
    except KeyboardInterrupt:
        print("\nStory interrupted.")
    finally:
        # Ensure the generator is closed properly
        await story_generator.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Already handled in main, but catch here too just in case
        print("\nExiting.")
