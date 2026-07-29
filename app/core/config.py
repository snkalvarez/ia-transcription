from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "IA Transcription Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8080

    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    MAX_AUDIO_SIZE_MB: int = 20
    
    ENABLE_VAD_FILTER: bool = True
    DEFAULT_LANGUAGE: str = "es"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()