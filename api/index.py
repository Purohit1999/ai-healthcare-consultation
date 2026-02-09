import os
from typing import Iterator

from fastapi import FastAPI, Depends  # type: ignore
from fastapi.responses import StreamingResponse  # type: ignore
from fastapi_clerk_auth import (  # type: ignore
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)
from openai import OpenAI  # type: ignore

app = FastAPI()

jwks_url = os.getenv("CLERK_JWKS_URL")
if not jwks_url:
    # Fail fast with a clear error message if env var is missing
    raise RuntimeError("CLERK_JWKS_URL is not set in environment variables.")

clerk_config = ClerkConfig(jwks_url=jwks_url)
clerk_guard = ClerkHTTPBearer(clerk_config)

def sse_event(data: str) -> str:
    # Ensure multi-line chunks are valid SSE
    lines = data.splitlines() or [data]
    return "".join(f"data: {line}\n" for line in lines) + "\n"

@app.get("/")
def idea(creds: HTTPAuthorizationCredentials = Depends(clerk_guard)):
    # User ID from JWT (available for future use)
    user_id = creds.decoded.get("sub")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        def missing_key() -> Iterator[str]:
            yield sse_event("ERROR: OPENAI_API_KEY is missing in environment variables.")
        return StreamingResponse(missing_key(), media_type="text/event-stream")

    client = OpenAI(api_key=api_key)

    prompt = [
        {
            "role": "system",
            "content": (
                "You generate concise, high-quality SaaS business ideas. "
                "Always format in clean Markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate ONE new business idea for AI Agents.\n\n"
                "Format in Markdown with this exact structure:\n"
                "## Title\n"
                "## Problem\n"
                "## Solution\n"
                "## Target Customers\n"
                "## Why It Works\n"
                "Use bullet points where helpful. Under 180 words."
            ),
        },
    ]

    stream = client.chat.completions.create(
        model="gpt-5-nano",
        messages=prompt,
        stream=True,
    )

    def event_stream() -> Iterator[str]:
        try:
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", None)
                if text:
                    yield sse_event(text)
            yield sse_event("[DONE]")
        except Exception as e:
            yield sse_event(f"ERROR: Streaming failed. Details: {str(e)}")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
