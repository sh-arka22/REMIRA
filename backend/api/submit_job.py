# backend/api/submit_job.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pydantic import BaseModel, Field
from fastapi import HTTPException

from modal import fastapi_endpoint
from modal_app import app, backend_image, GPU_TYPE, JOB_STORE, PHOTOS_VOLUME, AUDIO_VOLUME

from workers.image_analysis_worker import generate_photo_captions
from workers.summary_worker import summarize_captions
from workers.lyrics_worker import generate_lyrics
from workers.vocal_worker import generate_vocals
from workers.music_worker import generate_music
from workers.packaging_worker import package_result


class SubmitJobRequest(BaseModel):
    job_id: str = Field(..., description="Job ID from /upload_photo")
    genre: str = Field(..., description="e.g., pop, rock, edm, lo-fi")
    mood: str = Field(..., description="e.g., nostalgic, happy, epic")


# GPU pipeline worker – internal, not HTTP-exposed
@app.function(
    image=backend_image,
    gpu=GPU_TYPE,
    timeout=1200,
    volumes={
        "/photos": PHOTOS_VOLUME,
        "/audio": AUDIO_VOLUME
    }
)
def _run_pipeline(job_id: str):
    """
    Internal worker: runs the full pipeline for a given job_id.

    Steps:
      1. Get image sources (URLs or file paths) from JOB_STORE
      2. BLIP-2 captions (detailed image descriptions)
      3. Summary via Qwen (narrative story)
      4. Lyrics via Qwen (song lyrics)
      5. Vocals via Bark TTS (singing/speech)
      6. Package + update JOB_STORE
    """
    if job_id not in JOB_STORE:
        raise RuntimeError(f"Job {job_id} not found")

    job = dict(JOB_STORE[job_id])  # copy
    image_urls = job.get("image_urls", [])
    image_paths = job.get("image_paths", [])
    genre = job.get("genre", "pop")
    mood = job.get("mood", "nostalgic")

    # Combine URLs and paths into one list of sources
    image_sources = image_urls + image_paths

    if not image_sources:
        JOB_STORE[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "error": "No image sources (URLs or paths) stored on job",
        }
        return

    # Update status
    JOB_STORE[job_id] = {**job, "status": "processing"}

    try:
        # 1) Captions
        captions = generate_photo_captions(image_sources, device="cuda")

        # 2) Summary
        summary = summarize_captions(captions)

        # 3) Lyrics
        lyrics = generate_lyrics(summary, genre=genre, mood=mood)

        # Ensure we have a persistent directory for generated audio
        audio_dir = "/audio"
        os.makedirs(audio_dir, exist_ok=True)

        # 4) Vocals from lyrics (Bark)
        audio_path = generate_vocals(
            job_id=job_id,
            lyrics=lyrics,
            out_dir=audio_dir,
        )
        AUDIO_VOLUME.commit()

        # 5) Package result
        result = package_result(
            job_id=job_id,
            captions=captions,
            summary=summary,
            lyrics=lyrics,
            audio_path=audio_path,
        )

        JOB_STORE[job_id] = result

    except Exception as e:
        JOB_STORE[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }
        raise


@app.function(image=backend_image, timeout=300)
@fastapi_endpoint(method="POST")
def submit_job(body: SubmitJobRequest):
    """
    POST /submit_job

    Body:
      { "job_id": "...", "genre": "pop", "mood": "nostalgic" }

    Returns:
      { "job_id": "...", "status": "queued" }
    """
    job_id = body.job_id

    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = dict(JOB_STORE[job_id])

    if job.get("status") not in ("created", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Job is already in status {job.get('status')}",
        )

    image_urls = job.get("image_urls", [])
    image_paths = job.get("image_paths", [])
    
    if not image_urls and not image_paths:
        raise HTTPException(
            status_code=400,
            detail="Job has no images stored; call /upload_photo or /upload_photo_files first",
        )

    job["genre"] = body.genre
    job["mood"] = body.mood
    job["status"] = "queued"
    JOB_STORE[job_id] = job

    # Spawn GPU pipeline
    _run_pipeline.spawn(job_id)

    return {"job_id": job_id, "status": "queued"}
