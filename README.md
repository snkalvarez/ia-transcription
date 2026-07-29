# IA Transcription Service

API sencilla para transcribir archivos de audio a texto con **FastAPI** y
**Faster-Whisper**. Recibe un archivo mediante `multipart/form-data` y devuelve
el texto transcrito junto con el idioma detectado.

## Características

- Transcripción de audio con Faster-Whisper.
- Transcripción configurada actualmente para español.
- Detección de actividad de voz (`vad_filter`) para omitir silencios.
- Documentación interactiva incluida mediante Swagger UI.
- CORS habilitado para `http://localhost:5173`.

## Requisitos

- Python 3.11 o superior.
- Memoria y capacidad de cómputo suficientes para el modelo seleccionado.
  La configuración predeterminada usa el modelo `small` en CPU.

> La primera ejecución descarga el modelo de Whisper seleccionado, por lo que
> requiere conexión a Internet y puede tardar unos minutos.

## Instalación

Clone el repositorio y cree un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale las dependencias del proyecto y las necesarias para ejecutar FastAPI
con carga de archivos:

```powershell
pip install -r requirements.txt
pip install uvicorn pydantic-settings python-multipart
```

En macOS o Linux, active el entorno con:

```bash
source .venv/bin/activate
```

## Configuración

La API admite las siguientes variables de entorno. Si no se especifican, usa
los valores predeterminados mostrados:

| Variable | Predeterminado | Descripción |
| --- | --- | --- |
| `WHISPER_MODEL` | `small` | Modelo de Faster-Whisper que se cargará. |
| `DEVICE` | `cpu` | Dispositivo de ejecución, por ejemplo `cpu` o `cuda`. |
| `COMPUTE_TYPE` | `int8` | Precisión de cálculo, por ejemplo `int8`, `float16` o `float32`. |

Ejemplo para PowerShell:

```powershell
$env:WHISPER_MODEL = "base"
$env:DEVICE = "cpu"
$env:COMPUTE_TYPE = "int8"
```

Para usar GPU NVIDIA, configure un entorno compatible con CUDA y ajuste
`DEVICE=cuda` junto con un `COMPUTE_TYPE` compatible, por ejemplo `float16`.

## Ejecutar la API

Desde la raíz del repositorio:

```powershell
uvicorn app.main:app --reload
```

El servicio estará disponible en `http://127.0.0.1:8000`.

- Documentación Swagger: `http://127.0.0.1:8000/docs`
- Documentación ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### Estado del servicio

```http
GET /
```

Respuesta:

```json
{
  "status": "ok",
  "service": "IA Transcription Service"
}
```

### Transcribir un audio

```http
POST /transcribe
Content-Type: multipart/form-data
```

Parámetros:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| `file` | Archivo | Sí | Archivo de audio que se desea transcribir. |

Ejemplo con `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.webm"
```

Ejemplo con PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/transcribe" `
  -Method Post `
  -Form @{ file = Get-Item ".\audio.webm" }
```

Respuesta exitosa:

```json
{
  "language": "es",
  "text": "Texto transcrito del archivo de audio."
}
```

## Estructura del proyecto

```text
app/
├── core/
│   └── config.py                 # Variables de configuración
├── services/
│   ├── transcription_service.py  # Orquestación de la transcripción
│   └── whisper_service.py        # Integración con Faster-Whisper
└── main.py                       # Aplicación y rutas FastAPI
```

## Notas

- El idioma se solicita como español (`language="es"`) en el servicio de
  Whisper.
- El archivo se guarda temporalmente durante la transcripción y se elimina al
  finalizar la solicitud.
- El tiempo de respuesta depende de la duración del audio, el modelo elegido y
  el hardware disponible.
