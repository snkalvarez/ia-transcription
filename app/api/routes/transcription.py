from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import (get_groq_service,get_processing_repository,get_transcription_service)
from app.core.database import get_db
from app.core.logger import logger
from app.repositories.procesamiento_ia_repository import ProcessingRepository
from app.services.groq_service import GroqService, GroqServiceError
from app.services.ollama_service import OllamaService, OllamaServiceError
from app.services.transcription_service import TranscriptionService

router = APIRouter(tags=["transcription"])

@router.post(
    "/transcribe",
    summary="Transcribir audio",
    description="Recibe un archivo de audio y devuelve el texto transcrito utilizando el servicio de transcripción configurado.",
)
async def transcribe(
    file: UploadFile = File(...),
    service: TranscriptionService = Depends(get_transcription_service),
) -> dict[str, str]:
    """Transcribe un archivo de audio a texto para su posterior procesamiento."""
    return await service.transcribe_upload(file)


@router.get(
    "/procesamientos/activo",
    summary="Obtener procesamiento activo",
    description="Consulta la respuesta vigente del día actual para un número de ingreso y tipo específicos.",
)
async def get_current_active_processing(
    numero_ingreso: str,
    tipo: str,
    db: AsyncSession = Depends(get_db),
    repository: ProcessingRepository = Depends(get_processing_repository),
) -> dict[str, object]:
    """Retorna la respuesta vigente del día actual para un ingreso y tipo."""
    processing = await repository.get_current_active(
        db=db,
        numero_ingreso=numero_ingreso,
        tipo=tipo,
    )
    if processing is None:
        raise HTTPException(
            status_code=404,
            detail="No existe una respuesta vigente para el ingreso, tipo y día actual.",
        )

    stored_resultado = processing.resultado
    if isinstance(stored_resultado.get("resultado"), dict):
        stored_resultado = stored_resultado["resultado"]

    return {
        "id": processing.id,
        "numero_ingreso": processing.numero_ingreso,
        "tipo": processing.tipo,
        "fecha": processing.fecha,
        "schema": processing.schema,
        "resultado": stored_resultado,
        "vigente": processing.vigente,
    }


# @router.post(
#     "/transcribeandresultado",
#     summary="Transcribir y extraer resultado con Ollama",
#     description="Transcribe el archivo cargado y luego envía el texto a Ollama para obtener una extracción clínica estructurada.",
# )
# async def transcribe_and_resultado(
#     file: UploadFile = File(...),
#     transcription_service: TranscriptionService = Depends(get_transcription_service),
#     ollama_service: OllamaService = Depends(get_ollama_service),
# ) -> dict[str, object]:
#     """Transcribe el audio y devuelve el resultado generado por Ollama."""
#     transcription = await transcription_service.transcribe_upload(file)
#     try:
#         resultado = await ollama_service.extract_async(transcription["text"])
#     except OllamaServiceError as exc:
#         logger.exception("Error al solicitar la extracción clínica a Ollama")
#         raise HTTPException(
#             status_code=502,
#             detail="Ollama no está disponible o devolvió una respuesta inválida.",
#         ) from exc
#     return {"transcription": transcription, "resultado": resultado}


@router.post(
    "/procesarAudioTrabajarAnalisisConIa",
    summary="Transcribir y guardar resultado clínico",
    description="Transcribe el archivo recibido, extrae la información clínica con un agente IA y guarda el procesamiento asociado al ingreso indicado.",
)
async def transcribe_and_resultado_groq(
    file: UploadFile = File(...),
    numero_ingreso: str = Form(...),
    tipo: str = Form(...),
    db: AsyncSession = Depends(get_db),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    groq_service: GroqService = Depends(get_groq_service),
    repository: ProcessingRepository = Depends(get_processing_repository),
) -> dict[str, object]:
    """Transcribe, extrae la nota clínica con Groq y persiste el procesamiento como vigente."""
    transcription = await transcription_service.transcribe_upload(file)
    print(f"Transcripción obtenida: {transcription['text']}")
    try:
        resultado = await groq_service.extract_note(transcription["text"])
        resultado["transcription"] = transcription
    except GroqServiceError as exc:
        logger.exception("Error al solicitar la extracción clínica a Groq")
        raise HTTPException(
            status_code=502,
            detail="Groq no está disponible o devolvió una respuesta válida.",
        ) from exc
    response_data = {"resultado": resultado}
    processing = await repository.save(
        db=db,
        numero_ingreso=numero_ingreso,
        tipo=tipo,
        schema="SOAP",
        resultado=resultado
    )
    response_data["vigente"] = processing.vigente
    return response_data
