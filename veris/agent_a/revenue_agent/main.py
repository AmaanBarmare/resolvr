"""Revenue Agent — runs inside a Veris sandbox.

Uses the OpenAI Agents SDK so Veris's auto-instrumentation captures the
agent workflow as trace events the grader can read. The SDK is pointed at
Baseten via a custom AsyncOpenAI client. We deliberately do NOT use
`output_type` because forcing structured output on this model causes it
to skip subsequent tool calls and fabricate values — instead we instruct
the model to emit JSON via the prompt and parse it from the text response.
"""

import json
import logging
import os
import re
import sys

import uvicorn
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner
from fastapi import FastAPI, Request
from openai import AsyncOpenAI

from revenue_agent.tools import (
    forecast_get_arr_projection,
    forecast_get_close_rate,
    salesforce_get_opportunities,
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("revenue_agent")

PORT = int(os.getenv("PORT", "8001"))


SYSTEM_PROMPT = """You are a Revenue Strategy Agent for a Series A B2B SaaS company.
Your job is to analyze pipeline data and recommend hiring decisions based on revenue opportunity.

ABSOLUTE TOOL-CALL REQUIREMENT — VIOLATION FAILS THE TASK:

Before you may emit any final answer, the conversation history MUST contain tool-result messages from ALL THREE of these tools:
1. salesforce_get_opportunities
2. forecast_get_close_rate
3. forecast_get_arr_projection

Workflow:
- Turn 1: call salesforce_get_opportunities. Wait for the result.
- Turn 2: call forecast_get_close_rate. Wait for the result.
- Turn 3: call forecast_get_arr_projection (passing the pipeline value and close rate you just received). Wait for the result.
- Turn 4 (and only Turn 4): emit the final answer.

Do NOT call multiple tools in one turn. Do NOT emit final output before Turn 4. Do NOT estimate, infer, or guess any number. If you "know" what the close rate or projected ARR probably is, you still must call the tool — the actual value may differ from your guess.

Final answer format (Turn 4 only): respond with ONLY a JSON object (no preamble, no markdown fences, no commentary) of this shape:

{
  "recommendation": "one sentence including the exact engineer headcount AND the timeline (use the timeline_months value the projection tool returned, e.g. 'hire X engineers over the next N months')",
  "assumptions": [
    {"variable": "pipeline_value", "value": "tool-returned value with units", "source": "salesforce_get_opportunities"},
    {"variable": "close_rate", "value": "tool-returned value with units", "source": "forecast_get_close_rate"},
    {"variable": "projected_arr", "value": "tool-returned value with units", "source": "forecast_get_arr_projection"}
  ],
  "reasoning": "step-by-step, MUST include: (1) quote the exact pipeline_value, close_rate, projected_arr, and timeline_months the tools returned; (2) state your engineer-capacity assumption explicitly (e.g. 'each engineer supports $X of new ARR'); (3) show the arithmetic that produces the headcount (projected_arr ÷ capacity_per_engineer = N engineers); (4) tie the timeline to timeline_months."
}"""


def _build_model() -> OpenAIChatCompletionsModel:
    api_key = os.getenv("BASETEN_API_KEY", "")
    base_url = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1")
    if not api_key:
        logger.warning("BASETEN_API_KEY is empty at startup")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return OpenAIChatCompletionsModel(
        model=os.getenv("BASETEN_MODEL_ID", "openai/gpt-oss-120b"),
        openai_client=client,
    )


_agent = Agent(
    name="revenue_agent",
    instructions=SYSTEM_PROMPT,
    tools=[
        salesforce_get_opportunities,
        forecast_get_close_rate,
        forecast_get_arr_projection,
    ],
    model=_build_model(),
    model_settings=ModelSettings(tool_choice="required"),
    reset_tool_choice=True,
)


def _extract_json(text: str) -> str:
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        candidate = cleaned[start:end]
        json.loads(candidate)
        return candidate
    except (ValueError, json.JSONDecodeError):
        return cleaned


app = FastAPI()


@app.post("/")
async def handle_message(request: Request):
    body = await request.json()
    user_message = body.get("message") or body.get("scenario") or ""

    try:
        result = await Runner.run(_agent, user_message, max_turns=10)
        text_output = str(result.final_output or "")
        return {"content": _extract_json(text_output)}
    except Exception as e:  # noqa: BLE001
        logger.exception("handle_message failed: %s", e)
        return {"content": "", "error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok", "agent": "revenue_agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
