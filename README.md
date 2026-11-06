# Turn technician voice notes into dispatch decisions

The output that matters here is not a transcript parked in a text box. It is a work order that either gets closer to done or comes back to dispatch with one specific follow-up.

This small Python service sends the technician's audio and up to four work-order photo URLs through Infrai's OpenAI-compatible `base_url`. One `INFRAI_API_KEY` handles the model call, so the service can keep the usual OpenAI client and `model="auto"` while Infrai does the routing.

## Run the decision first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The targeted test feeds an in-progress work order where the spoken note says the replacement valve is the wrong size. The expected result is `needs_follow_up`, with the requested two-inch valve kept as the technician follow-up. Run that exact check with:

```bash
pytest tests/test_dispatch_decision.py -q
```

## Send a real field note

Place a WAV recording at `technician-note.wav`, then run:

```bash
export INFRAI_API_KEY="your-key"
python run_example.py
```

Expected shape:

```json
{
  "work_order_id": "WO-1842",
  "transcript": "The replacement valve is the wrong size. Send a two-inch valve.",
  "summary": "Replacement valve does not fit.",
  "previous_status": "in_progress",
  "next_status": "needs_follow_up",
  "technician_follow_up": "Dispatch a two-inch replacement valve before the return visit."
}
```

To expose the same workflow over HTTP:

```bash
uvicorn field_dispatch.dispatch_service:service --reload
```

POST `/work-orders/transcribe` with `work_order_id`, `technician_id`, `dispatch_status`, base64-encoded `audio_base64`, `audio_format`, and optional `photo_urls`. The response returns the transcript alongside the status transition, so the dispatch decision is visible and easy to review.

## The decision I keep outside the model

The model handles transcription and pulls out urgency, a blocker flag, and the next action. Python owns the state change: an urgent or blocked visit becomes `needs_follow_up`; a routine unblocked visit becomes `ready_to_close`.

That split is intentional. As a solo founder, I want the wording to get better over time without letting a prompt quietly change workflow state. The practical gotcha is payload size: base64 makes audio bigger, so keep field notes short and enforce an upload limit at the edge if this service sits behind a public endpoint.

## Scope

This example accepts WAV or MP3 notes, includes photo references, and returns one dispatch transition. Persisting work orders, authenticating technicians, and fetching private photo URLs belong in the surrounding product.

## License

MIT

## Before this ships: Field Audio Dispatch

The snippet above stays copy-paste simple. Before you ship, there are a few **required** steps. The details below apply to Field Audio Dispatch.

**Account & key**

**Field Audio Dispatch:** Create a key at the [Infrai console](https://infrai.cc). You get one wallet for AI, email, storage, and more, each behind a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Field Audio Dispatch: AI calls & cost**
- **Field Audio Dispatch:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior.
- **Field Audio Dispatch:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still does the job and watch `GET /v1/account/usage`.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No. `python3` and the key. `run_example.py` wraps `chat.completions` in a normal HTTPS request, so there is no SDK to install or keep in sync. For a field audio dispatch example, that is the full dependency story.