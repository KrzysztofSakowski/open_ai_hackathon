"""
Module containing the image generation agent.

To run it in the interactive CLI mode, run:
```bash
python -m image_generation.__init__
```
"""

import base64
from pathlib import Path

from image_generation.agent import generate_images
import matplotlib.pyplot as plt
import asyncio
from PIL import Image
import io
import time


async def _run_in_cli() -> None:
    from image_generation.guardrails import inappropriate_image_output_guardrail
    from image_generation.models import ImageGeneratorContext, ImageGenerationPrompt

    what_to_draw = input("What do you want to draw? ")

    start_time = time.monotonic()
    image_bytes = await generate_images(
        context := ImageGeneratorContext(
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
        # Construct path relative to the current file (__init__.py)
        current_dir = Path(__file__).parent
        save_dir = current_dir / "examples"
        save_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        save_path = save_dir / f"{what_to_draw}.png"

        with open(save_path, "wb") as f:
            f.write(image)

        image_base64 = base64.b64encode(image).decode("utf-8")
        is_inappropriate = await inappropriate_image_output_guardrail(context, image_base64)
        print(f"Is the image inappropriate? {is_inappropriate}")

        image = Image.open(io.BytesIO(image))
        plt.imshow(image)
        plt.show()


if __name__ == "__main__":
    try:
        asyncio.run(_run_in_cli())
    except KeyboardInterrupt:
        print("\nExiting...")
