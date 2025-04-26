from pydantic import BaseModel
from typing import Literal, Any


class Address(BaseModel):
    country: str | None
    city: str | None


class PersonEntry(BaseModel):
    name: str | None
    age: int | None
    likes: list[str]
    dislikes: list[str]


class Knowledge(BaseModel):
    address: Address | None = None
    parent: PersonEntry | None = None
    child: PersonEntry | None = None
    theme: str | None = None


class EventModel(BaseModel):
    name: str
    description: str
    justification: str
    estimated_cost: str | float | None = None
    url: str | None = None
    url_to_book_tickets: str | None = None
    address: str | None = None


class StoryContinuationOutput(BaseModel):
    next_scene: str
    option1: str
    option2: str


class InteractiveTurnOutput(BaseModel):
    """Output for a single turn of the interactive story + illustration agent."""

    scene_text: str
    image_paths: list[str]
    options: StoryContinuationOutput | None  # Holds the *next* scene and options, or None if story ends


class FinalOutput(BaseModel):
    story: str
    story_image_paths: list[str]
    lesson: str
    reasoning: str
    plan_for_evening: str
    knowledge: Knowledge
    event: EventModel | None


class ConvoInfo(BaseModel):
    convo_id: str
    existing_convo: bool = False


class MessageToUser(BaseModel):
    type: Literal["audio", "output"]
