from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.services.transcription_service import TranscriptionService
from app.services.ollama_service import OllamaService, OllamaServiceError
from app.services.groq_service import extract_note
from app.core.config import settings
from app.core.logger import logger
from app.schemas.chat_request import ChatRequest
from groq import AsyncGroq
import logging
import json
from pathlib import Path

client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=settings.GROQ_TIMEOUT)

logger = logging.getLogger(__name__)

import asyncio

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
BASE_DIR = Path(__file__).resolve().parent

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
    logger.info("Iniciando proceso de transcripción para el archivo %s", file.filename)
    logger.info("Archivo recibido %s", file.filename)
    result = await transcription_service.transcribe_upload(file, ALLOWED_TYPES)
    return result

@app.post("/transcribeandresultado")
async def transcribeandresultado(file: UploadFile = File(...)):
    """Transcribe un audio y genera el resultado clínico estructurado con Ollama."""
    transcription = await transcription_service.transcribe_upload(file, ALLOWED_TYPES)
    try:
        resultado = await asyncio.to_thread(ollama_service.extract, transcription["text"])
    except OllamaServiceError as exc:
        logger.exception("Error al solicitar la extracción clínica a Ollama")
        raise HTTPException(
            status_code=502,
            detail="Ollama no está disponible o devolvió una respuesta inválida.",
        ) from exc

    return {"transcription": transcription, "resultado": resultado}


@app.post("/transcribeandresultadogroq")
async def transcribeandresultadogroq(file: UploadFile = File(...)):
    """Transcribe un audio y genera el resultado clínico estructurado con Groq."""
    transcription = await transcription_service.transcribe_upload(file, ALLOWED_TYPES)
    try:
        resultado = await extract_note(transcription["text"])
    except Exception as exc:
        logger.exception("Error al solicitar la extracción clínica a Groq")
        raise HTTPException(
            status_code=502,
            detail="Groq no está disponible o devolvió una respuesta inválida.",
        ) from exc

    return {"transcription": transcription, "resultado": resultado}


@app.post("/groq-chat")
async def groq_chat(request: ChatRequest):
    try:
        # Realizamos la petición de transcripción/generación de texto a Groq
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": request.text,
                }
            ],
            model=settings.GROQ_MODEL,
            temperature=0.7,         # Controla la creatividad (0.0 más lógico, 1.0 más creativo)
            max_tokens=1024,         # Límite de tokens en la respuesta
        )

        # Extraemos el texto de la respuesta devuelta por Groq
        response_text = chat_completion.choices[0].message.content

        return {
            "status": "success",
            "response": response_text
        }

    except Exception as e:
        logger.exception("Error durante la petición a Groq Chat Completions")
        raise HTTPException(
            status_code=502,
            detail="Error al procesar la solicitud con el servicio de Groq.",
        ) from e


@app.get("/json-schema")
def get_json_schema():
    """Devuelve el esquema JSON de la clase ChatRequest."""
    schema_path = BASE_DIR / "schemas" / "response_ok.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))

