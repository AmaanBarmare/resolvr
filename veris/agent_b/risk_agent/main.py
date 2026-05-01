"""Risk Agent — runs inside a Veris sandbox.

Exposes a POST / endpoint. Veris posts a scenario message; we loop through
the OpenAI-compatible tool-use protocol against Baseten until the model
emits a final JSON recommendation.
"""

import json
import logging
import os
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, Request
from openai import AsyncOpenAI

from risk_agent.tools import TOOL_SCHEMAS, dispatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_agent")

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY", "")
BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID", "openai/gpt-oss-120b")
BASETEN_BASE_URL = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1")
PORT = int(os.getenv("PORT", "8002"))

SYSTEM_PROMPT = """You are a Risk Management Agent for a Series A B2B SaaS company.
Your job is to analyze financial risk and make conservative headcount recommendations based on runway preservation.

You have access to:
- finance_get_burn_rate: query current monthly burn
- finance_get_runway_months: compute runway in months
- finance_get_hire_cost_impact: compute hire cost impact on burn
- macro_get_market_outlook: get macro enterprise SaaS conditions

When making recommendations, always cite:
- The exact burn rate you found
- The exact runway in months
- The cost impact of each hire on monthly burn
- The macro market conditions you factored in

After you have called the tools you need, produce your FINAL recommendation as JSON
with this exact structure (and nothing else - no preamble, no markdown):

{
  "recommendation": "string - your hiring recommendation",
  "assumptions": [
    {"variable": "machine_readable_key", "value": "value with units", "source": "where you got this"}
  ],
  "reasoning": "your reasoning chain as a single string"
}"""


app = FastAPI()


def _client() -> AsyncOpenAI:
    api_key = os.getenv("BASETEN_API_KEY", "")
    base_url = os.getenv("BASETEN_BASE_URL", BASETEN_BASE_URL)
    if not api_key:
        logger.warning("BASETEN_API_KEY is empty at call time — LLM calls will 401")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


async def _run_tool_loop(user_message: str) -> Dict[str, Any]:
    client = _client()
    model_id = os.getenv("BASETEN_MODEL_ID", BASETEN_MODEL_ID)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    tool_calls_log: List[Dict[str, Any]] = []

    for _ in range(8):
        try:
            response = await client.chat.completions.create(
                model=model_id,
                max_tokens=1500,
                temperature=0.2,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                extra_body={"reasoning_effort": "low"},
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Baseten call failed: %s", e)
            return {"final_text": "", "tool_calls": tool_calls_log, "error": str(e)}
        msg = response.choices[0].message

        if not msg.tool_calls:
            return {"final_text": msg.content or "", "tool_calls": tool_calls_log}

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = dispatch(name, args)
            except Exception as e:  # noqa: BLE001
                result = {"error": str(e)}
            tool_calls_log.append({"tool": name, "input": args, "output": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    return {"final_text": "", "tool_calls": tool_calls_log}


def _parse_final(text: str) -> Dict[str, Any]:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"recommendation": text, "assumptions": [], "reasoning": ""}


@app.post("/")
async def handle_message(request: Request):
    body = await request.json()
    user_message = body.get("message") or body.get("scenario") or ""

    try:
        result = await _run_tool_loop(user_message)
        parsed = _parse_final(result.get("final_text", "") or "")
        transcript: Dict[str, Any] = {
            "agent": "risk_agent",
            "agent_role": "Risk Management",
            "tool_calls": result.get("tool_calls", []),
            "recommendation": parsed.get("recommendation", ""),
            "assumptions": parsed.get("assumptions", []),
            "reasoning": parsed.get("reasoning", ""),
            "confidence": "high",
        }
        if result.get("error"):
            transcript["error"] = result["error"]
            transcript["confidence"] = "low"
    except Exception as e:  # noqa: BLE001
        logger.exception("handle_message failed: %s", e)
        transcript = {
            "agent": "risk_agent",
            "agent_role": "Risk Management",
            "tool_calls": [],
            "recommendation": "",
            "assumptions": [],
            "reasoning": "",
            "error": str(e),
            "confidence": "none",
        }
    payload = {
        "recommendation": transcript.get("recommendation", ""),
        "assumptions": transcript.get("assumptions", []),
        "reasoning": transcript.get("reasoning", ""),
    }
    return {"response": json.dumps(payload), "transcript": transcript}


@app.get("/health")
def health():
    return {"status": "ok", "agent": "risk_agent"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
