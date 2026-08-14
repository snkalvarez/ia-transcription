import asyncio
import os
import tempfile
from fastapi import HTTPException, UploadFile
from app.core.config import settings
from app.core.constants import ALLOWED_AUDIO_MIME_TYPES
from app.services.whisper_service import WhisperService

class TranscriptionService:
    """Valida archivos y coordina la transcripción con Whisper."""
    def __init__(self) -> None:
        self.whisper_service = WhisperService()

    def transcribe(self, file_path: str) -> dict[str, str]:
        return self.whisper_service.transcribe_audio(file_path)

    async def transcribe_upload(self, file: UploadFile) -> dict[str, str]:
        if file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
            raise HTTPException(status_code=415, detail="Formato de audio no soportado.")
        contents = await file.read()
        max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
        if len(contents) > max_size:
            raise HTTPException(status_code=413, detail=f"El archivo supera el tamaño máximo permitido de {settings.MAX_AUDIO_SIZE_MB} MB.")
        temp_path: str | None = None
        try:
            extension = os.path.splitext(file.filename or "audio")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file.write(contents)
                temp_path = temp_file.name
            return await asyncio.to_thread(self.transcribe, temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    async def transcribe_upload_text(self, file: UploadFile) -> str:
        return (await self.transcribe_upload(file)).get("text", "")
