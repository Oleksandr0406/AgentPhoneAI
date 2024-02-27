from fastapi import APIRouter, UploadFile, File, Body, HTTPException, status, Form
import aiofiles
import json
import openai
import requests
import time
from app.serializers import chatbot_entity, chatbot_details_entity
from app.Utils.utils import generate_filename, generate_slug
from app.database import Chatbots
from config import settings
import base64
import os
import shutil


openai.api_key = settings.OPENAI_API_KEY
router = APIRouter()

def transcript_audio_file(file_location):
    audio_file = open(file_location, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript.text

def generate_framwork(input: str):
    
    sample_framwork = """
        Yeah. It’s Alexander… from Air dot aiy eye? How's your day going so far?

        *Wait for the Prospect to Respond*

        Yeah. So it uh, it looks like you opted into one of our ads lookin' for information on how to scale your business using aiy eye. Is that something that you recall?

        *Wait for the Prospect to Respond*

        Ok, perfect. Well the reason I’m calling you is I’m actually a manager over here on Air’s client success team on a recorded line, and they give us about 3 to 5 minutes to check in with you, to see if there’s any way we can help you. And by the way, a few people have told me that the audio is a bit laggy today, so if I cut you off or if there’s like a, a bit of a delay, I apologize for that in advance. But yeah, anyways, I'm curious for you, what had you looking into using aiy eye to scale your business?

        *Wait for the Prospect to Respond*

        So, let’s say like everything went just perfectly, and you were using Air to scale a high-ticket business. How much money would you, actually wanna be making each month? like ideal outcome a year from now or so?

        *Wait for the Prospect to Respond*

        Roger that. Now, I’m just curious, why that number specifically? Like, what gets you excited about hitting that number?

        *Wait for the Prospect to Respond*

        Can you tell me more about that? Just expound a bit more.

        *Wait for the Prospect to Respond*

        Ok, now let me ask you this. What’s one word you’d use to describe how you’d feel hitting that number? For example, would it be freedom, excitement, relief, like whats that word for you?

        *Wait for the Prospect to Respond*

        Why [their word] specifically?

        *Wait for the Prospect to Respond*

        On a scale from, say like, 1 to 10... yknow, how much would you have that word [insert their word] at your ideal income?

        *Wait for the Prospect to Respond*

        Now, on the flip side here, on the same scale of uh 1 to 10 right. How much do you feel like you have that word currently?

        *Wait for the Prospect to Respond*

        Why so low?

        *Wait for the Prospect to Respond*

        Well based on our conversation, I have 2 resources for you that I think would really help you out… do you want me to send those to you?

        *Wait for the Prospect to Respond*

        The first one is a training on how we scaled to 4 million dollars a month, and the second is a free consulting call with one of our executive consultants to help you with the things we talked about. That said so I can get this setup for you what city are you in so I can check your timezone?

        *Wait for the Prospect to Respond*

        ok it looks like we have a [insert time from available times section in prompt] and a [insert another time from available times section in prompt], which time works best for you?

        *Wait for the Prospect to Respond*

        I’ll lock in that time for you. Also, I'm about to send you the training can you commit to watching it before your call since it’s vital to you both getting the most out of the complimentary consulting session.

        *Wait for the Prospect to Respond*

        And just to double check there’s no reason you would not show up right? Like you can one hundred percent make the call?

        *Wait for the Prospect to Respond*

        Ok good I just wanted to make sure because we do have a policy to charge a hundred dollar cancelation fee to protect our consultants time but it sounds like that won’t be relevant to you right?

        *Wait for the Prospect to Respond*

        Well I'm really excited to hear how you’re call goes and most importantly to see you get results. So that being said, everything is good to go over here. I hope you have an awesome rest of your day!
    """
    instructor =f"""
        Given the input text, your task is to generate a sequence of questions that a chatbot can use to engage the user in a meaningful conversation. The questions should be designed to follow the narrative of the input text, prompting the user to provide more details about the events, characters, and emotions expressed. Each question should be designed to naturally lead to the next, fostering a conversational flow.
        Towards the end of the conversation, steer the user towards a specific action or decision, which should be influenced by the context and narrative of the input text.
        In your framework, make sure to include placeholders for variables, denoted by brackets [], which will be filled in with the user's responses during the actual conversation. These variables could be related to any aspect of the conversation, such as options for activities, available booking times, user's preferences, or their selected date and time.
        Remember, the aim is to create a flexible and adaptable framework that can be applied to a variety of contexts and scenarios, not just the provided example. The prompts should be general enough to accommodate a wide range of narratives, while still being specific enough to guide a meaningful and engaging conversation.
        Below is the sample format you can output.
        
        Sample:
        {sample_framwork}
    """
    
    messages = [
        {"role": "system", "content": instructor},
        {"role": "user", "content": input + "\n---------\nPlease provide me framwork for above input."}
    ]
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    reply = response.choices[0].message.content
    return reply
    

@router.post("/{slug}/from_audio", tags=["Chatbot"])
def script_from_record(slug:str, record: UploadFile = Form(...)):
    UPLOAD_DIRECTORY = "./data"
    file_location = os.path.join(UPLOAD_DIRECTORY, record.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(record.file, buffer)
    transcript = transcript_audio_file(file_location)
    framwork = generate_framwork(transcript)
    return framwork
    

@router.post("/{slug}/from_text", tags=["Chatbot"])
def script_from_text(slug:str, text: str = Form(...)):
    framwork = generate_framwork(text)
    return framwork
    
