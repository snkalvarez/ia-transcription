FROM python:3.11-slim

# Evita archivos .pyc y fuerza salida inmediata de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Directorio de trabajo
WORKDIR /app

# Instalar FFmpeg (necesario para Faster Whisper)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libgomp1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Ejecutar la aplicación sin privilegios. El directorio home mantiene una
# caché escribible para la descarga inicial de los modelos de Whisper.
RUN useradd --create-home --uid 10001 appuser

# Copiar aplicación
COPY --chown=appuser:appuser app ./app

USER appuser

# Puerto del servicio
EXPOSE 8080

# Ejecutar FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
