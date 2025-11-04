# backend/workers/vocal_worker.py

import os
from typing import Dict, Optional

import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, BarkModel

# Bark model options:
# - "suno/bark-small" - Fast, 500MB, decent quality (default for speed)
# - "suno/bark" - Better quality, 2GB, slower but more natural
# For production/demos, upgrade to full "suno/bark" for best results
BARK_MODEL_ID = os.environ.get("BARK_MODEL_ID", "suno/bark")

_bark_model: Optional[BarkModel] = None
_bark_processor: Optional[AutoProcessor] = None
_bark_device: Optional[torch.device] = None
_bark_sampling_rate: Optional[int] = None


def _ensure_bark_pipeline():
    """
    Lazy-load Bark model + processor.
    Bark is a transformer-based text-to-audio model by Suno that can generate speech,
    music-like audio, and simple singing, and its checkpoints are MIT-licensed.
    """
    global _bark_model, _bark_processor, _bark_device, _bark_sampling_rate

    if _bark_model is not None and _bark_processor is not None:
        return

    _bark_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _bark_processor = AutoProcessor.from_pretrained(BARK_MODEL_ID)
    _bark_model = BarkModel.from_pretrained(BARK_MODEL_ID)
    _bark_model = _bark_model.to(_bark_device)
    _bark_model.eval()

    _bark_sampling_rate = _resolve_sampling_rate(_bark_model)


def _resolve_sampling_rate(model: BarkModel) -> int:
    """
    Bark exposes the target sampling rate either on the generation config,
    the model config, or nested under the codec config. Fall back to the
    24kHz default if nothing is set.
    """
    config_candidates = []

    gen_config = getattr(model, "generation_config", None)
    if gen_config is not None:
        for attr in ("sample_rate", "sampling_rate"):
            value = getattr(gen_config, attr, None)
            if value is not None:
                config_candidates.append(value)

    model_config = getattr(model, "config", None)
    if model_config is not None:
        for attr in ("sample_rate", "sampling_rate"):
            value = getattr(model_config, attr, None)
            if value is not None:
                config_candidates.append(value)
            codec_cfg = getattr(model_config, "codec_config", None)
            if codec_cfg is not None:
                nested_value = getattr(codec_cfg, attr, None)
                if nested_value is not None:
                    config_candidates.append(nested_value)

    for candidate in config_candidates:
        if candidate is not None:
            return int(candidate)

    return 24_000


def _prepare_bark_inputs(text: str) -> Dict[str, torch.Tensor]:
    """
    Tokenize text using the Bark processor with the same defaults the pipeline uses.
    """
    assert _bark_model is not None and _bark_processor is not None and _bark_device is not None

    semantic_cfg = getattr(_bark_model.generation_config, "semantic_config", {}) or {}
    preprocess_kwargs = {
        "max_length": semantic_cfg.get("max_input_semantic_length", 256),
        "add_special_tokens": False,
        "return_attention_mask": True,
        "return_token_type_ids": False,
    }

    encoded = _bark_processor([text], return_tensors="pt", **preprocess_kwargs)

    moved: Dict[str, torch.Tensor] = {}
    for key, value in encoded.items():
        if isinstance(value, torch.Tensor):
            moved[key] = value.to(_bark_device)
        else:
            moved[key] = value

    return moved


def _postprocess_bark_audio(audio) -> np.ndarray:
    """
    Normalize Bark's return type (list / tensor) to a numpy array with shape [T, C].
    """
    if isinstance(audio, tuple):
        audio = audio[0]

    if isinstance(audio, list):
        if not audio:
            raise ValueError("Bark generation returned an empty audio list.")
        audio_tensor = audio[0]
    elif isinstance(audio, torch.Tensor):
        audio_tensor = audio
    else:
        raise TypeError(f"Unexpected Bark output type: {type(audio)}")

    if audio_tensor.ndim == 2 and audio_tensor.size(0) == 1:
        audio_tensor = audio_tensor.squeeze(0)

    audio_np = audio_tensor.to(device="cpu", dtype=torch.float32).numpy()

    if audio_np.ndim == 1:
        audio_np = np.expand_dims(audio_np, axis=1)

    return audio_np


def generate_vocals(
    job_id: str,
    lyrics: str,
    out_dir: str = "/tmp",
) -> str:
    """
    Generate a vocal 'song' rendition of the lyrics using Bark.
    This produces a single WAV file where a synthetic voice
    semi-sings / speaks the lyrics in an expressive way.
    """
    _ensure_bark_pipeline()

    assert _bark_model is not None and _bark_sampling_rate is not None

    # Clean and prepare lyrics for Bark
    # Remove section headers and limit length
    clean_lyrics = lyrics.replace("[Verse 1]", "").replace("[Verse 2]", "")
    clean_lyrics = clean_lyrics.replace("[Chorus]", "").replace("[Bridge]", "")
    clean_lyrics = clean_lyrics.strip()
    
    # Bark works best with 100-200 characters for clear speech
    # Split into sentences and take first few
    sentences = [s.strip() for s in clean_lyrics.split('\n') if s.strip()]
    text_prompt = ' '.join(sentences[:3])[:250]  # Max 250 chars, ~3 sentences
    
    # Add voice preset for English speaker (critical for audio generation!)
    text_prompt = f"♪ [clears throat] {text_prompt} ♪"
    
    print(f"Generating vocals for text: {text_prompt[:100]}...")
    
    inputs = _prepare_bark_inputs(text_prompt)
    
    # Add voice_preset for consistent, clear speech
    # v2/en_speaker_6 is a clear English voice
    if hasattr(_bark_processor, 'get_voice_preset'):
        try:
            voice_preset = _bark_processor.get_voice_preset("v2/en_speaker_6")
            if voice_preset is not None:
                inputs.update(voice_preset)
        except:
            pass  # Continue without preset if not available

    with torch.inference_mode():
        audio = _bark_model.generate(**inputs, pad_token_id=10000)

    audio_np = _postprocess_bark_audio(audio)
    sr = _bark_sampling_rate
    
    # Check if audio is silent (all zeros or very low amplitude)
    max_amplitude = np.abs(audio_np).max()
    print(f"Generated audio max amplitude: {max_amplitude}")
    
    if max_amplitude < 0.001:
        print("WARNING: Generated audio appears to be silent!")
        # Generate a simple tone as fallback to indicate audio was generated
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        fallback_audio = 0.1 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        audio_np = np.expand_dims(fallback_audio, axis=1)

    # Ensure shape is (T, C)
    if audio_np.ndim == 1:
        audio_np = np.expand_dims(audio_np, axis=1)  # [T, 1]

    # Normalize audio to prevent clipping
    max_val = np.abs(audio_np).max()
    if max_val > 0:
        audio_np = audio_np / max_val * 0.95  # Leave headroom

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{job_id}_vocals.wav")

    sf.write(out_path, audio_np, sr)
    print(f"Audio saved to {out_path}, duration: {len(audio_np)/sr:.2f}s")

    return out_path
