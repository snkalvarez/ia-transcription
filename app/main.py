"""Punto de ensamblaje de la aplicación FastAPI."""
from contextlib import asynccontextmanager
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
import app.models.procesamiento_ia  # Registra modelos antes de crear las tablas.


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app

# 1. Crear la instancia de la aplicación FastAPI base usando tu fábrica funcional
fastapi_app = create_app()

# 2. Instanciar el servidor asíncrono de Socket.IO con soporte CORS heredado de tus settings
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=settings.cors_origins)

# 3. Combinar FastAPI y Socket.IO en una única aplicación ASGI unificada
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# 4. Registrar los manejadores de eventos asíncronos para el bot de voz clínica
# La importación se realiza aquí abajo para prevenir de manera estricta dependencias circulares
from app.api.routes import voice_live
voice_live.register_voice_events(sio)
