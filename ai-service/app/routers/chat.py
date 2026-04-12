"""Chat endpoints — placeholder, implemented in commit 12."""

from fastapi import APIRouter

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat_message():
    return {"message": "Chat endpoint — coming in commit 12"}


@router.post("/chat/stream")
async def chat_stream():
    return {"message": "Streaming endpoint — coming in commit 12"}
