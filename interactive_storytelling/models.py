"""
Pydantic models for the interactive storytelling module.
"""

from pydantic import BaseModel


class StoryMoral(BaseModel):
    """Represents a moral for a story."""

    name: str  # A short identifier or title for the moral
    description: str  # The full description of the moral


EXAMPLE_STORY_MORALS: list[StoryMoral] = [
    StoryMoral(name="Friendship", description="Friendship and loyalty are priceless."),
    StoryMoral(name="Uniqueness", description="Everyone is unique."),
    StoryMoral(name="Goodness Returns", description="Goodness always returns."),
    StoryMoral(name="Honesty", description="It's always worth telling the truth."),
    StoryMoral(name="Respect Differences", description="Respect others, even if you're different."),
    StoryMoral(name="Persistence", description="Never give up."),
    StoryMoral(name="Inner Beauty", description="Inner beauty matters most."),
    StoryMoral(name="True Courage", description="Helping the weaker shows true courage."),
    StoryMoral(name="Listen to Elders", description="Listen to the advice of elders and the experienced."),
    StoryMoral(name="Responsibility", description="Be responsible for your actions."),
]


class InteractiveTurnDecisions(BaseModel):
    """
    User's choice for the next turn of the interactive story.
    """

    option1: str
    option2: str


class InteractiveTurnOutput(BaseModel):
    """
    Output for a single turn of the interactive story.

    Contains the scene text and the possible choices for the next turn.
    Decisions are optional, and lack of them denotes the end of the story.
    """

    scene_text: str
    decisions: InteractiveTurnDecisions | None


class StorytellerContext(BaseModel):
    """Context for the storyteller agent."""

    main_topic: str
    main_moral: StoryMoral
    main_character: str
    language: str
    age: int

    def get_prompt_content(self) -> str:
        """Returns the content for the system prompt."""
        return f"""
Prepare a story for child of age {self.age} years old.
The story should be about {self.main_topic}.
The story should have the following moral: {self.main_moral.name}.
The story should have the following main character: {self.main_character}.
The story should be written in the following language: {self.language}.
"""
