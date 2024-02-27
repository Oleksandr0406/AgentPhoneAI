from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    MONGO_INITDB_DATABASE: str
    DATABASE_URL: str

    JWT_PUBLIC_KEY: str
    JWT_PRIVATE_KEY: str
    REFRESH_TOKEN_EXPIRES_IN: int
    ACCESS_TOKEN_EXPIRES_IN: int
    JWT_ALGORITHM: str

    CLIENT_ORIGIN: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    PINECONE_API_KEY: str
    PINECONE_ENV: str
    PINECONE_INDEX: str
    
    class Config:
        env_file = "./.env"


settings = Settings()
