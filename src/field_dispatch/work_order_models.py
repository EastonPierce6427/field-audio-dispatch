from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class DispatchStatus(StrEnum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    NEEDS_FOLLOW_UP = "needs_follow_up"
    READY_TO_CLOSE = "ready_to_close"


class WorkOrderAudio(BaseModel):
    work_order_id: str = Field(min_length=1)
    technician_id: str = Field(min_length=1)
    dispatch_status: DispatchStatus
    audio_base64: str = Field(min_length=1)
    audio_format: Literal["wav", "mp3"]
    photo_urls: list[HttpUrl] = Field(default_factory=list, max_length=4)


class FieldNote(BaseModel):
    transcript: str
    summary: str
    urgency: Literal["routine", "urgent"]
    blocker: bool
    follow_up_note: str


class DispatchResult(BaseModel):
    work_order_id: str
    transcript: str
    summary: str
    previous_status: DispatchStatus
    next_status: DispatchStatus
    technician_follow_up: str | None
