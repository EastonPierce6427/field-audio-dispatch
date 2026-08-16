from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError

from .audio_dispatcher import AudioDispatcher
from .work_order_models import DispatchResult, WorkOrderAudio

service = FastAPI(title="Field audio dispatch")


@service.post("/work-orders/transcribe", response_model=DispatchResult)
def transcribe_work_order(request: WorkOrderAudio) -> DispatchResult:
    try:
        return AudioDispatcher().transcribe_and_route(request)
    except APIStatusError as exc:
        detail = exc.body if isinstance(exc.body, dict) else {"message": str(exc)}
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="AI service connection failed") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed") from exc
