import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Load .env from the project root (parent of backend/)
load_dotenv(Path(__file__).parent.parent / ".env")

from pipeline import load_json, run_pipeline  # noqa: E402

app = FastAPI(title="The Divorce Lawyer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    try:
        load_json("seed.json")
        load_json("transcript_a.json")
        load_json("transcript_b.json")
        return {
            "status": "ok",
            "transcripts_loaded": True,
            "seed_loaded": True,
            "mock_pipeline": os.getenv("USE_MOCK_PIPELINE", "false").lower() == "true",
            "mock_grounding": os.getenv("USE_MOCK_GROUNDING", "false").lower() == "true",
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e)}


@app.get("/api/run")
async def run(scenario_a: str | None = None, scenario_b: str | None = None):
    return StreamingResponse(
        run_pipeline(scenario_a=scenario_a, scenario_b=scenario_b),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
