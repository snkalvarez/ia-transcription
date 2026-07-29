from app.services.whisper_service import WhisperService

class TranscriptionService:

    def __init__(self):
        self.whisper_service = WhisperService()

    def transcribe(self, file_path: str):

        return self.whisper_service.transcribe_audio(file_path)