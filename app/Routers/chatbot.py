from fastapi import APIRouter, UploadFile, File, Body, HTTPException, status, Form
import aiofiles
import json
import openai
import requests
import time
from app.serializers import chatbot_entity, chatbot_details_entity
from app.Utils.utils import generate_filename, generate_slug
from app.Utils.pinecone_util import train_csv, train_pdf, train_txt, train_ms_word, train_url
from app.database import Chatbots
from config import settings
import base64
import os
import shutil


openai.api_key = settings.OPENAI_API_KEY
router = APIRouter()

supported_file_extensions = [".csv", ".pdf", ".txt", ".doc", ".docx"]

@router.post("/", tags=["Chatbot"])
async def create_chatbot(
    scenario: str = Body(...),
    image: UploadFile = File(...),
    role_play_system_prompt: str = Body(...),
    guide_system_prompt: str = Body(...),
    person_details: str = Body(...),
    person_voices: str = Body(...),
):
    """
    Create a new chatbot with the given parameters.
    The image is saved to the server and information about the chatbot is stored in the database.
    """
    
    # Parse JSON strings into Python lists
    list_person_details = json.loads(person_details)
    list_person_voices = json.loads(person_voices)
    slug = generate_slug(scenario)

    # Check if a chatbot with the same slug already exists
    is_existing = Chatbots.find_one({"slug": slug})
    if is_existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A chatbot with the given scenario already exists.",
        )
        
    # Save the image file to the server
    generated_name = generate_filename(image.filename)
    destination_file_path = f"./static/images/{generated_name}"
    async with aiofiles.open(destination_file_path, "wb") as out_file:
        while content := await image.read(1024):
            await out_file.write(content)
            
    # Insert chatbot information into the database
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


@router.post("/{slug}/chat", tags=["Chatbot"])
async def chat(slug: str, msg: list = Body(embed=True)):
    """
    Handle a chat session with a chatbot identified by the slug.
    The messages are processed by the OpenAI API and a response is generated.
    """
    chatbot = Chatbots.find_one({"slug": slug})
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chatbot with slug '{slug}' not found."
        )
        
    # Prepare the initial system messages
    messages = [
        {
            "role": "system",
            "content": f"{chatbot['role_play_system_prompt']}\n{chatbot['guide_system_prompt']}When you answer or ask questions, you have to say the sentence with less than 20 words."
        }
    ]
    
    # Append user messages
    for item in msg:
        messages.append({"role": item["type"], "content": item["text"]})
    if len(msg) == 0:
        messages.append({"role": "user", "content": 'Please try instructions one by one.'})
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    reply = response.choices[0].message.content
    
    
    # Convert the reply to speech using ElevenLabs API

    url = f"https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    api_key = settings.ELEVENLABS_API_KEY
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

    # Make the request to ElevenLabs and handle any potential errors
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Text-to-speech conversion failed: {e}"
        )

    # Encode the audio content to base64
    audio_base64 = base64.b64encode(response.content).decode('utf-8')
    
    return {
        "status": "success",
        "data": {
            "msg": reply,
            "audioBase64": audio_base64
        }
    }
    

@router.post("/{slug}/add-training-file")
def add_training_file_api(slug: str, file: UploadFile = File(...)):
    """
    Add a training file for the chatbot identified by the slug.
    The file is saved to the server and used to train the chatbot.
    """
     # Validate the file extension
    extension = os.path.splitext(file.filename)[1]
    if extension not in supported_file_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type!"
        )
    try:
        # Define the directory where training files will be stored
        directory = settings.TRAIN_DATA_DIRECTORY
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Save the training file to the server
        file_path = os.path.join(directory, f"{slug}-{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the training file based on its extension
        if extension == ".csv":
            train_csv(file_path, slug)
        elif extension == ".pdf":
            train_pdf(file_path, slug)
        elif extension == ".txt":
            train_txt(file_path, slug)
        elif extension in [".doc", ".docx"]:
            train_ms_word(file_path, slug)
        
        # Optionally, store information about the file in the database if needed
        # add_file(slug, file.filename)
        return {"status": "success", "message": "Training file added successfully!"}
        
    except Exception as e:
        # Log the exception details for debugging purposes
        print(f"Training error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the training file."
        )

@router.post("/{slug}/add-page")
def add_page_api(slug: str, url: str = Form(...)):
    """
    Add a webpage URL as training material for the chatbot identified by the slug.
    """
    try:
        # Optionally, store the webpage URL in the database if needed
        # add_page(slug, url)

        # Train the chatbot with the content from the provided URL
        train_url(url, slug)

        return {"status": "success", "message": "Page added successfully as training material!"}
    except Exception as e:
        # Log the exception details for debugging purposes
        print(f"Error adding page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding the page as training material."
        )