# backend/api/upload_photo.py

from typing import List, Optional
import uuid
import os

from pydantic import BaseModel, Field
from fastapi import HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modal import fastapi_endpoint
from modal_app import app, backend_image, JOB_STORE, PHOTOS_VOLUME


class UploadPhotoRequest(BaseModel):
    image_urls: List[str] = Field(
        ..., min_items=1, description="Array of publicly accessible image URLs"
    )


# Endpoint for URL-based uploads (backward compatible)
@app.function(image=backend_image, timeout=300)
@fastapi_endpoint(method="POST")
def upload_photo(body: UploadPhotoRequest):
    """
    POST /upload_photo

    Body:
      {
        "image_urls": ["https://.../img1.jpg", ...]
      }

    Returns:
      {
        "job_id": "...",
        "status": "created"
      }
    """
    if not body.image_urls:
        raise HTTPException(status_code=400, detail="No image URLs provided")

    job_id = str(uuid.uuid4())

    JOB_STORE[job_id] = {
        "job_id": job_id,
        "status": "created",
        "image_urls": body.image_urls,
        "image_paths": [],  # Empty for URL-based uploads
        # genre / mood filled at /submit_job
    }

    return {"job_id": job_id, "status": "created"}


# New endpoint for file uploads
@app.function(
    image=backend_image,
    timeout=600,
    volumes={"/photos": PHOTOS_VOLUME}
)
@fastapi_endpoint(method="POST")
async def upload_photo_files(files: List[UploadFile] = File(...)):
    """
    POST /upload_photo_files

    Upload actual image files (multipart/form-data).
    Accepts multiple files.

    Returns:
      {
        "job_id": "...",
        "status": "created",
        "uploaded_count": 3
      }
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    job_id = str(uuid.uuid4())
    job_dir = f"/photos/{job_id}"
    os.makedirs(job_dir, exist_ok=True)

    image_paths = []
    uploaded_count = 0

    for idx, file in enumerate(files):
        # Validate file type
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            continue

        # Generate safe filename
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        safe_filename = f"photo_{idx}{ext}"
        file_path = os.path.join(job_dir, safe_filename)

        # Save file to volume
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        image_paths.append(file_path)
        uploaded_count += 1

    # Commit the volume so files persist
    PHOTOS_VOLUME.commit()

    if uploaded_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No valid image files found. Please upload image files."
        )

    JOB_STORE[job_id] = {
        "job_id": job_id,
        "status": "created",
        "image_urls": [],  # Empty for file-based uploads
        "image_paths": image_paths,
        # genre / mood filled at /submit_job
    }

    return {
        "job_id": job_id,
        "status": "created",
        "uploaded_count": uploaded_count
    }