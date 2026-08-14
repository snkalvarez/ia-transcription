import asyncio
import json
from pathlib import Path
import requests
from requests import RequestException
from app.core.config import settings

class OllamaServiceError(Exception):
    """Error al comunicarse con Ollama o al interpretar su respuesta."""

class OllamaService:
    def __init__(self) -> None:
        base_path = Path(__file__).resolve().parent.parent
        self.prompt_template = (base_path / "prompts" / "extractor_prompt.txt").read_text(encoding="utf-8")
        schema = json.loads((base_path / "schemas" / "soap_schema.json").read_text(encoding="utf-8"))
        self.schema = schema.get("format", schema)

    def extract(self, text: str) -> dict:
        payload = {"model": settings.OLLAMA_MODEL, "prompt": self.prompt_template.replace("{texto}", text), "stream": False, "format": self.schema}
        try:
            response = requests.post(f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate", json=payload, timeout=settings.OLLAMA_TIMEOUT)
            response.raise_for_status()
            return json.loads(response.json()["response"])
        except (RequestException, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise OllamaServiceError("No fue posible obtener un resultado válido de Ollama.") from exc

    async def extract_async(self, text: str) -> dict:
        """Evita bloquear el bucle de eventos durante la llamada HTTP síncrona."""
        return await asyncio.to_thread(self.extract, text)
