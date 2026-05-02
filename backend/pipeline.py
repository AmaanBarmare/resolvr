import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from agents import build_scenario_profile, run_revenue_agent, run_risk_agent
from exceptions import PipelineError
from models import AgentOutput, Assumption, Stage1Output
from pipeline_stages.brief import run_brief
from pipeline_stages.forensics import run_forensics
from pipeline_stages.grounding import run_grounding
from pipeline_stages.simulation import run_simulation

DATA_DIR = Path(__file__).parent / os.getenv("DATA_DIR", "data")
CASES_DIR = DATA_DIR / "cases"


def _save_case(
    case_id: str,
    stage_data: Dict[int, Any],
    scenario_a: str,
    scenario_b: str,
) -> None:
    """Persist a completed run to a local JSON file (per CLAUDE.md: no DB)."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scenarios": {"a": scenario_a, "b": scenario_b},
        "stage_data": {str(k): v for k, v in stage_data.items()},
    }
    with open(CASES_DIR / f"{case_id}.json", "w") as f:
        json.dump(payload, f, indent=2)


def load_case(case_id: str) -> Optional[Dict[str, Any]]:
    """Read a saved case by ID. Returns None if not found."""
    path = CASES_DIR / f"{case_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_json(name: str) -> dict:
    with open(DATA_DIR / name) as f:
        return json.load(f)


def load_transcripts() -> Dict[str, dict]:
    """Fallback path: read the pre-saved transcripts (used in mock mode)."""
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
            source=a.get("source_label", "revenue_agent (live)"),
        ),
        agent_b=AgentOutput(
            recommendation=b["final_recommendation"],
            assumptions=_assumptions_from_transcript(b),
            source=b.get("source_label", "risk_agent (live)"),
        ),
    )


def _profile_to_seed(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a scenario profile into the seed dict the downstream stages expect."""
    return {
        "company": profile.get("company_name", ""),
        "industry": profile.get("sector", ""),
        "stage": profile.get("stage", ""),
        "financials": {
            "runway_total_dollars": profile.get("cash_on_hand_usd"),
            "burn_rate_monthly": profile.get("monthly_burn_usd"),
            "runway_months": profile.get("runway_months"),
        },
        "team": {
            "engineers_current": profile.get("headcount_engineers"),
            "total_employees": profile.get("headcount_total"),
        },
        "pipeline": {
            "total_value": profile.get("pipeline_value_usd"),
            "deal_count": profile.get("deal_count"),
            "primary_region": profile.get("region"),
            "avg_deal_size": profile.get("avg_deal_size_usd"),
        },
        "hire_cost": {
            "per_engineer_monthly": profile.get("avg_hire_monthly_cost_usd"),
            "hiring_batch": profile.get("proposed_hire_count"),
        },
        "decision_question": profile.get("decision_question", ""),
    }


def _event(stage: Any, status: str, *, data: Any = None, message: str = None) -> str:
    payload: dict = {"stage": stage, "status": status}
    if data is not None:
        payload["data"] = data
    if message is not None:
        payload["message"] = message
    return f"data: {json.dumps(payload)}\n\n"


# Mock demo pacing: small sleeps so the UI can show each stage streaming in.
MOCK_DELAY = float(os.getenv("MOCK_STAGE_DELAY_SECONDS", "1.2"))


async def _run_live_agents(
    scenario_a: str,
    scenario_b: str,
    profile: Dict[str, Any],
) -> Dict[str, dict]:
    revenue_task = asyncio.create_task(run_revenue_agent(scenario_a, profile))
    risk_task = asyncio.create_task(run_risk_agent(scenario_b, profile))
    agent_a, agent_b = await asyncio.gather(revenue_task, risk_task)

    for label, transcript in (("revenue_agent", agent_a), ("risk_agent", agent_b)):
        if transcript.get("error"):
            raise PipelineError(
                stage=1,
                message=f"{label} failed: {transcript['error']}",
            )
        if not transcript.get("final_recommendation"):
            raise PipelineError(
                stage=1,
                message=f"{label} returned no recommendation",
            )

    agent_a["source_label"] = "revenue_agent (live)"
    agent_b["source_label"] = "risk_agent (live)"
    return {"agent_a": agent_a, "agent_b": agent_b}


