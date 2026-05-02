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
  "recommendation": "one sentence including the exact engineer headcount AND a concrete timeline (e.g. 'hire over the next N months' or 'pause hiring until runway recovers above X months')",
  "assumptions": [
    {"variable": "monthly_burn", "value": "tool-returned value with units", "source": "finance_get_burn_rate"},
    {"variable": "runway_months", "value": "tool-returned value with units", "source": "finance_get_runway_months"},
    {"variable": "market_outlook", "value": "tool-returned value", "source": "macro_get_market_outlook"},
    {"variable": "hire_cost_impact", "value": "tool-returned value with units", "source": "finance_get_hire_cost_impact"}
  ],
  "reasoning": "step-by-step, MUST include: (1) quote the exact monthly_burn, runway_months, and the new_runway_months the hire-impact tool returned; (2) state your runway-floor assumption explicitly (e.g. 'we will not let runway drop below N months'); (3) show the arithmetic that produces the headcount (compare new_runway_months to your floor); (4) tie the recommendation to the macro outlook the tool returned."
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
