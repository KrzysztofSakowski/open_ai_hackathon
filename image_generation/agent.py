import base64

from image_generation.models import ImageGenerationPrompt, ImageGeneratorContext
from settings import openai_client
import asyncio


async def generate_images(context: ImageGeneratorContext) -> list[bytes]:
    """
    Generate images for a list of prompts.

    Generated images are tailored to the child's age and preferred style.
    """
    return await asyncio.gather(
        *(
            _generate_image(prompt, context.child_age, context.child_preferred_style)
            for prompt in context.images_to_generate
        )
    )


async def _generate_image(
    image_generation_prompt: ImageGenerationPrompt, child_age: int, child_preferred_style: str
) -> bytes:
    prompt = f"""
        Generate an image suitable for a {child_age}-year-old child.
        The image should depict: {image_generation_prompt.prompt}.
        Try to match the following style preference: {child_preferred_style}.
    """
    if not image_generation_prompt.base_images:
        result = await openai_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            quality="medium",
        )
    else:
        result = await openai_client.images.edit(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            quality="medium",
            image=image_generation_prompt.base_images,
        )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    return image_bytes
