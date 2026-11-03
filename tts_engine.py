"""
TTS & Inference Engine for AutoVoiceStudio:
- Vietnamese Edge-TTS voice generation (Nam Minh / Hoài My)
- RVC Voice Conversion using trained model weights (.pth) & index (.index)
"""

import os
import sys
import uuid
import asyncio
import edge_tts
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPLIO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Applio-RVC"))
VOICE_BANKS_DIR = os.path.join(BASE_DIR, "voice_banks")
TEMP_DIR = os.path.join(BASE_DIR, "temp_downloads")

if APPLIO_DIR not in sys.path:
    sys.path.insert(0, APPLIO_DIR)


async def generate_edge_tts(text: str, voice: str = "vi-VN-NamMinhNeural", output_file: str = None) -> str:
    """Generate high quality Vietnamese synthetic speech via Microsoft Edge-TTS."""
    if not output_file:
        output_file = os.path.join(TEMP_DIR, f"tts_{uuid.uuid4().hex[:8]}.mp3")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file


def convert_to_wav(input_file: str, output_wav: str) -> str:
    """Convert any audio file to 48kHz Mono 16-bit PCM WAV using FFmpeg."""
    from audio_processor import get_ffmpeg
    ffmpeg_bin = get_ffmpeg()
    cmd = [
        ffmpeg_bin, "-y",
        "-i", input_file,
        "-ar", "48000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_wav
    ]
    subprocess.run(cmd, check=True)
    return output_wav


def convert_voice(
    input_audio_path: str,
    character_id: str,
    pitch: int = 0,
    index_rate: float = 0.9,
    protect: float = 0.33,
    f0_method: str = "rmvpe"
) -> str:
    """Convert audio into the character's cloned voice using trained RVC weights."""
    import core

    # 1. Locate model .pth and .index
    model_dir = os.path.join(VOICE_BANKS_DIR, character_id, "model")
    pth_candidates = [
        os.path.join(model_dir, f"{character_id}.pth"),
        os.path.join(APPLIO_DIR, "assets", "weights", f"{character_id}.pth"),
    ]
    pth_path = None
    for c in pth_candidates:
        if os.path.exists(c):
            pth_path = c
            break

    if not pth_path:
        raise FileNotFoundError(f"Chưa tìm thấy model đã train ({character_id}.pth). Hãy bấm 'Train Model' trước!")

    index_candidates = [
        os.path.join(model_dir, f"{character_id}.index"),
    ]
    # Check Applio logs
    import glob
    applio_indexes = glob.glob(os.path.join(APPLIO_DIR, "logs", character_id, "added_*.index"))
    if applio_indexes:
        index_candidates.append(max(applio_indexes, key=os.path.getmtime))

    index_path = ""
    for c in index_candidates:
        if os.path.exists(c):
            index_path = c
            break

    output_path = os.path.join(TEMP_DIR, f"clone_{character_id}_{uuid.uuid4().hex[:8]}.wav")

    # Run inference via Applio core
    msg, final_out = core.run_infer_script(
        pitch=pitch,
        index_rate=index_rate,
        volume_envelope=1.0,
        protect=protect,
        f0_method=f0_method,
        input_path=input_audio_path,
        output_path=output_path,
        pth_path=pth_path,
        index_path=index_path,
        f0_autotune=False,
        f0_autotune_strength=1.0,
        proposed_pitch=False,
        proposed_pitch_threshold=0.0,
        export_format="WAV",
        embedder_model="contentvec",
    )

    return final_out
