from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    INTERVAL_SECONDS: int
    LOG_LEVEL: str
    CONTAINER_NAME: str
    ODDS_API_KEY: str
    SENDER_MNEMONIC: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 