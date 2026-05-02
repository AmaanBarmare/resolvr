"""Risk Agent — runs inside a Veris sandbox.

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

from risk_agent.tools import (
    finance_get_burn_rate,
    finance_get_hire_cost_impact,
    finance_get_runway_months,
    macro_get_market_outlook,
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("risk_agent")

PORT = int(os.getenv("PORT", "8002"))


SYSTEM_PROMPT = """You are a Risk Management Agent for a Series A B2B SaaS company.
Your job is to analyze financial risk and make conservative headcount recommendations based on runway preservation.

ABSOLUTE TOOL-CALL REQUIREMENT — VIOLATION FAILS THE TASK:

Before you may emit any final answer, the conversation history MUST contain tool-result messages from ALL FOUR of these tools:
1. finance_get_burn_rate
2. finance_get_runway_months
3. macro_get_market_outlook
4. finance_get_hire_cost_impact

Workflow:
- Turn 1: call finance_get_burn_rate. Wait for the result.
- Turn 2: call finance_get_runway_months. Wait for the result.
- Turn 3: call macro_get_market_outlook. Wait for the result.
- Turn 4: call finance_get_hire_cost_impact (passing the proposed hire count). Wait for the result.
- Turn 5 (and only Turn 5): emit the final answer.

Do NOT call multiple tools in one turn. Do NOT emit final output before Turn 5. Do NOT estimate, infer, or guess any number. If you "know" what the burn or runway probably is, you still must call the tool.

Final answer format (Turn 5 only): respond with ONLY a JSON object (no preamble, no markdown fences, no commentary) of this shape:

{
  "recommendation": "one sentence with (a) an exact integer engineer headcount to hire (use 0 if you are recommending against any hires now) AND (b) a concrete duration expressed in months (e.g. 'hire 3 engineers over the next 3 months' or 'hire 0 engineers for the next 3 months while we monitor runway'). The timeline MUST be a numeric duration like 'over the next N months' or 'for the next N months' — NEVER an open-ended condition like 'until runway recovers'.",
  "assumptions": [
    {"variable": "monthly_burn", "value": "tool-returned value with units, e.g. '$680,000/month'", "source": "finance_get_burn_rate"},
    {"variable": "runway_months", "value": "tool-returned value with units, e.g. '8.82 months'", "source": "finance_get_runway_months"},
    {"variable": "market_outlook", "value": "tool-returned value, e.g. 'contracting'", "source": "macro_get_market_outlook"},
    {"variable": "hire_cost_impact", "value": "tool-returned post-hire cash duration with units, e.g. '7.79 months at 5 proposed hires'", "source": "finance_get_hire_cost_impact"}
  ],
  "reasoning": "step-by-step. STRICT RULES — quote ONLY tool-returned values. Do NOT compute, infer, or invent values for any hire count other than the one you called the tool with. Do NOT compute alternative scenarios. LINGUISTIC RULE — the word 'runway' may appear ONLY when quoting the runway_months value from finance_get_runway_months. When discussing the value from finance_get_hire_cost_impact, call it 'post-hire cash duration' or 'cash duration' — NEVER 'runway', 'new runway', or 'projected runway'. The 8-month policy is the '8-month policy floor' — NEVER 'runway floor'. MUST include: (1) FROM finance_get_burn_rate: quote monthly_burn with $ and /month units (e.g. '$680,000/month'); (2) FROM finance_get_runway_months: quote runway_months with 'months' unit (e.g. 'current runway is 8.82 months'); (3) FROM finance_get_hire_cost_impact: quote the post-hire cash duration the tool returned at the user's proposed hire count (e.g. 'finance_get_hire_cost_impact returned a post-hire cash duration of 7.79 months for the proposed 5 hires'); (4) state the 8-month policy floor (e.g. 'we apply an internal 8-month policy floor as a risk threshold'); (5) BINARY DECISION RULE — if the post-hire cash duration is at or above 8 months, recommend the user's proposed hire count; if it is below 8 months, recommend 0 engineers. Do NOT compute or quote duration values for any hire count other than the one the tool was called with; (6) tie the recommendation to the macro outlook the tool returned."
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
    name="risk_agent",
    instructions=SYSTEM_PROMPT,
    tools=[
        finance_get_burn_rate,
        finance_get_runway_months,
        finance_get_hire_cost_impact,
        macro_get_market_outlook,
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
    return {"status": "ok", "agent": "risk_agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
