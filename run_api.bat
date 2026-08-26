@echo off
cd /d "D:\MicroservicesGitHub\ia-transcription-service"

call "C:\ProgramData\miniconda3\condabin\conda.bat"

call conda activate ia-transcription

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
