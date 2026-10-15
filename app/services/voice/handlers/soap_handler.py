from app.services.voice.handlers.base_handler import BaseVoiceHandler
from app.core.logger import logger


class SoapVoiceHandler(BaseVoiceHandler):

    name = "soap"

    @property
    def system_instruction(self) -> str:
        return (
            "Eres un asistente de voz clínico ultra-estructurado. "
            "Tu objetivo exclusivo es guiar al médico paso a paso "
            "para rellenar la evolución médica siguiendo el orden "
            "estricto del formato SOAP."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "functionDeclarations": [
                    {
                        "name": "guardar_evolucion_soap",
                        "description": (
                            "Guarda de forma estructurada la evolución "
                            "del paciente bajo el formato SOAP."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "subjetivo": {
                                    "type": "STRING",
                                    "description": (
                                        "Síntomas narrados por el paciente."
                                    ),
                                },
                                "objetivo": {
                                    "type": "STRING",
                                    "description": (
                                        "Hallazgos clínicos medibles."
                                    ),
                                },
                                "analisis": {
                                    "type": "STRING",
                                    "description": (
                                        "Juicio clínico del médico."
                                    ),
                                },
                                "plan": {
                                    "type": "STRING",
                                    "description": (
                                        "Tratamiento a seguir."
                                    ),
                                },
                            },
                            "required": [
                                "subjetivo",
                                "objetivo",
                                "analisis",
                                "plan",
                            ],
                        },
                    }
                ]
            }
        ]

    @property
    def ends_session_after_tool_call(self) -> bool:
        """
        SOAP finaliza automáticamente la conversación
        cuando Gemini ejecuta guardar_evolucion_soap.
        """
        return True

    async def handle_tool_call(
        self,
        call: dict,
        sio,
        sid: str,
    ):
        """
        Procesa las herramientas propias del flujo SOAP.
        """

        if call["name"] != "guardar_evolucion_soap":
            return None

        extracted_soap = call["args"]

        logger.info(
            f"Evolución SOAP completa extraída "
            f"exitosamente para {sid}!"
        )

        logger.info(
            extracted_soap
        )

        # ======================================================
        # ENVIAR RESULTADO AL FRONTEND
        # ======================================================

        await sio.emit(
            "voice_result",
            extracted_soap,
            to=sid,
        )

        return {
            "success": True
        }