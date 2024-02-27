from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.Routers import voices, chatbot, call, magic_script

import uvicorn

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(voices.router, prefix="/api/voices")
app.include_router(chatbot.router, prefix="/api/chatbots")
app.include_router(call.router)
app.include_router(magic_script.router, prefix="/api/magic")


@app.get("/")
async def health_checker():
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
