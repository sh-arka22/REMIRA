# backend/workers/packaging_worker.py

import os
from typing import List, Dict, Any
from urllib.parse import quote_plus


def package_result(
    job_id: str,
    captions: List[str],
    summary: str,
    lyrics: str,
    audio_path: str,
    base_url: str = "https://sahaarkajyoti2018--family-photo-song-backend-download-audio.modal.run"
) -> Dict[str, Any]:
    """
    Prepare the result object stored in JOB_STORE.

    Returns a publicly accessible URL for the audio file.
    """
    audio_filename = os.path.basename(audio_path)
    # Full URL that the browser can access
    public_url = f"{base_url}?job_id={quote_plus(job_id)}"

    return {
        "job_id": job_id,
        "status": "complete",
        "captions": captions,
        "summary": summary,
        "lyrics": lyrics,
        # Return full Modal URL for browser access
        "audio_url": public_url,
        "audio_path": public_url,  # Keep for backward compatibility
        "audio_filename": audio_filename,
        "_audio_file_path": audio_path,  # Internal use only
    }
