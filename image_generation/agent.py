from agents import Agent, Runner

from image_generation.guardrails import inappropriate_image_output_guardrail
from image_generation.models import ImageGenerationOutput, ImageGeneratorContext
from image_generation.tools import generate_images_tool

image_generation_agent = Agent(
    name="image_generation_agent",
    instructions="""
    You are an AI assistant specialized in generating images for children based on provided prompts and context.
    Your task is to generate one image for each prompt specified in the 'images_to_generate' list within the run context.

    Context includes:
    - child_age: The target age for the images.
    - child_preferred_style: The preferred artistic style.
    - images_to_generate: A list of objects, each containing a 'prompt' string and potentially 'base_images' (list of bytes).

    Process:
    1. Iterate through each object in the 'images_to_generate' list from the context.
    2. For *each* object, call the 'generate_image' tool.
    3. Pass the following arguments to the 'generate_image' tool for each call:
        - image_generation_prompt: The current object from the 'images_to_generate' list.
        - child_age: The value from the context.
        - child_preferred_style: The value from the context.
    4. Collect the resulting image bytes from *all* successful tool calls.
    5. Structure the final output as an 'ImageGenerationOutput' object, placing the collected list of image bytes into its 'images' field.
    """,
    output_type=ImageGenerationOutput,
    tools=[generate_images_tool],
    output_guardrails=[
        inappropriate_image_output_guardrail,
    ],
)


async def run_image_generation(context: ImageGeneratorContext) -> ImageGenerationOutput:
    response = await Runner.run(
        image_generation_agent,
        context.images_to_generate,  # TODO: fix typing
        context=context,
    )
    return response.final_output
