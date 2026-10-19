import json
import base64
import asyncio
from copy import deepcopy
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
        numero_ingreso = str(
            auth.get("numero_ingreso", "")
        ).strip()
        user_name = str(
            auth.get("user_name", "")
        ).strip()

        if voice_type == "formulario_hc_14" and not numero_ingreso:
            logger.warning(
                "Socket.IO connection rejected: "
                "missing admission number for HC14"
            )
            return False

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
                "numero_ingreso": numero_ingreso,
                "user_name": user_name,
                "form_draft": {},
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

            await gemini_service.enviar_texto(
                gemini_ws,
                (
                    "Inicia la conversación saludando cordialmente al médico "
                    f"por su nombre ({user_name}) y preguntándole cómo puedes "
                    "ayudarle a diligenciar el formulario."
                    if user_name
                    else
                    "Inicia la conversación saludando cordialmente al médico "
                    "y preguntándole cómo puedes ayudarle a diligenciar el formulario."
                ),
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
                    session = client_sessions.get(sid, {})
                    call_for_handler = call

                    if tool_name == "guardar_formulario_hc_14":
                        final_data = merge_form_data(
                            session.get("form_draft", {}),
                            call.get("args") or {},
                        )
                        session["form_draft"] = final_data
                        call_for_handler = {
                            **call,
                            "args": final_data,
                        }

                    if tool_name == "actualizar_formulario_hc_14":
                        session["form_draft"] = merge_form_data(
                            session.get("form_draft", {}),
                            call.get("args") or {},
                        )
                        await sio.emit(
                            "voice_form_update",
                            session["form_draft"],
                            to=sid,
                        )

                    result = (
                        await handler.handle_tool_call(
                            call=call_for_handler,
                            sio=sio,
                            sid=sid,
                            numero_ingreso=session.get("numero_ingreso"),
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

                    if handler.should_end_session_after_tool_call(tool_name):
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

        if session is not None:
            ws = session["gemini_ws"]

            if ws:
                try:
                    await ws.close()
                except Exception as e:
                    logger.warning(
                        f"Error cerrando WebSocket de Gemini "
                        f"en cleanup para {sid}: {str(e)}"
                    )


def merge_form_data(current: dict, update: dict) -> dict:
    """Combina actualizaciones parciales sin perder objetos anidados."""
    merged = deepcopy(current)

    for key, value in update.items():
        if (
            isinstance(value, dict)
            and isinstance(merged.get(key), dict)
        ):
            merged[key] = merge_form_data(merged[key], value)
        else:
            merged[key] = deepcopy(value)

    return merged