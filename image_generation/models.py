from pydantic import BaseModel


class ImageGenerationPrompt(BaseModel):
    """
    Prompt for image generation.

    The base images could be used to generate consistent images of the same subject across multiple prompts,
    e.g. the same main character in different poses, settings, etc.
    """

    base_images: list[bytes]
    prompt: str


class ImageGeneratorContext(BaseModel):
    """Context for image generation agent."""

    child_age: int
    child_preferred_style: str
    images_to_generate: list[ImageGenerationPrompt]


class ImageGenerationOutput(BaseModel):
    """Output of the image generation agent."""

    images: list[bytes]
