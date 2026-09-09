"""Constantes que no pertenecen a la configuración de entorno."""

ALLOWED_AUDIO_MIME_TYPES = frozenset({
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",  # Para archivos .mp3 comunes
    "audio/mp3",   # Variante de algunos navegadores/sistemas para .mp3
    "audio/mp4",   # Contenedor común en Apple (.m4a)
    "audio/x-m4a", # Variante muy común para .m4a en Safari
    "audio/webm;codecs=opus",
    "audio/ogg",
    "audio/aac",   # Grabaciones nativas de iOS
    "application/octet-stream" # Comodín cuando el cliente no logra identificar el tipo
})
