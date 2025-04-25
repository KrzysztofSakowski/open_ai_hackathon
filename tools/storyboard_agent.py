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
    trace,
)


class Scene(BaseModel):
    title: str
    narration: str
    prompt: str


class ScenesOutput(BaseModel):
    scene: list[Scene]


storyboard_assistant_agent = Agent(
    name="story_agent",
    instructions="Based on the user's story generate a list of scenes for the storyboard. Each scene should consist a title and a prompt for the image generation. Make sure to pick maximum 7 most important scenes, make sure to include setup and the final scene.",
    output_type=ScenesOutput,
)


class StoryboardOutput(BaseModel):
    images: list[str]


@function_tool
async def get_storyboard(story: str) -> StoryboardOutput:
    return await _get_storyboard(story)


async def _get_storyboard(theme: str) -> StoryboardOutput:
    input_prompt = f"The story is following: {theme}"

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
        images=[scene.prompt for scene in storyboard_result.final_output.scene]
    )


if __name__ == "__main__":
    asyncio.run(
        _get_storyboard("""
**Dino Adventures in Rainbow Valley**

In the heart of the magical Rainbow Valley, where lush landscapes glimmered and dinosaurs roamed with vibrant colors, lived Trixie, a curious young triceratops with an insatiable thirst for exploration.

One sunny morning by Crystal Creek, as the water shimmered with hues of the rainbow, Trixie stumbled upon an extraordinary find — a mysterious, sparkling egg. To her astonishment, the egg began to crack and out emerged a tiny, rainbow-feathered pterosaur named Flutter. Their eyes met, and a friendship blossomed instantly.

Eager to help Flutter find his family, Trixie and her newfound friend set off on an adventure. They traveled through lush forests where the leaves whispered tales of the past and crossed sparkling rivers that sang melodious tunes. 

Their quest soon led them to more companions: Sammy, a cheerful stegosaurus with a knack for storytelling, and Lila, a clever velociraptor with a lightning-fast mind. Together, they formed an inseparable team, each friend contributing their unique talents.

The journey wasn't without its challenges. At Windy Gorge, where fierce gusts threatened their progress, Lila devised a clever way to build a bridge using vines and branches. In the Mystical Maze, Sammy's keen sense of direction led them safely through its bewildering paths.

At last, their perseverance paid off. They reached the majestic Enchanted Cliffs, home to Flutter’s family. The reunion was filled with joy, laughter, and a celebration that reverberated through the valley, with music and dance that echoed under the bright stars.

Trixie realized the true meaning of friendship and courage, embracing the thrill of adventure. The group promised to reunite and explore even more wonders of Rainbow Valley.

As the vibrant sunset painted the sky in dazzling colors, the friends lay beneath the twinkling stars, dreaming together of the endless adventures yet to come.

""")
    )
