from app.services.whisper_service import WhisperService
from app.core.config import settings
from fastapi import HTTPException, UploadFile
import asyncio
import os
import tempfile

class TranscriptionService:

    def __init__(self):
        self.whisper_service = WhisperService()

    def transcribe(self, file_path: str):

        return self.whisper_service.transcribe_audio(file_path)

    async def transcribe_upload(self, file: UploadFile, allowed_types: set[str]):
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="Formato de audio no soportado.")

        max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo supera el tamaño maximo permitido de {settings.MAX_AUDIO_SIZE_MB} MB.",
            )

        temp_path = None
        try:
            extension = os.path.splitext(file.filename or "audio")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file.write(contents)
                temp_path = temp_file.name

            return await asyncio.to_thread(self.transcribe, temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    async def transcribe_upload_text(self, file: UploadFile, allowed_types: set[str]) -> str:
        transcription = await self.transcribe_upload(file, allowed_types)
        return str(transcription.get("text", ""))