"""Proveedores de dependencias para las rutas HTTP."""
from functools import lru_cache
from app.repositories.procesamiento_ia_repository import ProcessingRepository
from app.services.groq_service import GroqService
from app.services.ollama_service import OllamaService
from app.services.transcription_service import TranscriptionService

@lru_cache
def get_transcription_service() -> TranscriptionService:
    """Crea Whisper bajo demanda; cargar el modelo al importar la app es costoso."""
    return TranscriptionService()

@lru_cache
def get_ollama_service() -> OllamaService:
    return OllamaService()

@lru_cache
def get_groq_service() -> GroqService:
    return GroqService()

def get_processing_repository() -> ProcessingRepository:
    return ProcessingRepository()
