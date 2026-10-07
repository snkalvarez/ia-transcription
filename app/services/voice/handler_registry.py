from app.services.voice.handlers.formulario_hc_14_handler import FormularioHc14VoiceHandler
from app.services.voice.handlers.soap_handler import (
    SoapVoiceHandler,
)


VOICE_HANDLERS = {
    "soap": SoapVoiceHandler(),
    "formulario_hc_14": FormularioHc14VoiceHandler(),
}


def get_voice_handler(handler_type: str):

    handler = VOICE_HANDLERS.get(handler_type)

    if not handler:
        raise ValueError(
            f"Tipo de flujo de voz no soportado: {handler_type}"
        )

    return handler