# backend/api/__init__.py
# This file just makes "api" a package so we can import modules cleanly.

from . import upload_photo  # noqa: F401
from . import submit_job    # noqa: F401
from . import get_status    # noqa: F401
from . import fetch_result   # noqa: F401
from . import download_audio  # noqa: F401
