import json
import base64
from websockets.client import connect as ws_connect
from app.core.logger import logger
from app.core.config import settings

class GeminiLiveService:

    def __init__(self):
        raw_key = settings.GEMINI_API_KEY

        self.api_key = (
            raw_key
            .strip()
            .replace('"', '')
            .replace("'", "")
        )

        self.host_url = (
            "wss://generativelanguage.googleapis.com"
        )

    async def iniciar_sesion_gemini(self,system_instruction: str,tools: list | None = None,):
        import urllib.parse
        
        if not self.api_key:
            logger.error("Falta la variable de entorno GEMINI_API_KEY")
            raise ValueError("Falta GEMINI_API_KEY")

        clean_key = str(self.api_key).strip().replace('"', '').replace("'", "")

        # 1. Componentes limpios del Host (v1beta)
        base_host = "generativelanguage.googleapis.com"
        path = "/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
        query = urllib.parse.urlencode({"key": clean_key})
        uri_final = f"wss://{base_host}{path}?{query}"
        
        logger.info("Conectando de forma aislada a Google AI Studio (v1beta)...")
        gemini_ws = await ws_connect(uri_final)
        
        # 2. Handshake con CamelCase exacto y tipos estructurados
        setup_message = {
            "setup": {
                "model": "models/gemini-3.8-live",

                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Aoede"
                            }
                        }
                    }
                },

                "systemInstruction": {
                    "parts": [
                        {
                            "text": system_instruction
                        }
                    ]
                }
            }
        }

        if tools:
            setup_message["setup"]["tools"] = tools
        
        await gemini_ws.send(json.dumps(setup_message))

        # No enviar audio hasta que Gemini confirme que aceptó el setup.
        setup_response = json.loads(await gemini_ws.recv())
        if "setupComplete" not in setup_response:
            await gemini_ws.close()
            raise RuntimeError(f"Gemini no confirmó la configuración: {setup_response}")
        return gemini_ws

    async def enviar_audio_chunk(self, gemini_ws, raw_audio_bytes: bytes):
        """Codifica y transmite el fragmento PCM crudo a Gemini"""
        base64_audio = base64.b64encode(raw_audio_bytes).decode('utf-8')
        realtime_input = {
            "realtimeInput": {
                "audio": {
                    "mimeType": "audio/pcm;rate=16000",
                    "data": base64_audio
                }
            }
        }
        await gemini_ws.send(json.dumps(realtime_input))

    async def enviar_texto(self, gemini_ws, texto: str):
        """Envía un turno textual para iniciar una respuesta de Gemini."""
        client_content = {
            "clientContent": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": texto
                            }
                        ],
                    }
                ],
                "turnComplete": True,
            }
        }
        await gemini_ws.send(json.dumps(client_content))
