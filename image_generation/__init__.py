"""
Module containing the image generation agent.

To run it in the interactive CLI mode, run:
```bash
python -m image_generation.__init__
```
"""

from image_generation.agent import generate_images_for_prompts
import matplotlib.pyplot as plt
import asyncio
from PIL import Image
import io
import time

if __name__ == "__main__":
    what_to_draw = input("What do you want to draw? ")

    start_time = time.monotonic()
    image_bytes = asyncio.run(generate_images_for_prompts([what_to_draw]))
    end_time = time.monotonic()
    generation_time = end_time - start_time
    print(f"Image(s) generated in {generation_time:.2f} seconds")

    for image in image_bytes:
        image = Image.open(io.BytesIO(image))
        plt.imshow(image)
        plt.show()