async def run_pipeline(
    scenario_a: Optional[str] = None,
    scenario_b: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    mock = os.getenv("USE_MOCK_PIPELINE", "").lower() == "true"

    scenario_a = (scenario_a or "").strip()
    scenario_b = (scenario_b or "").strip()
    if not mock and (not scenario_a or not scenario_b):
        yield _event(
            1,
            "error",
            message="Both Revenue and Risk briefs are required.",
        )
        return

    case_id = uuid.uuid4().hex[:12]
    captured: Dict[int, Any] = {}

    try:
        # Stage 1 — synthesize a scenario profile, then run both advisors live
        if mock:
            yield _event(1, "loading", message="Loading saved transcripts…")
            transcripts = load_transcripts()
            seed = load_json("seed.json")
            await asyncio.sleep(MOCK_DELAY * 0.5)
        else:
            yield _event(
                1,
                "loading",
                message="Building the case profile from the two briefs…",
            )
            profile = await build_scenario_profile(scenario_a, scenario_b)
            yield _event(
                1,
                "loading",
                message=f"Dispatching the Revenue & Risk advisors on {profile.get('company_name', 'the case')}…",
            )
            transcripts = await _run_live_agents(scenario_a, scenario_b, profile)
            seed = _profile_to_seed(profile)

        stage1 = parse_agent_outputs(transcripts)
        captured[1] = stage1.model_dump()
        yield _event(1, "complete", data=captured[1])

        # Stage 2 — Forensics
        yield _event(2, "loading", message="Running forensics agent...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        forensics = await run_forensics(transcripts)
        captured[2] = forensics.model_dump()
        yield _event(2, "complete", data=captured[2])

        # Stage 3 — Grounding
        yield _event(
            3,
            "loading",
            message="Querying You.com for market benchmarks...",
        )
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        grounding = await run_grounding(forensics)
        captured[3] = grounding.model_dump()
        yield _event(3, "complete", data=captured[3])

        # Stage 4 — Simulation
        yield _event(4, "loading", message="Simulating outcome paths...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        simulation = await run_simulation(forensics, grounding, seed)
        captured[4] = simulation.model_dump()
        yield _event(4, "complete", data=captured[4])

        # Stage 5 — Brief
        yield _event(5, "loading", message="Generating decision brief...")
        if mock:
            await asyncio.sleep(MOCK_DELAY)
        brief = await run_brief(forensics, grounding, simulation, seed)
        captured[5] = brief.model_dump()
        yield _event(5, "complete", data=captured[5])

        # Persist the completed case so it can be re-opened via /api/case/{id}
        try:
            _save_case(case_id, captured, scenario_a, scenario_b)
        except Exception:  # noqa: BLE001
            # Persistence failure shouldn't break the user-facing run.
            pass

        # Final event includes the case_id so the frontend can update the URL.
        yield f"data: {json.dumps({'stage': 'done', 'status': 'complete', 'case_id': case_id})}\n\n"

    except PipelineError as e:
        yield _event(e.stage, "error", message=e.message)
    except Exception as e:  # noqa: BLE001
        yield _event("pipeline", "error", message=f"Unhandled error: {e!s}")


async def _main_cli() -> None:
    async for chunk in run_pipeline(
        "Healthbit, a Series A B2B health-tech company, is considering doubling its sales team to chase hospital contracts in Q3.",
        "Healthbit, a Series A B2B health-tech company, is reviewing a proposal to double its sales team; evaluate risk given current runway.",
    ):
        print(chunk, end="")


if __name__ == "__main__":
    asyncio.run(_main_cli())
