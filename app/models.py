from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DispatchStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DispatchCreate(BaseModel):
    origin: str = Field(min_length=1, max_length=500)
    destination: str = Field(min_length=1, max_length=500)

    @field_validator("origin", "destination")
    @classmethod
    def strip_address(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Address must not be blank")
        return value


class DispatchStatusUpdate(BaseModel):
    status: DispatchStatus


class DispatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin: str
    destination: str
    status: DispatchStatus
    created_at: datetime