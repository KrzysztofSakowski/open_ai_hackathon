from typing import Self
from pydantic import BaseModel
from dotenv import dotenv_values
from openai import AsyncOpenAI


class EnvSettings(BaseModel):
    """
    Configuration settings for the application.

    Values are loaded from the .env file, present in the root directory.
    """

    openai_api_key: str

    @classmethod
    def load(cls, env_path: str = ".env") -> Self:
        return cls(**{key.lower(): value for key, value in dotenv_values(env_path).items()})


env_settings = EnvSettings.load()

openai_client = AsyncOpenAI(api_key=env_settings.openai_api_key)
