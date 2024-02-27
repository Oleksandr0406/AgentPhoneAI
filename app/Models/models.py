from pydantic import BaseModel
from app.database import db
from typing import List
from bson import json_util
from bson.objectid import ObjectId
from datetime import date, datetime

ChatlogsDB = db.chatlogs

class Message(BaseModel):
    content: str
    role: str

class Chatlog(BaseModel):
    logId: str
    messages: List[Message] = []


def delete_summary_db_id(logId: str):
    ChatlogsDB.delete_one({"logId": logId})

def find_messages_by_id(logId: str):
    # ChatlogsDB.delete_one({"logId": logId})
    result = ChatlogsDB.find_one({"logId": logId})
    if result == None:
        return []
    return Chatlog(**result).messages


def add_new_message(logId: str, msg):
    result = ChatlogsDB.find_one({"logId": logId})
    # print(msg)
    if result:
        # If row with logId exists, append the new message to the existing messages list
        ChatlogsDB.update_one({"logId": logId}, {
            "$push": {
                "messages": msg.dict()
            }
        })
    else:
        # If row with logId doesn't exist, create a new Chatlog object and save it to the database
        new_chatlog = Chatlog(
            logId=logId,
            messages=[msg]
        )
        ChatlogsDB.insert_one(new_chatlog.dict())