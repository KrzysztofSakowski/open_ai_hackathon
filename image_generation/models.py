from pydantic import BaseModel


class ImageGenerationPrompt(BaseModel):
    """
    Prompt for image generation.

    The base images could be used to generate consistent images of the same subject across multiple prompts,
    e.g. the same main character in different poses, settings, etc.
    """

    base_images: list[str]  # List of base image paths
    prompt: str


class ImageGeneratorContext(BaseModel):
    """Context for image generation agent."""

    child_age: int
    child_preferred_style: str
    images_to_generate: list[ImageGenerationPrompt]


class InappropriateImageOutput(BaseModel):
    """Contains the result of the inappropriate image output guardrail."""

    is_inappropriate: bool
    reason: str
