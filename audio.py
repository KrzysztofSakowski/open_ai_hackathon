import asyncio
import base64
import uuid
from pathlib import Path

from openai import AsyncOpenAI

from tools.storyboard_agent import StoryboardOutput, _get_storyboard


async def generate_audio(client: AsyncOpenAI, prompt: str, output_path) -> None:
    async with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=prompt,
        instructions="Speak in a cheerful and positive tone.",
    ) as response:
        await response.stream_to_file(output_path)


async def generate_audio_from_storyboard(client: AsyncOpenAI, story_board: StoryboardOutput) -> None:
    """Generate audio from the storyboard output."""
    output_dir = Path("static/sample_audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with asyncio.TaskGroup() as tg:
        [
            tg.create_task(
                generate_audio(
                    client,
                    prompt=scene,
                    output_path=output_dir / f"audio_{i}.mp3",
                )
            )
            for i, scene in enumerate(story_board.narration)
        ]

    return [str(output_dir / f"audio_{i}.mp3") for i, scene in enumerate(story_board.narration)]


async def test_1():
    client = AsyncOpenAI()
    storyboard_output = await _get_storyboard(
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
    await generate_audio_from_storyboard(client, storyboard_output)


if __name__ == "__main__":
    asyncio.run(test_1())

    # main_character_description = "Create a little girl in the galaxy, she is the main character of the story. She is wearing a pink dress and has long brown hair. She is smiling and looking at the stars."
    # fairy_tale_description = "A little girl from the reference image meets a new friend from another galaxy. She remains the same but in a different pose."

    # # Generate the first image based on the main character description
    # image_response = generate_image(main_character_description, output_path="sample_images/img_0.png")
    # image_path = "sample_images/img_0.png"
    # image_response = generate_image_from_img(fairy_tale_description, image_path, output_path="sample_images/img_1.png")
