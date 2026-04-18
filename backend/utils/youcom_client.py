import os
from typing import Any, Dict, List

import httpx

YOUCOM_API_KEY = os.getenv("YOUCOM_API_KEY", "")
YOUCOM_MAX_RESULTS = int(os.getenv("YOUCOM_MAX_RESULTS", "5"))


async def search(query: str) -> Dict[str, Any]:
    """Fire a You.com Smart search. Returns the raw JSON payload.

    Uses the Search API (api.ydc-index.io). If the deployment uses a different
    endpoint (e.g. chat or smart), adjust here.
    """
    if not YOUCOM_API_KEY:
        raise RuntimeError(
            "YOUCOM_API_KEY is not set. Either set it in .env or run with "
            "USE_MOCK_GROUNDING=true."
        )

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://ydc-index.io/v1/search",
            headers={"X-API-Key": YOUCOM_API_KEY},
            params={"query": query, "count": YOUCOM_MAX_RESULTS},
        )
        response.raise_for_status()
        return response.json()


def extract_hits(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize a You.com v1 search payload to a list of {title, url, snippet}.

    v1 response shape: {"results": {"web": [...], "news": [...]}, "metadata": {...}}
    """
    hits: List[Dict[str, Any]] = []
    results = payload.get("results")
    raw: List[Dict[str, Any]] = []
    if isinstance(results, dict):
        raw.extend(results.get("web") or [])
        raw.extend(results.get("news") or [])
    elif isinstance(results, list):
        raw.extend(results)
    # Legacy fallbacks
    raw.extend(payload.get("hits") or [])

    for hit in raw:
        if not isinstance(hit, dict):
            continue
        hits.append(
            {
                "title": hit.get("title") or hit.get("name") or "",
                "url": hit.get("url") or hit.get("link") or "",
                "snippet": hit.get("description")
                or hit.get("snippet")
                or hit.get("content")
                or " ".join(hit.get("snippets", []) or []),
            }
        )
    return hits
