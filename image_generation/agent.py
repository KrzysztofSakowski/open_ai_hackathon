import base64

from settings import openai_client
import asyncio


async def generate_images_for_prompts(prompts: list[str]) -> list[bytes]:
    """
    Generate images for a list of prompts.
    """
    return await asyncio.gather(*[_generate_image(prompt) for prompt in prompts])


async def _generate_image(prompt: str) -> bytes:
    result = await openai_client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        quality="medium",
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    return image_bytes
