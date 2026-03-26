from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.classified_vault import get_classified_vault_service

logger = logging.getLogger("classified_api")
router = APIRouter()


class ClassifiedIngestPayload(BaseModel):
    source_id: str = Field(..., min_length=2, max_length=120)
    classification: str = Field(default="CONFIDENTIAL", min_length=3, max_length=64)
    text: str = Field(..., min_length=5)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClassifiedQueryPayload(BaseModel):
    query: str = Field(..., min_length=2)
    classification: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


@router.get("/status")
async def get_classified_status():
    service = get_classified_vault_service()
    try:
        return {"status": "success", "data": service.get_status()}
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/ingest")
async def ingest_classified_data(payload: ClassifiedIngestPayload):
    service = get_classified_vault_service()
    try:
        result = service.ingest(
            source_id=payload.source_id,
            classification=payload.classification,
            text=payload.text,
            tags=payload.tags,
            metadata=payload.metadata,
        )
        return {
            "status": "success",
            "message": "Classified payload stored in local encrypted vault.",
            "data": result,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/query")
async def query_classified_data(payload: ClassifiedQueryPayload):
    service = get_classified_vault_service()
    try:
        result = service.query(
            query_text=payload.query,
            classification=payload.classification,
            tags=payload.tags,
            top_k=payload.top_k,
        )
        return {"status": "success", "data": result}
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.delete("/record/{record_id}")
async def delete_classified_record(record_id: str):
    service = get_classified_vault_service()
    try:
        deleted = service.delete_record(record_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="Classified record not found.")

    return {
        "status": "success",
        "message": f"Deleted classified record {record_id}.",
    }


@router.delete("/records")
async def purge_classified_records(source_id: Optional[str] = None):
    service = get_classified_vault_service()
    try:
        deleted_count = service.purge(source_id=source_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Classified vault purge completed.",
        "deleted": deleted_count,
        "source_id": source_id,
    }
