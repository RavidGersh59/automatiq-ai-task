# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from auth_agent import run_auth_agent
from rag_agent import run_rag_agent

# FastAPI app
app = FastAPI()

# Conversation store per user
conversations_store = {}  # supports multiple users in parallel

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# AUTH ENDPOINT

class AuthRequest(BaseModel):
    message: str
    user_info: dict
    system_last_message: str

@app.post("/auth")
def auth(req: AuthRequest):
    system_msg, updated_info, done = run_auth_agent(
        req.message,
        req.user_info,
        req.system_last_message
    )

    if done:
        # Initialize conversation for this user
        conversations_store[updated_info["id"]] = []

    return {
        "user_info": updated_info,
        "system_last_message": system_msg,
        "authenticated": done
    }


# RAG ENDPOINT

class RagRequest(BaseModel):
    user_info: dict
    user_message: str

@app.post("/rag")
def rag(req: RagRequest):
    user_id = req.user_info.get("id")

    if user_id is None:
        return {"error": "Missing user ID!"}

    # Initialize if not exist
    if user_id not in conversations_store:
        conversations_store[user_id] = []

    conversation = conversations_store[user_id]

    user_message, updated_conversation, system_reply = run_rag_agent(
        req.user_info,
        req.user_message,
        conversation
    )

    # save conversation
    conversations_store[user_id] = updated_conversation

    return {
        "system_reply": system_reply
    }


# RESET ENDPOINT - reset chat history during the conversation itself

class ResetRequest(BaseModel):
    user_id: str

@app.post("/reset")
def reset(req: ResetRequest):
    if req.user_id in conversations_store:
        del conversations_store[req.user_id]

    return {"status": "conversation reset"}


@app.get("/")
def root():
    return {"status": "backend running"}
