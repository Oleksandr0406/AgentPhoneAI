from fastapi import APIRouter, UploadFile, File

import requests
import json
import aiofiles
import openai
from config import settings

router = APIRouter()


@router.get("/")
async def get_voices():
    headers = {
        "accept": "application/json",
        "AUTHORIZATION": settings.PLAY_HT_SECRET_KEY,
        "X-USER-ID": settings.PLAY_HT_USER_ID,
    }
    response = requests.get("https://play.ht/api/v2/voices", headers=headers)
    voices = json.loads(response.text)
    en_voices = [voice for voice in voices if voice["language_code"] == "en-US"]
    print(en_voices)
    return {"voices": en_voices}


@router.post("/transcript")
async def get_transcript(audio: UploadFile = File(...)):
    async with aiofiles.open("./static/audios/temp.mp3", "wb") as out_file:
        while content := await audio.read(1024):
            await out_file.write(content)
    audio_file = open("./static/audios/temp.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return {"status": "success", "data": transcript["text"]}
