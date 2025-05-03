"""
Module containing the image generation agent.

To run it in the interactive CLI mode, run:
```bash
python -m image_generation.__init__
```
"""

from image_generation.agent import generate_images
import matplotlib.pyplot as plt
import asyncio
from PIL import Image
import io
import time

from image_generation.models import ImageGeneratorContext, ImageGenerationPrompt


async def _run_in_cli() -> None:
    what_to_draw = input("What do you want to draw? ")

    start_time = time.monotonic()
    image_bytes = await generate_images(
        ImageGeneratorContext(
            child_age=5,
            child_preferred_style="Cell-shaded comic",
            images_to_generate=[
                ImageGenerationPrompt(
                    base_images=[],
                    prompt=what_to_draw,
                ),
            ],
        ),
    )
    end_time = time.monotonic()
    generation_time = end_time - start_time
    print(f"Image(s) generated in {generation_time:.2f} seconds")

    for image in image_bytes:
        image = Image.open(io.BytesIO(image))
        plt.imshow(image)
        plt.show()


if __name__ == "__main__":
    try:
        asyncio.run(_run_in_cli())
    except KeyboardInterrupt:
        print("\nExiting...")
