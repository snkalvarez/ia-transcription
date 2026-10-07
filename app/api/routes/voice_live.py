import json
import base64
import asyncio
import jwt

from app.services.gemini_live_service import GeminiLiveService
from app.services.voice.handler_registry import get_voice_handler
from app.core.logger import logger
from app.core.config import settings


# ==========================================================
# SESIONES ACTIVAS
# ==========================================================

# Estructura:
#
# client_sessions[sid] = {
#     "gemini_ws": websocket,
#     "handler": handler,
# }
#
client_sessions = {}
gemini_service = GeminiLiveService()

def register_voice_events(sio):

    @sio.event
    async def connect(sid, environ, auth=None):
        """
        Inicializa una sesión de voz.
        """

        auth = auth or {}
        token = auth.get("token")

        # ======================================================
        # VALIDACIÓN JWT
        # ======================================================

        if settings.JWT_SECRET:
            try:
                if not token:
                    logger.warning( 
                        "Socket.IO connection rejected: "
                        "missing JWT"
                    )
                    return False

                jwt.decode(token,settings.JWT_SECRET,algorithms=["HS256"],)

            except jwt.PyJWTError:
                logger.warning(
                    "Socket.IO connection rejected: "
                    "missing or invalid JWT"
                )
                return False

        # ======================================================
        # TIPO DE FLUJO
        # ======================================================

        # Si el frontend no envía voice_type,
        # usamos SOAP para mantener compatibilidad
        # con el frontend actual.
        voice_type = auth.get(
            "voice_type",
            "soap",
        )

        logger.info(
            f"🩺 Médico conectado vía Socket.IO "
            f"(Session ID: {sid}, "
            f"Voice Type: {voice_type})"
        )

        try:
            # ==================================================
            # OBTENER HANDLER
            # ==================================================

            handler = get_voice_handler(voice_type)

            # ==================================================
            # CONECTAR CON GEMINI
            # ==================================================

            gemini_ws = (
                await gemini_service.iniciar_sesion_gemini(
                    system_instruction=(handler.system_instruction),
                    tools=handler.tools,
                )
            )
            # ==================================================
            # GUARDAR SESIÓN
            # ==================================================

            client_sessions[sid] = {
                "gemini_ws": gemini_ws,
                "handler": handler,
            }

            # ==================================================
            # ESCUCHAR RESPUESTAS DE GEMINI
            # ==================================================

            asyncio.create_task(
                listen_to_gemini_stream(
                    sid=sid,
                    gemini_ws=gemini_ws,
                    handler=handler,
                    sio=sio,
                )
            )

        except Exception as e:
            logger.error(
                f"Error al enlazar sesión de voz "
                f"con Gemini: {str(e)}"
            )
            await sio.disconnect(sid)

    @sio.event
    async def audio_chunk(sid, data):
        """
        Recibe audio desde React y lo transmite a Gemini.
        """

        session = client_sessions.get(sid)
        if not session:
            logger.warning(
                f"Audio recibido para una sesión "
                f"inexistente: {sid}"
            )
            return

        gemini_ws = session["gemini_ws"]

        # ======================================================
        # VALIDAR WEBSOCKET
        # ======================================================
        if (
            gemini_ws
            and hasattr(gemini_ws, "open")
            and gemini_ws.open
        ):
            await gemini_service.enviar_audio_chunk(
                gemini_ws,
                data,
            )

    @sio.event
    async def disconnect(sid):
        """
        Cierra correctamente la sesión del cliente.
        """
        logger.info(
            f"🔴 Sesión de voz finalizada "
            f"para el cliente {sid}"
        )

        session = client_sessions.pop(
            sid,
            None,
        )

        if not session:
            return

        gemini_ws = session["gemini_ws"]

        if gemini_ws:
            try:
                await gemini_ws.close()

            except Exception as e:
                logger.warning(
                    f"Error cerrando WebSocket de Gemini "
                    f"para {sid}: {str(e)}"
                )


async def listen_to_gemini_stream(sid,gemini_ws,handler,sio,):
    """
    Escucha continuamente las respuestas de Gemini.
    Este método es genérico.
    No conoce SOAP, enfermería, órdenes médicas,
    etc.
    Se encarga solamente de:
    1. Recibir audio de Gemini.
    2. Enviarlo a React.
    3. Detectar llamadas a herramientas.
    4. Delegar la herramienta al handler.
    5. Responder a Gemini.
    """

    try:

        async for response in gemini_ws:
            data = json.loads(response)

            # ==================================================
            # GEMINI DEVUELVE AUDIO
            # ==================================================

            if (
                "serverContent" in data
                and "modelTurn" in data["serverContent"]
            ):

                parts = (
                    data["serverContent"]
                    ["modelTurn"]
                    ["parts"]
                )

                for part in parts:
                    if (
                        "inlineData" in part
                        and "data" in part["inlineData"]
                    ):
                        audio_bytes = base64.b64decode(
                            part["inlineData"]["data"]
                        )
                        await sio.emit(
                            "audio_response",
                            audio_bytes,
                            to=sid,
                        )

            # ==================================================
            # GEMINI EJECUTA UNA TOOL
            # ==================================================

            elif "toolCall" in data:
                function_calls = (
                    data["toolCall"]
                    ["functionCalls"]
                )

                for call in function_calls:
                    tool_name = call.get("name")
                    logger.info(
                        f"🔧 Gemini ejecutó herramienta "
                        f"'{tool_name}' "
                        f"para sesión {sid}"
                    )
                    # ==================================================
                    # DELEGAR AL HANDLER
                    # ==================================================
                    result = (
                        await handler.handle_tool_call(
                            call=call,
                            sio=sio,
                            sid=sid,
                        )
                    )

                    # Si el handler no reconoce
                    # la herramienta.
                    if result is None:
                        logger.warning(
                            f"El handler '{handler.name}' "
                            f"no procesó la herramienta "
                            f"'{tool_name}'"
                        )
                        continue
                    # ==================================================
                    # RESPONDER A GEMINI
                    # ==================================================

                    response_message = {
                        "toolResponse": {
                            "functionResponses": [
                                {
                                    "name": tool_name,
                                    "id": call["id"],
                                    "response": {
                                        "output": result
                                    },
                                }
                            ]
                        }
                    }

                    await gemini_ws.send(
                        json.dumps(
                            response_message
                        )
                    )

                    if handler.ends_session_after_tool_call:
                        logger.info(
                            f"🏁 Flujo '{handler.name}' completado "
                            f"para la sesión {sid}"
                        )

                        try:
                            await gemini_ws.close()
                        except Exception as e:
                            logger.warning(
                                f"Error cerrando WebSocket de Gemini "
                                f"para {sid}: {str(e)}"
                            )

                        return

    except Exception as e:

        logger.error(
            f"Error o desconexión en el flujo "
            f"continuo de voz para {sid}: {str(e)}"
        )

    finally:

        # ==================================================
        # LIMPIAR SESIÓN
        # ==================================================

        session = client_sessions.pop(
            sid,
            None,
        )

        if not session:
            return

        ws = session["gemini_ws"]

        if ws:
            try:
                await ws.close()
            except Exception as e:
                logger.warning(
                    f"Error cerrando WebSocket de Gemini "
                    f"en cleanup para {sid}: {str(e)}"
                )