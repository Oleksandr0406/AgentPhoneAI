from pydantic import BaseModel
from fastapi import APIRouter, Request, Form, Response
from typing import Optional
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
import json
import uvicorn
import openai
import os
import random
from dotenv import load_dotenv
import urllib.request
import asyncio
from urllib.parse import urljoin

load_dotenv()

router = APIRouter()
openai.api_key = os.getenv("OPENAI_API_KEY")


async def transcribe(recording_url):
    hash = str(random.getrandbits(32))
    try:
        urllib.request.urlretrieve(recording_url, hash + ".wav")
    except:
        return None

    audio_file = open(hash + ".wav", "rb")
    transcript = await openai.Audio.atranscribe("whisper-1", audio_file)

    os.remove(hash + ".wav")
    return transcript


@router.get("/make-call/{phoneNumber}")
def make_call(request: Request, phoneNumber: str):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    phoneNumber = phoneNumber.strip()
    print(phoneNumber)
    print(request.base_url)
    call = client.calls.create(
        url=urljoin(str(request.base_url), "/gather"),
        method="POST",
        to=phoneNumber,
        from_=twilio_number
    )
    print(call.sid)

@router.post("/gather")
async def gather_response(request: Request):
    data = await request.form()
    response = VoiceResponse()
    print("enter gather")
    # Check if we have a SpeechResult from the caller
    speech_result = data.get('SpeechResult', '').strip()

    if speech_result:
        print("here")
        # If there is a SpeechResult, process it in the /process_speech endpoint
        return await process_speech(request)
    else:
        # If there is no SpeechResult, this is the first time the caller is being prompted
        # response.say("enter goldrace")
        gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
        gather.say("Hello! Thank you for answering a call. How can I assist you today? If you have any questions, please tell me your response after the beep.")
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")

@router.post("/process_speech")
async def process_speech(request: Request):
    data = await request.form()
    speech_result = data.get('SpeechResult', '').strip()
    print("process enter")
    print("speech_result: ", speech_result)
    response = VoiceResponse()
    if speech_result:
        print(speech_result)
        messages = []
        messages.append({"role": "system", "content": "Whenver you answer to user's question, you should answer with one sentence that is not too long.(about 15 words)"})
        messages.append({"role": "user", "content": speech_result})
        openai_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        reply = openai_response.choices[0].message.content
        response.say(reply)
        print("reply: ", reply)
        gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
        response.append(gather)
        
    else:
        response.say("Ok. It's goldrace's openai test.")
        # response.say("I didn't catch that. Please tell me your response after the beep.")
        # Set up a new Gather to re-prompt the caller
        gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")

# @router.post("/process_speech")
# async def process_speech(request: Request):
#     data = await request.form()
#     speech_result = data.get('SpeechResult', '').strip()

#     response = VoiceResponse()
#     if speech_result:
#         # Process the caller's spoken response here
#         # For example, let's assume you want to continue the conversation if the caller says "continue"
#         if 'continue' in speech_result.lower():
#             response.say("You said continue. What else would you like to say?")
#             # Set up a new Gather to continue the conversation
#             gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
#             response.append(gather)
#         else:
#             response.say(f"You said: {speech_result}. If you want to continue talking, say 'continue'.")
#             # Set up a new Gather in case the caller wants to continue
#             gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
#             response.append(gather)
#     else:
#         response.say("I didn't catch that. Please tell me your response after the beep.")
#         # Set up a new Gather to re-prompt the caller
#         gather = Gather(input='speech', action='/process_speech', method='POST', speechTimeout='auto')
#         response.append(gather)

#     return Response(content=str(response), media_type="application/xml")



"""
@router.get("/test")
def test(request: Request):
    print(request.query_params.get("To"))


@router.get("/greeting-gather")
def greeting_gather(request: Request):
    print(request.query_params.get("To"))
    Digits = request.query_params.get("Digits")
    if Digits == "1":
        response = VoiceResponse()
        response.say("I'm the Story Quilt bot and I'm here to record a story. I'll ask you ten questions about the story and record your answers. After you tell me the story I'll see if I understand what you told me and ask some clarifying questions. Okay, let's get started.")
        response.redirect("/question/0", method='GET')
        return Response(content=str(response), media_type="application/xml")
    else:
        response = VoiceResponse()
        response.redirect("/finish-without-answer", method='GET')
        return Response(content=str(response), media_type="application/xml")


@router.get("/finish-without-answer")
def finish_without_answer(request: Request):
    response = VoiceResponse()
    response.say("Thank you. Please have a nice day.")
    response.hangup()
    return Response(content=str(response), media_type="application/xml")


@router.get("/question/{questionIndex}")
def question(request: Request, questionIndex: int):
    _to = request.query_params.get("To")
    with open(f"./data/{_to}_question.json", "r") as f:
        questions = json.loads(f.read())

    response = VoiceResponse()
    response.say(questions[questionIndex])
    response.record(action=f"/recording/{questionIndex}",
                    questionIndex=questionIndex, finish_on_key="*", method="GET", timeout=10)
    # response.redirect(f"/question/{questionIndex + 1}", method='GET')
    return Response(content=str(response), media_type="application/xml")
  
"""