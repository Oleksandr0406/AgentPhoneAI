from pydantic import BaseModel
from app.database import db
from typing import List

ChatlogsDB = db.chatlogs

# Define a Pydantic model for a message
class Message(BaseModel):
    content: str
    role: str
    
# Define a Pydantic model for a chat log
class Chatlog(BaseModel):
    logId: str  # Unique identifier for the chat log
    messages: List[Message] = []  # A list of messages in the chat log


# Function to delete a chat log from the database by its ID
def delete_summary_db_id(logId: str):
    ChatlogsDB.delete_one({"logId": logId})

# Function to find messages by chat log ID
def find_messages_by_id(logId: str):
    result = ChatlogsDB.find_one({"logId": logId})
    if result is None:  # Use `is None` for comparison with None
        return []
    return Chatlog(**result).messages  # Deserialize the database result into a Chatlog object and return its messages



# Function to add a new message to a chat log
def add_new_message(logId: str, msg: Message):
    result = ChatlogsDB.find_one({"logId": logId})
    if result:
        # If a chat log with the given logId exists, append the new message to the existing messages list
        ChatlogsDB.update_one({"logId": logId}, {
            "$push": {
                "messages": msg.dict()  # Serialize the Message object to a dictionary before pushing to the array
            }
        })
    else:
        # If a chat log with the given logId doesn't exist, create a new Chatlog object and save it to the database
        new_chatlog = Chatlog(
            logId=logId,
            messages=[msg]
        )
        ChatlogsDB.insert_one(new_chatlog.dict())  # Serialize the Chatlog object to a dictionary before inserting