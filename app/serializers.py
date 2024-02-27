def chatbot_entity(chatbot) -> dict:
    return {
        "_id": str(chatbot["_id"]),
        "scenario": chatbot["scenario"],
        "image": chatbot["image"],
        "slug": chatbot["slug"]
    }

def chatbot_details_entity(chatbot) -> dict:
    return {
        "_id": str(chatbot["_id"]),
        "scenario": chatbot["scenario"],
        "image": chatbot["image"],
        "person_details": chatbot["person_details"]
    }