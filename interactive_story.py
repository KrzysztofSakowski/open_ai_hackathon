import asyncio

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


async def run_interactive_story_agent(story_topic: str) -> None:
    story_input_so_far = [
        Message(
            role="user", content=[ResponseInputTextParam(text=f"Topic of the story: {story_topic}", type="input_text")]
        ),
    ]

    with trace(workflow_name="interactive_story_agent", group_id=story_topic):
        while True:
            story_decision = await Runner.run(
                interactive_story_agent,
                story_input_so_far,
            )
            final_output = story_decision.final_output
            print(final_output.scene_text)

            if final_output.decisions is None:
                print("\nThe story concludes here.")
                break

            print("\nNext steps:")
            print(f"1. {final_output.decisions.option1}")
            print(f"2. {final_output.decisions.option2}")

            user_choice = input("\nWhich path would you like to take (enter the text)? ")
            story_input_so_far = story_decision.to_input_list() + [
                Message(role="user", content=[ResponseInputTextParam(text=user_choice, type="input_text")])
            ]


if __name__ == "__main__":
    load_dotenv()
    selected_story_topic_topic = (
        input("What topic would you like the story to be about? (Leave blank to use predefined one): ")
        or "A brave little turtle who wants to explore the world."
    )
    try:
        asyncio.run(run_interactive_story_agent(selected_story_topic_topic))
    except KeyboardInterrupt:
        print("\nStory interrupted.")
