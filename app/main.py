from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.services.transcription_service import TranscriptionService
from app.core.config import settings
from app.core.logger import logger

import tempfile
import shutil
import os

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

transcription_service = TranscriptionService()

ALLOWED_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg"
}

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Formato de audio no soportado."
        )    
    logger.info("Iniciando proceso de transcripción para el archivo %s", file.filename)
    print("Archivo recibido:", file.filename, file.content_type)
    MAX_SIZE = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    contents = await file.read()
    logger.info("Archivo recibido %s", file.filename)

    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el tamaño máximo permitido de {settings.MAX_AUDIO_SIZE_MB} MB."
        )
    await file.seek(0)
    temp_path = None

    try:
        extension = file.filename.split(".")[-1]
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{extension}"
        )

        temp_path = temp_file.name
        temp_file.close()
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = transcription_service.transcribe(temp_path)
        return result

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)