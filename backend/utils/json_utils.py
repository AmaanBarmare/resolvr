import json
import re

from exceptions import PipelineError


def parse_claude_json(raw: str, stage: str) -> dict:
    """Strip markdown fences and parse JSON. Raises PipelineError on failure."""
    clean = re.sub(r"```json\s*|```\s*", "", raw).strip()
    # If Claude prefixed anything, try to grab the first {...} block
    if not clean.startswith("{"):
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            clean = match.group(0)
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise PipelineError(
            stage=stage,
            message=f"Claude returned invalid JSON: {e}. Raw: {clean[:300]}",
        )
