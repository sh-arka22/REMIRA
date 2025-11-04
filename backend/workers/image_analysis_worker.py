# backend/workers/image_analysis_worker.py

from io import BytesIO
from typing import List, Union
import os

import requests
from PIL import Image
import torch

# Upgrade to BLIP-2 for much better captions (more detailed and accurate)
# Options:
# - "Salesforce/blip2-opt-2.7b" - Better quality, moderate size (RECOMMENDED)
# - "Salesforce/blip2-flan-t5-xl" - Best quality but larger
# - "Salesforce/blip-image-captioning-large" - Fallback if BLIP-2 has issues
BLIP_MODEL_NAME = os.environ.get("BLIP_MODEL", "Salesforce/blip2-opt-2.7b")
CAPTION_PROMPT = "Describe the photo in rich detail."

_blip_processor = None
_blip_model = None


def _ensure_blip(device: str = "cuda"):
    """Lazy-load the BLIP-2 captioning model."""
    global _blip_processor, _blip_model
    if _blip_processor is None or _blip_model is None:
        # Check if using BLIP-2 or BLIP-1
        is_blip2 = "blip2" in BLIP_MODEL_NAME.lower()
        
        if is_blip2:
            from transformers import Blip2Processor, Blip2ForConditionalGeneration
            _blip_processor = Blip2Processor.from_pretrained(BLIP_MODEL_NAME)
            _blip_model = Blip2ForConditionalGeneration.from_pretrained(
                BLIP_MODEL_NAME,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            ).to(device)
        else:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            _blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_NAME)
            _blip_model = BlipForConditionalGeneration.from_pretrained(
                BLIP_MODEL_NAME
            ).to(device)


def _load_image(source: str) -> Image.Image:
    """
    Load an image from either a URL or a local file path.
    
    Args:
        source: Either a URL (starting with http) or a local file path
        
    Returns:
        PIL Image in RGB mode
    """
    if source.startswith("http://") or source.startswith("https://"):
        # Load from URL
        resp = requests.get(source)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
    else:
        # Load from local file path
        if not os.path.exists(source):
            raise FileNotFoundError(f"Image file not found: {source}")
        img = Image.open(source).convert("RGB")
    
    return img


def generate_photo_captions(
    image_sources: List[str],
    device: str = "cuda"
) -> List[str]:
    """
    Generate captions for images from URLs or local file paths.
    
    Args:
        image_sources: List of image URLs or local file paths
        device: Device to run the model on ("cuda" or "cpu")

    Returns:
        List of captions, one per image.
    """
    _ensure_blip(device)
    captions: List[str] = []

    for source in image_sources:
        img = _load_image(source)

        # Prepare inputs
        is_blip2 = "blip2" in BLIP_MODEL_NAME.lower()
        
        if is_blip2:
            # BLIP-2 uses different input processing
            inputs = _blip_processor(
                images=img,
                text=CAPTION_PROMPT,
                return_tensors="pt",
            ).to(device)
            # Better generation parameters for BLIP-2
            with torch.no_grad():
                out = _blip_model.generate(
                    **inputs,
                    max_length=75,  # Longer captions for more detail
                    num_beams=5,
                    repetition_penalty=1.2,
                    length_penalty=1.0,
                )
            caption = _blip_processor.decode(out[0], skip_special_tokens=True)
        else:
            # Original BLIP processing
            inputs = _blip_processor(
                images=img,
                text=CAPTION_PROMPT,
                return_tensors="pt",
            ).to(device)
            with torch.no_grad():
                out = _blip_model.generate(
                    **inputs,
                    max_length=50,
                    num_beams=5,
                    repetition_penalty=1.1,
                )
            caption = _blip_processor.decode(out[0], skip_special_tokens=True)
        
        captions.append(caption)

    return captions
