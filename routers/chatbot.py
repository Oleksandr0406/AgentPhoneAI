from fastapi import APIRouter, UploadFile, File, Body, HTTPException, status
import aiofiles
import json
import openai
import requests
import time
from serializers import chatbot_entity, chatbot_details_entity
from utils import generate_filename, generate_slug
from database import Chatbots
from config import settings
import base64

openai.api_key = settings.OPENAI_API_KEY
router = APIRouter()


@router.post("/", tags=["Chatbot"])
async def create_chatbot(
    scenario: str = Body(...),
    image: UploadFile = File(...),
    role_play_system_prompt: str = Body(...),
    guide_system_prompt: str = Body(...),
    person_details: str = Body(...),
    person_voices: str = Body(...),
):
    list_person_details = json.loads(person_details)
    list_person_voices = json.loads(person_voices)
    slug = generate_slug(scenario)

    is_existing = Chatbots.find_one({"slug": slug})
    if is_existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is exising scenario about this kind of chatbot.",
        )

    generated_name = generate_filename(image.filename)
    destination_file_path = f"./static/images/{generated_name}"
    async with aiofiles.open(destination_file_path, "wb") as out_file:
        while content := await image.read(1024):
            await out_file.write(content)
    Chatbots.insert_one(
        {
            "scenario": scenario,
            "image": generated_name,
            "role_play_system_prompt": role_play_system_prompt,
            "guide_system_prompt": guide_system_prompt,
            "person_details": list_person_details,
            "person_voices": list_person_voices,
            "slug": slug,
        }
    )
    return {"status": "success", "message": "Chatbot created successfully!"}


@router.get("/", tags=["Chatbot"])
async def get_chatbot_list():
    chatbots = Chatbots.find({})
    chatbot_list = [chatbot_entity(bot) for bot in chatbots]
    return {"status": "success", "data": list(chatbot_list)}


@router.get("/{slug}", tags=["Chatbot"])
async def get_chatbot_by_slug(slug: str):
    chatbot = Chatbots.find_one({"slug": slug})
    return {"status": "success", "data": chatbot_details_entity(chatbot)}

# @router.post("/{slug}/init-chat", tags=["Chatbot"])
# async def chat(slug: str, msg: list = Body(embed=True)):

@router.post("/{slug}/chat", tags=["Chatbot"])
async def chat(slug: str, msg: list = Body(embed=True)):
    chatbot = Chatbots.find_one({"slug": slug})
    messages = []
    messages.append({"role": "system", "content": chatbot["role_play_system_prompt"] + '\n' + chatbot["guide_system_prompt"] + "When you answer or ask questions, you have to say the sentence with less than 20 words."})
    for item in msg:
        messages.append({"role": item["type"], "content": item["text"]})
    print(chatbot["guide_system_prompt"])
    if len(msg) == 0:
        messages.append({"role": "user", "content": 'Please try instructions one by one.'})
    start_time = time.time()  
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    reply = response.choices[0].message.content
    
    
    current_time = time.time()
    print(current_time - start_time)
    # url = "https://play.ht/api/v2/tts"

    # start_time = time.time()
    
    # payload = {
    #     "text": reply,
    #     "voice": "larry",
    #     "quality": "medium",
    #     "output_format": "mp3",
    #     "speed": 1,
    #     "sample_rate": 24000,
    #     "voice_engine": "PlayHT1.0",
    # }
    # headers = {
    #     "accept": "text/event-stream",
    #     "content-type": "application/json",
    #     "AUTHORIZATION": settings.PLAY_HT_SECRET_KEY,
    #     "X-USER-ID": settings.PLAY_HT_USER_ID,
    # }

    # response = requests.post(url, json=payload, headers=headers, stream=True)
    # print(response.text)
    # lines = response.text.split("\n")
    # lines = filter(None, lines)
    # events = []
    # for line in lines:
    #     if line.startswith("data:"):
    #         if "{" in line:
    #             event = json.loads(line.replace("data: ", ""))
    #             events.append(event)
    # url = events[len(events) - 1]["url"]
    # print(url)
    
    # return {"status": "success", "data": {"msg": reply, "audioBase64": url}}
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    CHUNK_SIZE = 25
    api_key = "def7138943e286ec6df4843ce41c303b"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    print(reply)
    data = {
        "text": reply,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    response = requests.post(url, json=data, headers=headers)
    print(response)
    print(base64.b64encode(response.content).decode('utf-8'))
    # with open('output.mp3', 'wb') as f:
    #     for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
    #         if chunk:
    #             print(chunk)
    #             f.write(chunk)
    current_time = time.time()
    print(current_time - start_time)
    return {"status": "success", "data": {"msg": reply, "audioBase64": base64.b64encode(response.content).decode('utf-8')}}
    # return base64.b64encode(response.content).decode('utf-8')
    
