# backend/api/download_audio.py

import os
import sys
from typing import Iterator

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from modal import fastapi_endpoint

from modal_app import app, backend_image, JOB_STORE, AUDIO_VOLUME


def _iter_file_chunks(path: str) -> Iterator[bytes]:
    with open(path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            yield chunk


@app.function(
    image=backend_image,
    timeout=300,
    volumes={"/audio": AUDIO_VOLUME},
)
@fastapi_endpoint(method="GET")
def download_audio(job_id: str):
    """
    GET /download_audio?job_id=...

    Streams the generated audio file for the given job.
    """
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOB_STORE[job_id]
    if job.get("status") != "complete":
        raise HTTPException(status_code=404, detail="Audio not ready")

    audio_path = job.get("_audio_file_path")
    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio not available")

    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing")

    filename = job.get("audio_filename") or os.path.basename(audio_path)

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "public, max-age=3600",
    }

    return StreamingResponse(
        _iter_file_chunks(audio_path),
        media_type="audio/wav",
        headers=headers,
    )
