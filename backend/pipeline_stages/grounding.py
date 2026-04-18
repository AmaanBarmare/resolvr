import asyncio
import json
import os
from typing import List

from models import AssumptionRow, ForensicsOutput, GroundedAssumption, GroundingOutput
from prompts import GROUNDING_VERDICT_PROMPT
from utils import baseten_client, youcom_client
from utils.json_utils import parse_claude_json

AUTHORITATIVE_DOMAINS = [
    "gartner.com",
    "idc.com",
    "forrester.com",
    "mckinsey.com",
    "a16z.com",
    "bvp.com",
    "saastr.com",
    "openviewpartners.com",
    "tomtunguz.com",
    "nytimes.com",
    "wsj.com",
    "techcrunch.com",
    "reuters.com",
    "bloomberg.com",
    "cbinsights.com",
]


QUERY_TEMPLATES = {
    "close_rate": "enterprise B2B SaaS close rate benchmark 2026",
    "burn_rate": "Series A SaaS burn rate benchmark 2026",
    "runway_months": "Series A startup runway months benchmark 2026",
    "macro_outlook": "enterprise SaaS market growth outlook 2026",
    "arr_projection": "Series A SaaS ARR growth benchmark 2026",
    "arr_growth": "Series A SaaS ARR growth benchmark 2026",
    "pipeline_value": "enterprise SaaS APAC pipeline benchmark 2026",
}


MOCK_GROUNDED = [
    {
        "variable": "close_rate",
        "agent_a_value": "34%",
        "agent_b_value": "19%",
        "market_benchmark": "17-22%",
        "verdict": "outlier",
        "source_url": "https://gartner.com/en/sales/insights/saas-sales-benchmarks",
        "source_name": "Gartner Enterprise SaaS Sales Benchmarks 2026",
        "note": "Agent A at 34% is ~1.7x the Gartner market median of 17-22% - a clear outlier.",
    },
    {
        "variable": "macro_outlook",
        "agent_a_value": "not modeled",
        "agent_b_value": "contracting",
        "market_benchmark": "Enterprise SaaS deal velocity slowing Q3-Q4 2026",
        "verdict": "outlier",
        "source_url": "https://cbinsights.com/research/enterprise-saas-q1-2026",
        "source_name": "CB Insights Enterprise SaaS Report Q1 2026",
        "note": "Agent A ignored the macro signal; CB Insights confirms Agent B's contracting outlook.",
    },
    {
        "variable": "arr_projection",
        "agent_a_value": "$1.43M",
        "agent_b_value": "$798K (implied at 19%)",
        "market_benchmark": "APAC enterprise software market growing 18% YoY",
        "verdict": "aligned",
        "source_url": "https://idc.com/getdoc.jsp?containerId=AP49823",
        "source_name": "IDC APAC Enterprise Software Market Forecast 2026",
        "note": "IDC macro growth rate is consistent with either projection; the ARR split is downstream of close_rate.",
    },
]


def _to_ground(forensics: ForensicsOutput) -> List[AssumptionRow]:
    return [
        row
        for row in forensics.assumption_table
        if row.divergence_type in ("data_conflict", "missing_var")
    ]


def _build_query(row: AssumptionRow) -> str:
    return QUERY_TEMPLATES.get(
        row.variable, f"{row.variable.replace('_', ' ')} enterprise SaaS benchmark 2026"
    )


def _format_search_results_for_prompt(hits: list) -> str:
    if not hits:
        return "(no results returned)"
    lines = []
    for i, h in enumerate(hits[:5], 1):
        lines.append(
            f"[{i}] {h.get('title','')}\n    URL: {h.get('url','')}\n    Snippet: {h.get('snippet','')[:320]}"
        )
    return "\n".join(lines)


async def _ground_row(row: AssumptionRow) -> GroundedAssumption:
    query = _build_query(row)
    raw = await youcom_client.search(query)
    hits = youcom_client.extract_hits(raw)

    prompt = GROUNDING_VERDICT_PROMPT.format(
        variable=row.variable,
        agent_a_value=row.agent_a_value,
        agent_b_value=row.agent_b_value,
        search_results=_format_search_results_for_prompt(hits),
    )
    verdict_raw = await baseten_client.complete(prompt, max_tokens=800)
    verdict = parse_claude_json(verdict_raw, stage="grounding")

    # Prefer an authoritative source if we can find one in the hits
    url = verdict.get("source_url") or ""
    if not any(d in url for d in AUTHORITATIVE_DOMAINS):
        for h in hits:
            h_url = h.get("url") or ""
            if any(d in h_url for d in AUTHORITATIVE_DOMAINS):
                url = h_url
                if not verdict.get("source_name"):
                    verdict["source_name"] = h.get("title") or "Unknown source"
                break

    verdict_val = (verdict.get("verdict") or "unverifiable").lower()
    if verdict_val not in {"outlier", "aligned", "unverifiable"}:
        verdict_val = "unverifiable"

    return GroundedAssumption(
        variable=row.variable,
        agent_a_value=row.agent_a_value,
        agent_b_value=row.agent_b_value,
        market_benchmark=verdict.get("market_benchmark") or "unavailable",
        verdict=verdict_val,
        source_url=url,
        source_name=verdict.get("source_name") or "Unknown source",
        note=verdict.get("note") or "",
    )


async def run_grounding(forensics: ForensicsOutput) -> GroundingOutput:
    if (
        os.getenv("USE_MOCK_PIPELINE", "").lower() == "true"
        or os.getenv("USE_MOCK_GROUNDING", "").lower() == "true"
    ):
        return GroundingOutput(
            grounded_assumptions=[GroundedAssumption(**g) for g in MOCK_GROUNDED]
        )

    rows = _to_ground(forensics)
    grounded = await asyncio.gather(*[_ground_row(r) for r in rows])
    return GroundingOutput(grounded_assumptions=list(grounded))
