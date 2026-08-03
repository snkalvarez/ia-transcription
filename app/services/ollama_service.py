import json
from pathlib import Path

import requests
from requests import RequestException

from app.core.config import settings


class OllamaServiceError(Exception):
    """Error al comunicarse con Ollama o al interpretar su respuesta."""


class OllamaService:

    def __init__(self):

        base_path = Path(__file__).resolve().parent.parent

        with open(base_path / "prompts" / "extractor_prompt.txt", encoding="utf8") as f:
            self.prompt_template = f.read()

        with open(base_path / "schemas" / "soap_schema.json", encoding="utf8") as f:
            schema = json.load(f)
            # El archivo original contenía el cuerpo completo de ejemplo. Ollama
            # espera que `format` reciba exclusivamente el esquema JSON.
            self.schema = schema.get("format", schema)

    def extract(self, texto: str):

        prompt = self.prompt_template.replace("{texto}", texto)

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": self.schema,
        }

        try:
            response = requests.post(
                f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate",
                json=payload,
                timeout=settings.OLLAMA_TIMEOUT,
            )
            response.raise_for_status()
            respuesta = response.json()["response"]
            return json.loads(respuesta)
        except (RequestException, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise OllamaServiceError("No fue posible obtener un resultado válido de Ollama.") from exc
