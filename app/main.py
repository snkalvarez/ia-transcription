from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.services.transcription_service import TranscriptionService
from app.services.ollama_service import OllamaService, OllamaServiceError
from app.core.config import settings
from app.core.logger import logger

import tempfile
import shutil
import os
import asyncio

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )

transcription_service = TranscriptionService()
ollama_service = OllamaService()

ALLOWED_TYPES = {"audio/webm", "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/ogg" }

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

@app.post("/transcribeandresultado")
async def transcribeandresultado(file: UploadFile = File(...)):
    """Transcribe un audio y genera el resultado clínico estructurado con Ollama."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Formato de audio no soportado.")

    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el tamaño máximo permitido de {settings.MAX_AUDIO_SIZE_MB} MB."
        )

    temp_path = None
    try:
        extension = os.path.splitext(file.filename or "audio")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        transcription = await asyncio.to_thread(transcription_service.transcribe, temp_path)
        try:
            resultado = await asyncio.to_thread(ollama_service.extract, transcription["text"])
        except OllamaServiceError as exc:
            logger.exception("Error al solicitar la extracción clínica a Ollama")
            raise HTTPException(
                status_code=502,
                detail="Ollama no está disponible o devolvió una respuesta inválida.",
            ) from exc

        return {"transcription": transcription, "resultado": resultado}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
