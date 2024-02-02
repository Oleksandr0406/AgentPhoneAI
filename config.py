from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PLAY_HT_USER_ID: str
    PLAY_HT_SECRET_KEY: str
    OPENAI_API_KEY: str

    MONGO_INITDB_DATABASE: str
    DATABASE_URL: str

    JWT_PUBLIC_KEY: str
    JWT_PRIVATE_KEY: str
    REFRESH_TOKEN_EXPIRES_IN: int
    ACCESS_TOKEN_EXPIRES_IN: int
    JWT_ALGORITHM: str

    CLIENT_ORIGIN: str

    class Config:
        env_file = "./.env"


settings = Settings()
