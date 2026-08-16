from field_dispatch.audio_dispatcher import decide_dispatch
from field_dispatch.work_order_models import DispatchStatus, FieldNote, WorkOrderAudio


def test_blocked_job_requests_follow_up_instead_of_closing() -> None:
    request = WorkOrderAudio(
        work_order_id="WO-1842",
        technician_id="tech-17",
        dispatch_status=DispatchStatus.IN_PROGRESS,
        audio_base64="UklGRg==",
        audio_format="wav",
    )
    note = FieldNote(
        transcript="The replacement valve is the wrong size. Send a two-inch valve.",
        summary="Replacement valve does not fit.",
        urgency="routine",
        blocker=True,
        follow_up_note="Dispatch a two-inch replacement valve before the return visit.",
    )

    result = decide_dispatch(request, note)

    assert result.next_status is DispatchStatus.NEEDS_FOLLOW_UP
    assert result.technician_follow_up == (
        "Dispatch a two-inch replacement valve before the return visit."
    )


def test_completed_routine_job_is_ready_to_close() -> None:
    request = WorkOrderAudio(
        work_order_id="WO-1843",
        technician_id="tech-17",
        dispatch_status=DispatchStatus.IN_PROGRESS,
        audio_base64="UklGRg==",
        audio_format="wav",
    )
    note = FieldNote(
        transcript="Replaced the seal and verified normal pressure.",
        summary="Seal replaced and pressure verified.",
        urgency="routine",
        blocker=False,
        follow_up_note="",
    )

    result = decide_dispatch(request, note)

    assert result.next_status is DispatchStatus.READY_TO_CLOSE
    assert result.technician_follow_up is None
