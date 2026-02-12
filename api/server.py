import os
from pathlib import Path
from typing import Iterator, Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fastapi_clerk_auth import (
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)

from openai import OpenAI


app = FastAPI()

# If frontend and backend are served from the same domain in one container,
# you generally DON'T need CORS. Keeping it here is okay for early testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later (e.g., your domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clerk authentication
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)


class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str


SYSTEM_PROMPT = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.
Reply with exactly three sections with the headings:
### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
""".strip()


def user_prompt_for(visit: Visit) -> str:
    return (
        f"Create the summary, next steps and draft email for:\n"
        f"Patient Name: {visit.patient_name}\n"
        f"Date of Visit: {visit.date_of_visit}\n"
        f"Notes:\n{visit.notes}"
    )


@app.post("/api/consultation")
def consultation_summary(
    visit: Visit,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    # You can use this later for logging / usage limits, etc.
    _user_id = creds.decoded.get("sub")

    client = OpenAI()

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you prefer
    user_prompt = user_prompt_for(visit)

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )

    def event_stream() -> Iterator[str]:
        # Each yielded chunk must be valid SSE: "data: ...\n\n"
        for chunk in stream:
            delta = chunk.choices[0].delta
            text: Optional[str] = getattr(delta, "content", None)
            if text:
                # send as-is; ReactMarkdown can handle newlines fine
                yield f"data: {text}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Some proxies buffer responses; this discourages buffering.
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
def health_check():
    """Health check endpoint for AWS App Runner / ECS"""
    return {"status": "healthy"}


# -------------------------
# Static export serving (MUST BE LAST)
# -------------------------
# Put your Next.js export output into ./static inside the container
# e.g. copy `out/` -> `static/` during Docker build
static_path = Path("static")

if static_path.exists():
    @app.get("/")
    def serve_root():
        index = static_path / "index.html"
        return FileResponse(index)

    # Serve everything else from static
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
