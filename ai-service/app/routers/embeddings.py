"""Embedding management endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["embeddings"])


@router.post("/embeddings/generate")
async def generate_embeddings():
    return {"message": "Embedding generation endpoint — coming in commit 12"}


@router.post("/embeddings/reindex")
async def reindex():
    return {"message": "Reindex endpoint — coming in commit 12"}
