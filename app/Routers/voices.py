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
    url = "https://api.elevenlabs.io/v1/voices"
    response = requests.request("GET", url)
    return response.json()

@router.post("/transcript")
async def get_transcript(audio: UploadFile = File(...)):
    async with aiofiles.open("./static/audios/temp.mp3", "wb") as out_file:
        while content := await audio.read(1024):
            await out_file.write(content)
    audio_file = open("./static/audios/temp.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return {"status": "success", "data": transcript["text"]}

@router.post("/voice-clone") # To use this endpoint, you have to input paid elevenlabs api key
def voice_clone(file: UploadFile = Form(...), voice_name: str = Form(...)):
    with open(f"./data/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    voice = clone(
        name = voice_name,
        files = [f"./data/{file.filename}"]
    )
    print(voice)