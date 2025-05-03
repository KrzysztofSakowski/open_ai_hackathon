from settings import openai_client


async def inappropriate_image_output_guardrail(image_base64: str) -> str:
    response = await openai_client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Oceń, czy obraz zawiera treści obsceniczne lub nieodpowiednie."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        max_tokens=300,
    )

    return response.choices[0].message.content
