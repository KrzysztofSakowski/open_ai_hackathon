from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import date


class Language(str, Enum):
    pl = "pl"
    en = "en"


class TransportMethod(str, Enum):
    car = "car"
    public_transport = "public_transport"
    walking = "walking"
    cycling = "cycling"


class InterestArea(str, Enum):
    science = "science"
    art = "art"
    sports = "sports"
    nature = "nature"
    technology = "technology"
    storytelling = "storytelling"
    music = "music"
    history = "history"


class DifficultyLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ChildProfile(BaseModel):
    name: str
    date_of_birth: date
    interests: List[InterestArea]
    favorite_color: Optional[str] = None
    hobbies: Optional[List[str]] = None
    difficult_subjects: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None
    attention_span: Optional[DifficultyLevel] = None


class ParentProfile(BaseModel):
    name: str
    email: str
    location: str
    preferred_language: Language
    available_transport_methods: List[TransportMethod]
    preferred_communication_method: Optional[str] = None
    parenting_style: Optional[str] = None  # e.g. "strict", "permissive", "authoritative", etc.


class UserContext(BaseModel):
    parent: ParentProfile
    children: List[ChildProfile]
    registration_date: date
    last_active: Optional[date] = None
