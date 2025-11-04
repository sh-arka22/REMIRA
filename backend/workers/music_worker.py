# backend/workers/music_worker.py

import os
from typing import Optional

import torch
import soundfile as sf
from diffusers import StableAudioPipeline

STABLE_AUDIO_REPO = "stabilityai/stable-audio-open-1.0"

_audio_pipe: Optional[StableAudioPipeline] = None


def _ensure_audio_pipe(device: str = None):
    """
    Lazy-load Stable Audio Open 1.0 via Diffusers.
    """
    global _audio_pipe
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if _audio_pipe is None:
        _audio_pipe = StableAudioPipeline.from_pretrained(
            STABLE_AUDIO_REPO,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        _audio_pipe = _audio_pipe.to(device)


def generate_music(
    job_id: str,
    lyrics: str,
    genre: str,
    mood: str,
    out_dir: str = "/tmp",
    seconds: float = 30.0,
) -> str:
    """
    Generate melodious instrumental music using Stable Audio Open.
    Extracts themes from lyrics to create contextual music.

    Returns: local path to WAV file.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _ensure_audio_pipe(device)

    # Extract key themes/words from lyrics for more relevant music
    lyrics_words = lyrics.replace("[Verse 1]", "").replace("[Verse 2]", "")
    lyrics_words = lyrics_words.replace("[Chorus]", "").replace("[Bridge]", "")
    theme_snippet = ' '.join(lyrics_words.split()[:15])  # First 15 words

    # Enhanced prompt with lyrics context
    prompt = (
        f"Beautiful {genre} instrumental song, {mood} emotional melody, "
        f"warm harmonies, gentle rhythm, melodious and uplifting, "
        f"cinematic quality, inspired by themes of {theme_snippet}, "
        f"professional studio recording, clear and balanced mix"
    )
    negative_prompt = (
        "low quality, distorted, noisy, off-key, harsh, clipping, dissonant, "
        "amateur, poor recording, muddy, chaotic"
    )

    print(f"Generating {seconds}s of {genre} music with {mood} mood...")

    generator = torch.Generator(device).manual_seed(0)

    result = _audio_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=150,  # Higher for better quality
        guidance_scale=7.0,
        audio_end_in_s=seconds,
        num_waveforms_per_prompt=1,
        generator=generator,
    )

    audio = result.audios[0]  # [channels, samples]
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{job_id}_music.wav")

    # Use the pipeline's sample rate
    sr = _audio_pipe.vae.sampling_rate
    sf.write(out_path, audio.T, sr)  # (samples, channels)
    
    print(f"Music generated and saved to {out_path}")

    return out_path


def mix_audio_tracks(
    music_path: str,
    vocals_path: str,
    output_path: str,
    music_volume_db: int = -8,
    vocals_volume_db: int = 0,
) -> str:
    """
    Mix instrumental music with vocals into a final track.
    
    Args:
        music_path: Path to instrumental music WAV
        vocals_path: Path to vocals WAV
        output_path: Path for final mixed output
        music_volume_db: Volume adjustment for music (negative = quieter)
        vocals_volume_db: Volume adjustment for vocals
    
    Returns: Path to mixed audio file
    """
    try:
        from pydub import AudioSegment
        
        print(f"Mixing audio: music={music_path}, vocals={vocals_path}")
        
        # Load audio files
        music = AudioSegment.from_wav(music_path)
        vocals = AudioSegment.from_wav(vocals_path)
        
        # Adjust volumes
        music = music + music_volume_db  # Make music quieter
        vocals = vocals + vocals_volume_db  # Keep vocals clear
        
        # Ensure both tracks are same length (use shorter duration)
        min_duration = min(len(music), len(vocals))
        music = music[:min_duration]
        vocals = vocals[:min_duration]
        
        # Mix: overlay vocals on top of music
        final = music.overlay(vocals)
        
        # Normalize to prevent clipping
        final = final.normalize()
        
        # Export
        final.export(output_path, format="wav")
        
        print(f"Mixed audio saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error mixing audio: {e}")
        # Fallback: return vocals if mixing fails
        print("Falling back to vocals only")
        return vocals_path