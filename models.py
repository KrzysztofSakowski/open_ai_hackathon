from pydantic import BaseModel


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


class ConvoInfo(BaseModel):
    convo_id: str
    existing_convo: bool = False


class FinalOutput(BaseModel):
    story: str
    story_image_paths: list[str]
    lesson: str
    reasoning: str
    plan_for_evening: str
    knowledge: Knowledge
    event: EventModel | None
