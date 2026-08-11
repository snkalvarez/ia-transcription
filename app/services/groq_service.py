import json
from pathlib import Path

from groq import AsyncGroq

from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

BASE_DIR = Path(__file__).resolve().parent.parent

PROMPT = (
    BASE_DIR / "prompts" / "extractor_prompt.txt"
).read_text(encoding="utf-8")

JSON_SCHEMA = json.loads(
    (
        BASE_DIR / "schemas" / "soap_schema.json"
    ).read_text(encoding="utf-8")
)


async def extract_note(text: str):

    completion = await client.chat.completions.create(
        model="openai/gpt-oss-20b",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": JSON_SCHEMA
        }
    )

    return json.loads(
        completion.choices[0].message.content
    )