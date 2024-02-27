from fastapi import APIRouter, UploadFile, File, Form
import requests
import json
import aiofiles
import openai
import shutil
from config import settings
from elevenlabs import clone
from elevenlabs import set_api_key

set_api_key(settings.ELEVENLABS_API_KEY)

router = APIRouter()


@router.get("/")
async def get_voices():
    """
    Retrieve a list of available voices from ElevenLabs API.
    """
    url = "https://api.elevenlabs.io/v1/voices"
    response = requests.get(url)
    return response.json()

@router.post("/transcript")
async def get_transcript(audio: UploadFile = File(...)):
    """
    Transcribe the provided audio file using OpenAI's Whisper model.
    """
    temp_audio_path = "./static/audios/temp.mp3"
    async with aiofiles.open(temp_audio_path, "wb") as out_file:
        # Write the content of the audio file in chunks to prevent memory overflow
        while content := await audio.read(1024):
            await out_file.write(content)
    
    with open(temp_audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    
    # Remove the temporary audio file after processing
    os.remove(temp_audio_path)
    
    return {"status": "success", "data": transcript["text"]}

@router.post("/voice-clone")
async def voice_clone(file: UploadFile = Form(...), voice_name: str = Form(...)):
    """
    Clone a voice using the provided audio file and voice name.
    This endpoint requires a paid ElevenLabs API key.
    """
    file_path = f"./data/{file.filename}"
    with open(file_path, "wb") as buffer:
        # Directly use the file-like object from the request to save to disk
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Clone the voice using ElevenLabs API
        voice = clone(
            name=voice_name,
            files=[file_path]
        )
        print(voice)
    finally:
        # Clean up the temporary file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Return the result or handle errors accordingly
    return {"status": "success", "data": voice}