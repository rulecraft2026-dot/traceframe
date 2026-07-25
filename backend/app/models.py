from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1536x1024"
    quality: Literal["low", "medium", "high", "auto"] = "medium"


class ReplayRequest(BaseModel):
    prompt_override: str | None = Field(default=None, min_length=3, max_length=4000)


class ProvenanceRecord(BaseModel):
    id: str
    parent_id: str | None = None
    prompt: str
    provider: str
    model: str
    params: dict[str, Any]
    status: Literal["running", "completed", "failed"]
    created_at: datetime
    completed_at: datetime | None = None
    asset_url: str | None = None
    asset_sha256: str | None = None
    manifest_sha256: str | None = None
    manifest_url: str | None = None
    error: str | None = None
    replayable: bool = True


class HealthResponse(BaseModel):
    status: str
    mode: str
    storage: str
