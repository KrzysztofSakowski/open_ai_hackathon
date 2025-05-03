from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import date


class Language(str, Enum):
    """Enumeration for supported languages."""

    pl = "pl"
    en = "en"


class TransportMethod(str, Enum):
    """Enumeration for available transport methods."""

    car = "car"
    public_transport = "public_transport"
    walking = "walking"
    cycling = "cycling"


class InterestArea(str, Enum):
    """Enumeration for areas of interest for children."""

    science = "science"
    art = "art"
    sports = "sports"
    nature = "nature"
    technology = "technology"
    storytelling = "storytelling"
    music = "music"
    history = "history"


class DifficultyLevel(str, Enum):
    """Enumeration for difficulty levels, e.g., for attention span or activity complexity."""

    low = "low"
    medium = "medium"
    high = "high"


class ChildProfile(BaseModel):
    """
    Represents a child's profile, including personal details, interests, and traits.

    Attributes:
        name (str): The child's name.
        date_of_birth (date): The child's date of birth.
        interests (List[InterestArea]): A list of the child's areas of interest.
        favorite_color (Optional[str]): The child's favorite color, if specified.
        hobbies (Optional[List[str]]): A list of the child's hobbies, if specified.
        difficult_subjects (Optional[List[str]]): Subjects the child finds challenging, if specified.
        personality_traits (Optional[List[str]]): A list of the child's personality traits, if specified.
        attention_span (Optional[DifficultyLevel]): The child's attention span level, if specified.
    """

    name: str
    date_of_birth: date
    interests: List[InterestArea]
    favorite_color: Optional[str] = None
    hobbies: Optional[List[str]] = None
    difficult_subjects: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None
    attention_span: Optional[DifficultyLevel] = None


class ParentProfile(BaseModel):
    """Represents the profile of a parent user."""

    name: str
    email: str
    location: str
    preferred_language: Language
    available_transport_methods: List[TransportMethod]
    preferred_communication_method: Optional[str] = None
    parenting_style: Optional[str] = None  # e.g. "strict", "permissive", "authoritative", etc.


class UserContext(BaseModel):
    """Represents the overall user context, combining parent and child profiles."""

    parent: ParentProfile
    children: List[ChildProfile]
    registration_date: date
    last_active: Optional[date] = None
