import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_groq_service
from app.core.logger import logger
from app.schemas.chat_request import ChatRequest
from app.services.groq_service import GroqService, GroqServiceError

router = APIRouter(tags=["groq"])
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


@router.post("/groq-chat")
async def groq_chat(
    request: ChatRequest,
    groq_service: GroqService = Depends(get_groq_service),
) -> dict[str, str | None]:
    try:
        response_text = await groq_service.chat(request.text)
    except GroqServiceError as exc:
        logger.exception("Error durante la petición a Groq Chat Completions")
        raise HTTPException(
            status_code=502,
            detail="Error al procesar la solicitud con el servicio de Groq.",
        ) from exc
    return {"status": "success", "response": response_text}


@router.get("/json-schema")
async def get_json_schema() -> dict:
    """Expone el contrato JSON estático que consume el cliente actual."""
    return json.loads((SCHEMAS_DIR / "response_ok.json").read_text(encoding="utf-8"))
