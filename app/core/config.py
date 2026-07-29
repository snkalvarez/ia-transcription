from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "IA Transcription Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    MAX_AUDIO_SIZE_MB: int = 20
    
    ENABLE_VAD_FILTER: bool = True
    DEFAULT_LANGUAGE: str = "es"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()