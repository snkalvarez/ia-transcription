import json
import base64
from websockets.client import connect as ws_connect
from app.core.logger import logger
from app.core.config import settings

class GeminiLiveService:
    def __init__(self):
        # 1. URL Oficial y exacta para el protocolo WebSocket de Gemini Live
        self.host_url = "wss://generativelanguage.googleapis.com"
        
        # Obtenemos la API key y eliminamos espacios o comillas accidentales
        raw_key = settings.GEMINI_API_KEY
        self.api_key = raw_key.strip().replace('"', '').replace("'", "")
        
        # ... (Tu schema SOAP_TOOL y SYSTEM_INSTRUCTION se quedan exactamente igual) ...
        self.soap_tool = {
            "functionDeclarations": [{
                "name": "guardar_evolucion_soap",
                "description": "Guarda de forma estructurada la evolución del paciente bajo el formato SOAP.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "subjetivo": {"type": "STRING", "description": "Síntomas narrados por el paciente..."},
                        "objetivo": {"type": "STRING", "description": "Hallazgos clínicos medibles..."},
                        "analisis": {"type": "STRING", "description": "Juicio clínico del médico..."},
                        "plan": {"type": "STRING", "description": "Tratamiento a seguir..."}
                    },
                    "required": ["subjetivo", "objetivo", "analisis", "plan"]
                }
            }]
        }

        self.system_instruction = (
            "Eres un asistente de voz clínico ultra-estructurado. Tu objetivo exclusivo es guiar al médico "
            "paso a paso para rellenar la evolución médica siguiendo el orden estricto del formato SOAP..."
        )

    async def iniciar_sesion_gemini(self):
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
                    "responseModalities": ["AUDIO"],  # Correctamente posicionado aquí
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": { "voiceName": "Aoede" }
                        }
                    }
                },
                "systemInstruction": {
                    "parts": [
                        {"text": self.system_instruction}
                    ]
                },
                "tools": [self.soap_tool]
            }
        }
        
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
