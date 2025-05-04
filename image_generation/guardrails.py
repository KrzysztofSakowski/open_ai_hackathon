import json

from image_generation.models import InappropriateImageOutput, ImageGeneratorContext
from settings import openai_client


async def inappropriate_image_output_guardrail(
    context: ImageGeneratorContext, image_base64: str
) -> InappropriateImageOutput:
    """
    This guardrail checks if the image contains obscene or inappropriate content.

    It does not only look for explicit or obscene content, but also for content that is not appropriate for children
    at the given age. For example a "duck with a cigar" would be inappropriate for a 5-year-old child, because it promotes
    smoking (unhealthy habit).
    """
    response = await openai_client.beta.chat.completions.parse(
        model="gpt-4.1",
        response_format=InappropriateImageOutput,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Assess whether the image contains obscene or inappropriate content for a child that is {context.child_age} years old.",
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        max_tokens=300,
    )

    return InappropriateImageOutput(**json.loads(response.choices[0].message.content))
