# backend/api/fetch_result.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import HTTPException
from modal import fastapi_endpoint

from modal_app import app, backend_image, JOB_STORE


@app.function(image=backend_image, timeout=120)
@fastapi_endpoint(method="GET")
def fetch_result(job_id: str):
    """
    GET /fetch_result?job_id=...

    Returns a compact view of the final result:
      - captions: image descriptions
      - summary: cohesive story narrative
      - lyrics: structured song lyrics
      - audio_path: WAV file with a vocal performance of the lyrics

    If not complete, returns current status + message.
    """
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOB_STORE[job_id]
    status = job.get("status")

    if status != "complete":
        return {
            "job_id": job.get("job_id"),
            "status": status,
            "message": "Job not complete yet",
        }

    return {
        "job_id": job.get("job_id"),
        "status": "complete",
        "genre": job.get("genre"),
        "mood": job.get("mood"),
        "captions": job.get("captions"),
        "summary": job.get("summary"),
        "lyrics": job.get("lyrics"),
        "audio_path": job.get("audio_url") or job.get("audio_path"),
        "audio_url": job.get("audio_url") or job.get("audio_path"),
        "audio_filename": job.get("audio_filename"),
    }
