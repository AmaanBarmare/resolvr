import asyncio
import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

from exceptions import PipelineError
from models import AgentOutput, Assumption, Stage1Output
from pipeline_stages.brief import run_brief
from pipeline_stages.forensics import run_forensics
from pipeline_stages.grounding import run_grounding
from pipeline_stages.simulation import run_simulation

DATA_DIR = Path(__file__).parent / os.getenv("DATA_DIR", "data")


def load_json(name: str) -> dict:
    with open(DATA_DIR / name) as f:
        return json.load(f)


def load_transcripts() -> Dict[str, dict]:
    return {
        "agent_a": load_json("transcript_a.json"),
        "agent_b": load_json("transcript_b.json"),
    }


def _assumptions_from_transcript(t: dict) -> list[Assumption]:
    assumptions = []
    for variable, entry in (t.get("key_assumptions") or {}).items():
        assumptions.append(
            Assumption(
                variable=variable,
                value=entry.get("value", ""),
                source=entry.get("source", ""),
            )
        )
    return assumptions


def parse_agent_outputs(transcripts: Dict[str, dict]) -> Stage1Output:
    a = transcripts["agent_a"]
    b = transcripts["agent_b"]
    return Stage1Output(
        agent_a=AgentOutput(
            recommendation=a["final_recommendation"],
            assumptions=_assumptions_from_transcript(a),
            source="transcript_a.json",
        ),
        agent_b=AgentOutput(
            recommendation=b["final_recommendation"],
            assumptions=_assumptions_from_transcript(b),
            source="transcript_b.json",
        ),
    )


def _event(stage: Any, status: str, *, data: Any = None, message: str = None) -> str:
    payload: dict = {"stage": stage, "status": status}
    if data is not None:
        payload["data"] = data
    if message is not None:
        payload["message"] = message
    return f"data: {json.dumps(payload)}\n\n"


# Mock demo pacing: small sleeps so the UI can show each stage streaming in.
MOCK_DELAY = float(os.getenv("MOCK_STAGE_DELAY_SECONDS", "1.2"))


async def run_pipeline() -> AsyncGenerator[str, None]:
    mock = os.getenv("USE_MOCK_PIPELINE", "").lower() == "true"
    seed = load_json("seed.json")

    try:
        # Stage 1
        yield _event(1, "loading", message="Loading Veris transcripts...")
        transcripts = load_transcripts()
        stage1 = parse_agent_outputs(transcripts)
        if mock:
            await asyncio.sleep(MOCK_DELAY * 0.5)
        yield _event(1, "complete", data=stage1.model_dump())

        # Stage 2 — Forensics
        yield _event(2, "loading", message="Running forensics agent...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        forensics = await run_forensics(transcripts)
        yield _event(2, "complete", data=forensics.model_dump())

        # Stage 3 — Grounding
        yield _event(
            3,
            "loading",
            message="Querying You.com for enterprise SaaS benchmarks...",
        )
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        grounding = await run_grounding(forensics)
        yield _event(3, "complete", data=grounding.model_dump())

        # Stage 4 — Simulation
        yield _event(4, "loading", message="Simulating outcome paths...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        simulation = await run_simulation(forensics, grounding, seed)
        yield _event(4, "complete", data=simulation.model_dump())

        # Stage 5 — Brief
        yield _event(5, "loading", message="Generating decision brief...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        brief = await run_brief(forensics, grounding, simulation, seed)
        yield _event(5, "complete", data=brief.model_dump())

        yield _event("done", "complete")

    except PipelineError as e:
        yield _event(e.stage, "error", message=e.message)
    except Exception as e:  # noqa: BLE001
        yield _event("pipeline", "error", message=f"Unhandled error: {e!s}")


async def _main_cli() -> None:
    async for chunk in run_pipeline():
        print(chunk, end="")


if __name__ == "__main__":
    asyncio.run(_main_cli())
