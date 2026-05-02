"""Minimal HTTP client for Vercel Blob storage.

Used to persist completed arbitration cases on Vercel (where the filesystem
is read-only). Activated only when BLOB_READ_WRITE_TOKEN is set; otherwise
the caller falls back to local-disk persistence for dev.

Two operations:
    put_json(pathname, payload) -> public URL
    get_json(pathname) -> dict | None

We use the list endpoint to look up a blob by pathname so we don't have to
hard-code or decode the per-store URL prefix.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

BLOB_API = "https://blob.vercel-storage.com"


def _token() -> str:
    token = os.getenv("BLOB_READ_WRITE_TOKEN", "")
    if not token:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN is not set")
    return token


def is_configured() -> bool:
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


async def put_json(pathname: str, payload: Any) -> str:
    """Upload a JSON document at the given pathname. Returns the public URL."""
    body = json.dumps(payload).encode("utf-8")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.put(
            f"{BLOB_API}/{pathname}",
            content=body,
            headers={
                "authorization": f"Bearer {_token()}",
                "x-content-type": "application/json",
                "x-add-random-suffix": "0",
                "x-api-version": "7",
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["url"]


async def get_json(pathname: str) -> Optional[dict]:
    """Fetch a JSON document by pathname. Returns None if missing."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        listing = await client.get(
            BLOB_API,
            params={"prefix": pathname, "limit": 1},
            headers={"authorization": f"Bearer {_token()}"},
        )
        listing.raise_for_status()
        blobs = listing.json().get("blobs") or []
        match = next((b for b in blobs if b.get("pathname") == pathname), None)
        if not match:
            return None
        url = match.get("url")
        if not url:
            return None

        fetched = await client.get(url)
        if fetched.status_code == 404:
            return None
        fetched.raise_for_status()
        return fetched.json()
