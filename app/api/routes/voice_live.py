import json
import base64
import asyncio
import jwt
from app.services.gemini_live_service import GeminiLiveService
from app.core.logger import logger
from app.core.config import settings

# Almacenamiento en memoria para rastrear las conexiones de los clientes
client_sessions = {}
gemini_service = GeminiLiveService()

def register_voice_events(sio):
    
    @sio.event
    async def connect(sid, environ, auth=None):
        token = (auth or {}).get("token")
        if settings.JWT_SECRET:
            try:
                if not token:
                    return False
                jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            except jwt.PyJWTError:
                logger.warning("Socket.IO connection rejected: missing or invalid JWT")
                return False

        logger.info(f"🩺 Médico conectado vía Socket.IO (Session ID: {sid})")
        try:
            # Inicializar la llamada con Google AI Studio desde el servicio
            gemini_ws = await gemini_service.iniciar_sesion_gemini()
            client_sessions[sid] = gemini_ws
            
            # Lanzar tarea de fondo para procesar lo que Gemini nos hable
            asyncio.create_task(listen_to_gemini_stream(sid, gemini_ws, sio))
            
        except Exception as e:
            logger.error(f"Error al enlazar sesión de voz con Gemini: {str(e)}")
            await sio.disconnect(sid)

    @sio.event
    async def audio_chunk(sid, data):
        """Transmite el chunk binario que llega de React hacia Gemini"""
        gemini_ws = client_sessions.get(sid)
        
        # AGREGAMOS VALIDACIÓN: Solo enviar si el WebSocket existe y está abierto
        if gemini_ws and hasattr(gemini_ws, 'open') and gemini_ws.open:
            await gemini_service.enviar_audio_chunk(gemini_ws, data)

    @sio.event
    async def disconnect(sid):
        logger.info(f"🔴 Sesión de voz finalizada para el cliente {sid}")
        gemini_ws = client_sessions.pop(sid, None)
        if gemini_ws:
            await gemini_ws.close()


async def listen_to_gemini_stream(sid, gemini_ws, sio):
    """Escucha la respuesta de Gemini, envía audio a React o retorna el SOAP al completarse"""
    try:
        async for response in gemini_ws:
            data = json.loads(response)
            
            # CASO A: Nos está llegando la respuesta hablada de la IA (Audio nativo)
            if "serverContent" in data and "modelTurn" in data["serverContent"]:
                parts = data["serverContent"]["modelTurn"]["parts"]
                for part in parts:
                    if "inlineData" in part and "data" in part["inlineData"]:
                        audio_bytes = base64.b64decode(part["inlineData"]["data"])
                        # Retransmitir audio crudo al altavoz del Front-end en React
                        await sio.emit('audio_response', audio_bytes, to=sid)

            # CASO B: Formato SOAP completado por voz. Gemini dispara la herramienta estructurada
            elif "toolCall" in data:
                function_calls = data["toolCall"]["functionCalls"]
                for call in function_calls:
                    if call["name"] == "guardar_evolucion_soap":
                        extracted_soap = call["args"]
                        
                        logger.info(f"💥 ¡Evolución SOAP completa extraída exitosamente para {sid}!")
                        logger.info(json.dumps(extracted_soap, indent=2, ensure_ascii=False))
                        
                        # Enviar el JSON limpio estructurado de vuelta a React para tu interfaz web
                        await sio.emit('soap_result', extracted_soap, to=sid)
                        
                        # Responder a Gemini satisfactoriamente para cerrar el ciclo del Tool de Google
                        response_message = {
                            "toolResponse": {
                                "functionResponses": [{
                                    "name": "guardar_evolucion_soap",
                                    "id": call["id"],
                                    "response": {"output": {"success": True}}
                                }]
                            }
                        }
                        await gemini_ws.send(json.dumps(response_message))
                        
    except Exception as e:
        logger.error(f"Error o desconexión en el flujo continuo de voz para {sid}: {str(e)}")
    finally:
        gemini_ws = client_sessions.pop(sid, None)
        if gemini_ws:
            await gemini_ws.close()
