# backend/api/get_status.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import HTTPException
from modal import fastapi_endpoint

from modal_app import app, backend_image, JOB_STORE


@app.function(image=backend_image, timeout=120)
@fastapi_endpoint(method="GET")
def get_status(job_id: str):
    """
    GET /get_status?job_id=...

    Returns the full job object, including status.
    """
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")

    return JOB_STORE[job_id]