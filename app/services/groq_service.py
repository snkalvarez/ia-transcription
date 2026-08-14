import json
from pathlib import Path
from groq import APIError, AsyncGroq
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT = (BASE_DIR / "prompts" / "extractor_prompt.txt").read_text(encoding="utf-8")
JSON_SCHEMA = json.loads((BASE_DIR / "schemas" / "soap_schema.json").read_text(encoding="utf-8"))

class GroqServiceError(Exception):
    """Error de comunicación con Groq o de interpretación de su respuesta."""

class GroqService:
    """Adaptador del SDK de Groq; las rutas no conocen sus detalles."""
    def __init__(self) -> None:
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=settings.GROQ_TIMEOUT)

    async def extract_note(self, text: str) -> dict:
        try:
            completion = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL, temperature=0,
                messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": text}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {**JSON_SCHEMA, "strict": True},
                },
            )
            return json.loads(completion.choices[0].message.content)
        except (APIError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GroqServiceError("No fue posible obtener un resultado válido de Groq.") from exc

    async def chat(self, text: str) -> str | None:
        try:
            completion = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": text}], model=settings.GROQ_MODEL,
                temperature=0.7, max_tokens=1024,
            )
            return completion.choices[0].message.content
        except (APIError, IndexError, TypeError) as exc:
            raise GroqServiceError("No fue posible obtener una respuesta de Groq.") from exc
