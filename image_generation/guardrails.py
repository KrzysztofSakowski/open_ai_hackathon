"""
Guardrail implementations for the image generation agent.
"""

import asyncio
from typing import Coroutine, Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    output_guardrail,
)
from pydantic import BaseModel

from image_generation.models import ImageGenerationOutput, ImageGeneratorContext


class ImageAppropriatenessOutput(BaseModel):
    """Output model for the image appropriateness check."""

    is_inappropriate: bool
    reasoning: str
    details: dict[str, Any] | None = None


async def _check_image_appropriateness(
    image_bytes: bytes, child_age: int, ctx: RunContextWrapper[ImageGeneratorContext | None]
) -> ImageAppropriatenessOutput:
    """
    Checks a single image for appropriateness using a vision model.

    Args:
        image_bytes: The image data as bytes.
        child_age: The target child age for appropriateness check.
        ctx: The run context, potentially containing API clients or configurations.

    Returns:
        An ImageAppropriatenessOutput object indicating if the image is inappropriate and why.

    NOTE: Replace this function's body with the actual call to your vision model API
          (e.g., OpenAI Vision, Google Cloud Vision Safety Detection, etc.).
          You will need to format the request according to the specific API requirements,
          passing the image bytes and instructions to evaluate appropriateness for the given child_age.
    """
    print(f"Checking image appropriateness for age {child_age}...")
    await asyncio.sleep(0.1)
    is_inappropriate = False
    reasoning = "Image appears appropriate (dummy check)."
    if len(image_bytes) < 1000:
        is_inappropriate = False
        reasoning = "Image size is very small, potentially indicating an issue (dummy check)."
    return ImageAppropriatenessOutput(is_inappropriate=is_inappropriate, reasoning=reasoning)


@output_guardrail
async def inappropriate_image_output_guardrail(
    ctx: RunContextWrapper[ImageGeneratorContext | None], agent: Agent, output_data: ImageGenerationOutput
) -> GuardrailFunctionOutput:
    """
    Checks agent-generated images for content inappropriate for the specified child age.

    Triggers if *any* image in the output list is deemed inappropriate by the
    _check_image_appropriateness helper function (which should wrap a vision model).
    """
    if not ctx.context:
        return GuardrailFunctionOutput(
            tripwire_triggered=False,
            output_info={"warning": "Context missing, cannot perform age-appropriateness check."},
        )

    if not output_data.images:
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=None)

    child_age = ctx.context.child_age
    all_checks_results: list[ImageAppropriatenessOutput] = []
    tripwire_triggered = False
    final_reasoning = "All generated images appear appropriate."

    check_tasks: list[Coroutine[Any, Any, ImageAppropriatenessOutput]] = []
    for image_bytes in output_data.images:
        check_tasks.append(_check_image_appropriateness(image_bytes, child_age, ctx))

    results = await asyncio.gather(*check_tasks)

    for result in results:
        all_checks_results.append(result)
        if result.is_inappropriate:
            tripwire_triggered = True
            final_reasoning = f"Inappropriate content detected: {result.reasoning}"
            break

    return GuardrailFunctionOutput(
        tripwire_triggered=tripwire_triggered,
        output_info={
            "appropriateness_checks": [r.model_dump() for r in all_checks_results],
            "summary": final_reasoning,
        },
    )
