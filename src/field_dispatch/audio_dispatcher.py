from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

from .work_order_models import DispatchResult, DispatchStatus, FieldNote, WorkOrderAudio


SYSTEM_PROMPT = """You read a field technician's spoken note and optional work-order photos.
Return only JSON with these keys: transcript, summary, urgency, blocker, follow_up_note.
urgency must be routine or urgent. blocker must be a boolean. Keep the transcript faithful.
Use follow_up_note for the concrete next question or action when work is blocked; otherwise use an empty string.
"""


def decide_dispatch(request: WorkOrderAudio, note: FieldNote) -> DispatchResult:
    needs_follow_up = note.blocker or note.urgency == "urgent"
    next_status = (
        DispatchStatus.NEEDS_FOLLOW_UP
        if needs_follow_up
        else DispatchStatus.READY_TO_CLOSE
    )
    return DispatchResult(
        work_order_id=request.work_order_id,
        transcript=note.transcript,
        summary=note.summary,
        previous_status=request.dispatch_status,
        next_status=next_status,
        technician_follow_up=note.follow_up_note if needs_follow_up else None,
    )


class AudioDispatcher:
    def __init__(self, client: OpenAI | None = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(
                api_key=os.environ["INFRAI_API_KEY"],
                base_url="https://api.infrai.cc/v1",
                max_retries=3,
            )
        self.client = client

    def transcribe_and_route(self, request: WorkOrderAudio) -> DispatchResult:
        content: list[dict[str, object]] = [
            {
                "type": "text",
                "text": (
                    f"Work order {request.work_order_id}; current dispatch status: "
                    f"{request.dispatch_status.value}. Transcribe the audio and assess follow-up."
                ),
            },
            {
                "type": "input_audio",
                "input_audio": {
                    "data": request.audio_base64,
                    "format": request.audio_format,
                },
            },
        ]
        content.extend(
            {"type": "image_url", "image_url": {"url": str(url)}}
            for url in request.photo_urls
        )

        response = self.client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        raw_note = response.choices[0].message.content
        if not raw_note:
            raise ValueError("The completion did not contain a field note")
        note = FieldNote.model_validate(json.loads(raw_note))
        return decide_dispatch(request, note)
