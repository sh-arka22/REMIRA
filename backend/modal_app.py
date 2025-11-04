# backend/modal_app.py

import os
import modal

app = modal.App("family-photo-song-backend")

# Simple persistent KV store for jobs
JOB_STORE = modal.Dict.from_name(
    "family-photo-song-jobs", create_if_missing=True
)

# Volume to store uploaded photos
PHOTOS_VOLUME = modal.Volume.from_name(
    "family-photo-uploads", create_if_missing=True
)

# Volume to store generated audio files
AUDIO_VOLUME = modal.Volume.from_name(
    "family-audio-output", create_if_missing=True
)

# Base image with all deps (all open-source)
# Version pinning strategy:
# - torch==2.3.1: Newer PyTorch with _pytree.register_pytree_node API
# - numpy<2: Avoid NumPy 2.x compatibility issues with compiled modules
# - transformers==4.45.2 & diffusers==0.31.0: Compatible with torch 2.3.1
backend_image = (
    modal.Image.debian_slim()
    .pip_install(
        # Core ML stack
        "torch==2.3.1",
        "accelerate==0.33.0",
        "transformers==4.45.2",
        "sentencepiece",
        "safetensors",
        # Diffusers + audio
        "diffusers[audio]==0.31.0",
        # Audio / numeric libs
        "numpy<2",
        "scipy",
        "soundfile",
        # Vision / HTTP
        "requests",
        "Pillow",
        # Web framework
        "fastapi",
        "python-multipart",
        "pydantic",
    )
    .env({
        "LLMSTUDIO_API_URL": "https://unparsimonious-morris-excessively.ngrok-free.dev/v1/chat/completions",
        "LLMSTUDIO_MODEL_NAME": "qwen/qwen2.5-vl-7b",
        # "LLMSTUDIO_API_KEY": "optional-token",
        # Model selection (can override for better quality)
        "BLIP_MODEL": "Salesforce/blip2-flan-t5-xl",  # Best captions
        "BARK_MODEL_ID": "suno/bark",  # Better audio quality
    })
    .add_local_dir(
        os.path.dirname(__file__),
        remote_path="/root",
    )
)

# Choose your GPU type depending on Modal plan
GPU_TYPE = "A10G"  # e.g. "A100-40GB", "H100"

# ---- Optional local test entrypoint ----


@app.local_entrypoint()
def main():
    """
    Quick local dry-run of the pipeline (non-HTTP).

    Run:
        modal run backend.modal_app
    """
    from workers.image_analysis_worker import generate_photo_captions
    from workers.summary_worker import summarize_captions
    from workers.lyrics_worker import generate_lyrics
    from workers.vocal_worker import generate_vocals
    from workers.packaging_worker import package_result

    import uuid

    test_job_id = str(uuid.uuid4())
    sample_images = [
        "https://images.pexels.com/photos/1648374/pexels-photo-1648374.jpeg",
        "https://images.pexels.com/photos/2253879/pexels-photo-2253879.jpeg",
    ]

    print("Running local test job:", test_job_id)
    captions = generate_photo_captions(sample_images, device="cpu")
    summary = summarize_captions(captions)
    lyrics = generate_lyrics(summary, genre="acoustic", mood="nostalgic")
    audio_path = generate_vocals(
        job_id=test_job_id,
        lyrics=lyrics,
    )
    result = package_result(test_job_id, captions, summary, lyrics, audio_path)
    print(result)


# Ensure API endpoints are imported so Modal sees them on deploy
from api import upload_photo, submit_job, get_status, fetch_result, download_audio  # noqa: F401
