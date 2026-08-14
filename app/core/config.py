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

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://dgh", "http://hefesto"]

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: int = 300

    # Groq
    GROQ_API_KEY: str = ""
    # GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT: int = 300

    # Configuración de la base de datos.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ia_transcription_service"
    

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS if origin.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
