from faster_whisper import WhisperModel
from app.core.config import settings


class WhisperService:

    def __init__(self):

        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE
        )

    def transcribe_audio(self, file_path: str):

        segments, info = self.model.transcribe(
            file_path,
            language=settings.DEFAULT_LANGUAGE,
            vad_filter=settings.ENABLE_VAD_FILTER
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return {
            "language": info.language,
            "text": text
        }