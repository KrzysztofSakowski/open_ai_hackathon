import asyncio

from agents import Agent, Runner, function_tool, RunContextWrapper
from pydantic import BaseModel
from models import ConvoInfo


class Scene(BaseModel):
    title: str
    narration: str
    prompt: str


class ScenesOutput(BaseModel):
    scene: list[Scene]
    main_character_description: str


storyboard_assistant_agent = Agent(
    name="story_agent",
    instructions="""
    Write a captivating short story based on the given outline. Ensure that the narrative follows the structure outlined, incorporating the characters, setting, and key events provided.

# Steps

1. **Understand the Outline**: Carefully read the given outline, identifying the main plot points, characters, setting, and any specific themes or tones required.
2. **Develop Characters**: Flesh out the characters, giving them distinct voices and traits that contribute to the plot development.
3. **Establish Setting**: Clearly describe the setting, utilizing sensory details to create an immersive environment.
4. **Build the Narrative**: Follow the outline to construct the story, weaving together the characters, setting, and events in a coherent and engaging way.
5. **Resolve the Plot**: Ensure the story reaches a satisfying conclusion that aligns with the initial outline.

# Output Format

Write a short story of approximately 500-1000 words. The story should be in prose form, with paragraphs structured to reflect logical breaks in action or narrative development.

# Examples

Example Outline:
- **Characters**: Alex (a young scientist), Mia (Alex's best friend)
- **Setting**: A futuristic cityscape
- **Plot Points**: Alex discovers a method for time travel but needs Mia's help. They test the method and find themselves in a past era, learning key lessons before returning.
- **Themes**: Friendship, curiosity, and the consequence of actions

**Short Story Example Start**:

In the dazzling glow of the neon-lit metropolis, Alex wandered through the labyrinthine alleys of the city. A young scientist with an insatiable thirst for discovery, Alex rarely ventured beyond their lab except to see Mia. Today was different. Today, Alex had stumbled upon something extraordinary—a formula scribbled hastily on the whiteboard held the secret to traversing time itself.

(Continue the story based on the outline, ensuring it meets the required word count and contains a coherent narrative with character development, setting description, plot progression, and conclusion.)

# Notes

- Pay special attention to how the theme is integrated into the narrative.
- Ensure consistency in tone and style as indicated by the outline.
- Be creative while adhering to the given structure and elements.
    """,
    output_type=ScenesOutput,
)


class StoryboardOutput(BaseModel):
    images: list[str]
    narration: list[str]
    main_character_description: str


@function_tool
async def get_storyboard(wrapper: RunContextWrapper[ConvoInfo], story: str) -> StoryboardOutput:
    return await _get_storyboard(wrapper, story)


async def _get_storyboard(wrapper: RunContextWrapper[ConvoInfo], story: str) -> StoryboardOutput:
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

    output = StoryboardOutput(
        images=[scene.prompt for scene in storyboard_result.final_output.scene],
        narration=[scene.narration for scene in storyboard_result.final_output.scene],
        main_character_description=storyboard_result.final_output.main_character_description,
    )
    from api import add_to_output

    add_to_output(
        wrapper.context.convo_id,
        "storyboard",
        output.model_dump(),
    )
    return output


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
