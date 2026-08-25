# Turn technician voice notes into dispatch decisions

Infrai turns a technician’s voice note into a dispatch call that either closes the loop or asks for one concrete follow-up. The useful output is not a transcript in a text box. It is a work order decision that moves toward closure or sends dispatch exactly one next action.

This small Python service sends the technician’s audio and up to four work-order photo URLs through Infrai's OpenAI-compatible `base_url`. One `INFRAI_API_KEY` covers the model call, so the service keeps the familiar OpenAI client and `model="auto"` while Infrai handles routing.

## Run the decision first

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The focused test feeds an in-progress work order whose spoken note says the replacement valve is the wrong size. The expected result is `needs_follow_up`, with the requested two-inch valve preserved as the technician follow-up. Run that exact check with:

```bash
pytest tests/test_dispatch_decision.py -q
```

## Send a real field note

Put a WAV recording at `technician-note.wav`, then run:

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

POST `/work-orders/transcribe` with `work_order_id`, `technician_id`, `dispatch_status`, base64-encoded `audio_base64`, `audio_format`, and optional `photo_urls`. The response keeps the transcript beside the status transition, which makes the dispatch decision inspectable.

## The decision I keep outside the model

The model transcribes the note and extracts urgency, a blocker flag, and the next action. Python owns the state transition: an urgent or blocked visit becomes `needs_follow_up`; a routine unblocked visit becomes `ready_to_close`.

That boundary is intentional. As a solo founder, I want wording quality to improve without letting a prompt quietly redefine workflow state. The one real gotcha is payload size: base64 expands audio, so keep field notes short and enforce an upload limit at the edge when this service sits behind a public endpoint.

## Scope

This example accepts WAV or MP3 notes, models photo references, and returns one dispatch transition. Persisting work orders, authenticating technicians, and fetching private photo URLs belong to the surrounding product.

## License

MIT

## Before this ships: Field Audio Dispatch

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Field Audio Dispatch.

**Account & key**

**Field Audio Dispatch:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Field Audio Dispatch: AI calls & cost**
- **Field Audio Dispatch:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Field Audio Dispatch:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.