import json
from pathlib import Path
from groq import APIError, AsyncGroq
from app.core.config import settings
from app.services.schema_builder import (SchemaBuilder,SchemaBuilderError)

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT = (BASE_DIR / "prompts" / "extractor_prompt.txt").read_text(encoding="utf-8")


class GroqServiceError(Exception):
    """Error de comunicación con Groq o de interpretación de su respuesta."""


class GroqService:
    """Adaptador del SDK de Groq; las rutas no conocen sus detalles."""

    def __init__(self) -> None:
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY,timeout=settings.GROQ_TIMEOUT)

        # Directorio donde viven los schemas.
        self.schemas_dir = BASE_DIR / "schemas"

        # Builder responsable de resolver los $ref.
        self.schema_builder = SchemaBuilder(
            self.schemas_dir
        )

    async def extract_note(self, text: str) -> dict:

        try:
            # =====================================================
            # 1. CONSTRUIR EL SCHEMA COMPLETO
            # =====================================================
            formulario_schema = self.schema_builder.build("formulario_clinico.schema.json")
            # =====================================================
            # 2. OBTENER NAME Y SCHEMA
            # =====================================================
            schema_name = formulario_schema["name"]
            schema = formulario_schema["schema"]
            # =====================================================
            # DEBUG TEMPORAL
            # =====================================================
            print("\n========== SCHEMA ENVIADO A GROQ ==========")
            print(json.dumps(formulario_schema, indent=2, ensure_ascii=False ))
            print("===========================================\n")
            # =====================================================
            # 3. LLAMADA A GROQ
            # =====================================================

            completion = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                temperature=0,
                messages=[{"role": "system","content": PROMPT},{"role": "user","content": text}],

                response_format={
                    "type": "json_schema",
                    "json_schema": { "name": schema_name, "schema": schema, "strict": True }
                }
            )

            # =====================================================
            # 4. RESPUESTA
            # =====================================================
            content = completion.choices[0].message.content
            return json.loads(content)

        except (APIError,IndexError,TypeError,json.JSONDecodeError,SchemaBuilderError) as exc:
            raise GroqServiceError(
                "No fue posible obtener un resultado válido de Groq."
            ) from exc

    async def chat(self, text: str) -> str | None:
        try:
            completion = await self.client.chat.completions.create(
                messages=[{"role": "user","content": text}],
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content

        except (APIError,IndexError,TypeError) as exc:
            raise GroqServiceError("No fue posible obtener una respuesta de Groq.") from exc