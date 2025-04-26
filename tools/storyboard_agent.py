import asyncio

from agents import Agent, Runner, function_tool
from pydantic import BaseModel


class Scene(BaseModel):
    title: str
    narration: str
    prompt: str


class ScenesOutput(BaseModel):
    scene: list[Scene]
    main_character_description: str


storyboard_assistant_agent = Agent(
    name="story_agent",
    instructions="""You are a creative designer specializing in children's illustrated storybooks. Your task is to take a given story and prepare it for illustration.
First, provide a detailed visual description of the main character suitable for a children's book illustration.
Second, identify up to 7 key moments from the story (including the setup and the final scene) that would make compelling illustrations.
For each moment, create a scene consisting of:
1. A short, engaging title suitable for a page in a children's book.
2. A detailed prompt for an image generation model, describing the scene visually in a style appropriate for children (e.g., whimsical, colorful, simple).""",
    output_type=ScenesOutput,
)


class StoryboardOutput(BaseModel):
    images: list[str]
    main_character_description: str


@function_tool
async def get_storyboard(story: str) -> StoryboardOutput:
    return await _get_storyboard(story)


async def _get_storyboard(story: str) -> StoryboardOutput:
    input_prompt = f"""
The story is as follows:
{story}

Please analyze the story and identify up to 7 of its most impactful moments.
For each moment, create a scene with the following structure:
- A short, descriptive title for the scene.
- A detailed prompt suitable for an image generation model that captures the essence of the scene.
"""

    # Ensure the entire workflow is a single trace
    # 1. Generate an outline
    storyboard_result = await Runner.run(
        storyboard_assistant_agent,
        input_prompt,
    )
    print("Storyboard generated")
    for scene in storyboard_result.final_output.scene:
        print(f"Scene Title: {scene.title}")
        print(f"Scene Narration: {scene.narration}")
        print(f"Scene Prompt: {scene.prompt}")

    return StoryboardOutput(
        images=[scene.prompt for scene in storyboard_result.final_output.scene],
        main_character_description=storyboard_result.final_output.main_character_description,
    )


if __name__ == "__main__":
    asyncio.run(
        _get_storyboard(
            """
**Dino Adventures in Rainbow Valley**

In the heart of the magical Rainbow Valley, where lush landscapes glimmered and dinosaurs roamed with vibrant colors, lived Trixie, a curious young triceratops with an insatiable thirst for exploration.

One sunny morning by Crystal Creek, as the water shimmered with hues of the rainbow, Trixie stumbled upon an extraordinary find — a mysterious, sparkling egg. To her astonishment, the egg began to crack and out emerged a tiny, rainbow-feathered pterosaur named Flutter. Their eyes met, and a friendship blossomed instantly.

Eager to help Flutter find his family, Trixie and her newfound friend set off on an adventure. They traveled through lush forests where the leaves whispered tales of the past and crossed sparkling rivers that sang melodious tunes.

Their quest soon led them to more companions: Sammy, a cheerful stegosaurus with a knack for storytelling, and Lila, a clever velociraptor with a lightning-fast mind. Together, they formed an inseparable team, each friend contributing their unique talents.

The journey wasn't without its challenges. At Windy Gorge, where fierce gusts threatened their progress, Lila devised a clever way to build a bridge using vines and branches. In the Mystical Maze, Sammy's keen sense of direction led them safely through its bewildering paths.

At last, their perseverance paid off. They reached the majestic Enchanted Cliffs, home to Flutter’s family. The reunion was filled with joy, laughter, and a celebration that reverberated through the valley, with music and dance that echoed under the bright stars.

Trixie realized the true meaning of friendship and courage, embracing the thrill of adventure. The group promised to reunite and explore even more wonders of Rainbow Valley.

As the vibrant sunset painted the sky in dazzling colors, the friends lay beneath the twinkling stars, dreaming together of the endless adventures yet to come.

"""
        )
    )
