import base64
import json
from pathlib import Path

from field_dispatch.audio_dispatcher import AudioDispatcher
from field_dispatch.work_order_models import DispatchStatus, WorkOrderAudio


def main() -> None:
    audio_path = Path("technician-note.wav")
    request = WorkOrderAudio(
        work_order_id="WO-1842",
        technician_id="tech-17",
        dispatch_status=DispatchStatus.IN_PROGRESS,
        audio_base64=base64.b64encode(audio_path.read_bytes()).decode("ascii"),
        audio_format="wav",
        photo_urls=[],
    )
    result = AudioDispatcher().transcribe_and_route(request)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
