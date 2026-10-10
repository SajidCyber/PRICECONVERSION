"""Standard Common Schemas for API Envelopes, Metadata, and Health."""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class MetaInfo(BaseModel):
    total: int = Field(..., description="Total available records matching query")
    limit: int = Field(20, description="Page size limit")
    offset: int = Field(0, description="Page offset")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT
    meta: Optional[MetaInfo] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class HealthStatus(BaseModel):
    app_name: str
    version: str
    environment: str
    database_connected: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
