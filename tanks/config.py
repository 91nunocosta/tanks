from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = Field(min_length=3)
