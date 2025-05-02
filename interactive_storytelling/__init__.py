"""
Module containing the interactive story generator.

To run it in the interactive CLI mode, run:

```bash
python -m interactive_storytelling
```
"""

import asyncio

from agents import trace
from dotenv import load_dotenv

from interactive_storytelling.agent import run_interactive_story
from interactive_storytelling.models import StorytellerContext


async def _run_in_cli():
    load_dotenv()
    selected_story_topic = (
        input("What topic would you like the story to be about? (Leave blank for predefined): ")
        or "A brave little turtle who wants to explore the world."
    )

    story_generator = run_interactive_story(
        StorytellerContext(
            main_topic=selected_story_topic,
            main_moral="You should always trust your instincts",
            main_character="Nana, the Shiba dog",
            language="Polish",
            age=5,
        )
    )
    user_choice: str | None = None  # Start with None for the first asend

    try:
        with trace(workflow_name="interactive_story_cli", group_id=selected_story_topic):
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
        # Check if the generator has an aclose method before calling
        if hasattr(story_generator, "aclose"):
            await story_generator.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(_run_in_cli())
    except KeyboardInterrupt:
        # Already handled in main, but catch here too just in case
        print("\nExiting.")
