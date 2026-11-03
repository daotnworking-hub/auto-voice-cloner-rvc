"""
AutoVoiceStudio - FastAPI Web Application
Automated Voice Ingestion (YouTube/Demucs GPU), Incremental Voice Banks (% Completeness),
1-Click RTX 4060 Training Pipeline & Real-Time Voice Cloning Studio.
"""

import os
import sys
import glob
import shutil
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_BANKS_DIR = os.path.join(BASE_DIR, "voice_banks")
TEMP_DIR = os.path.join(BASE_DIR, "temp_downloads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(VOICE_BANKS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

import audio_processor
from trainer import trainer
import tts_engine

app = FastAPI(title="AutoVoiceStudio", version="2.0.0")


# --- DATA MODELS ---
class CreateBankRequest(BaseModel):
    character_id: str
    display_name: Optional[str] = ""

class YouTubeIngestRequest(BaseModel):
    url: str

class TrainRequest(BaseModel):
    character_id: str
    epochs: Optional[int] = 250
    batch_size: Optional[int] = 8

class TTSRequest(BaseModel):
    text: str
    character_id: str
    voice: Optional[str] = "vi-VN-NamMinhNeural"
    pitch: Optional[int] = 0
    index_rate: Optional[float] = 0.95


# --- API ROUTES ---

@app.get("/api/banks")
def list_banks():
    banks = []
    if os.path.exists(VOICE_BANKS_DIR):
        for d in os.listdir(VOICE_BANKS_DIR):
            full_path = os.path.join(VOICE_BANKS_DIR, d)
            if os.path.isdir(full_path):
                stats = audio_processor.get_character_voice_bank(d)
                # Check if model already trained
                model_pth = os.path.join(full_path, "model", f"{d}.pth")
                stats["has_model"] = os.path.exists(model_pth)
                banks.append(stats)
    return {"banks": banks}


@app.post("/api/banks")
def create_bank(req: CreateBankRequest):
    cid = req.character_id.strip().lower().replace(" ", "_")
    cid = "".join(c for c in cid if c.isalnum() or c == "_")
    if not cid:
        raise HTTPException(status_code=400, detail="Tên ngân hàng giọng không hợp lệ!")
    
    bank_dir = os.path.join(VOICE_BANKS_DIR, cid, "clean")
    os.makedirs(bank_dir, exist_ok=True)
    return audio_processor.get_character_voice_bank(cid)


@app.get("/api/banks/{character_id}")
def get_bank(character_id: str):
    bank_dir = os.path.join(VOICE_BANKS_DIR, character_id)
    if not os.path.exists(bank_dir):
        raise HTTPException(status_code=404, detail="Không tìm thấy ngân hàng giọng!")
    
    stats = audio_processor.get_character_voice_bank(character_id)
    model_pth = os.path.join(bank_dir, "model", f"{character_id}.pth")
    stats["has_model"] = os.path.exists(model_pth)
    return stats


@app.post("/api/banks/{character_id}/youtube")
def ingest_youtube(character_id: str, req: YouTubeIngestRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Vui lòng nhập đường link YouTube hợp lệ!")

    try:
        # 1. Download YouTube audio stream
        uid = uuid.uuid4().hex[:8]
        raw_name = f"yt_{character_id}_{uid}"
        dl_res = audio_processor.download_youtube_audio(url, raw_name)
        raw_path = dl_res["path"]

        # 2. Separate clean vocals via Demucs GPU
        target_dir = os.path.join(VOICE_BANKS_DIR, character_id, "clean")
        os.makedirs(target_dir, exist_ok=True)
        final_vocal_path = os.path.join(target_dir, f"vocal_yt_{uid}.wav")
        audio_processor.isolate_vocals_demucs(raw_path, final_vocal_path)

        # Cleanup raw download
        try:
            if os.path.exists(raw_path):
                os.remove(raw_path)
        except Exception:
            pass

        # Return updated stats
        return audio_processor.get_character_voice_bank(character_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải hoặc lọc giọng: {str(e)}")


@app.post("/api/banks/{character_id}/upload")
async def ingest_upload(character_id: str, file: UploadFile = File(...)):
    try:
        uid = uuid.uuid4().hex[:8]
        ext = os.path.splitext(file.filename)[1] or ".wav"
        temp_raw = os.path.join(TEMP_DIR, f"upload_{character_id}_{uid}{ext}")
        with open(temp_raw, "wb") as f:
            content = await file.read()
            f.write(content)

        target_dir = os.path.join(VOICE_BANKS_DIR, character_id, "clean")
        os.makedirs(target_dir, exist_ok=True)
        final_vocal_path = os.path.join(target_dir, f"vocal_up_{uid}.wav")

        # Separate clean vocals via Demucs GPU
        audio_processor.isolate_vocals_demucs(temp_raw, final_vocal_path)

        # Cleanup raw upload
        try:
            if os.path.exists(temp_raw):
                os.remove(temp_raw)
        except Exception:
            pass

        return audio_processor.get_character_voice_bank(character_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file upload: {str(e)}")


@app.delete("/api/banks/{character_id}/clips/{filename}")
def delete_clip(character_id: str, filename: str):
    target = os.path.join(VOICE_BANKS_DIR, character_id, "clean", filename)
    if os.path.exists(target):
        os.remove(target)
        return audio_processor.get_character_voice_bank(character_id)
    raise HTTPException(status_code=404, detail="Không tìm thấy file clip!")


# --- TRAINING ROUTES ---

@app.post("/api/train/start")
def start_train(req: TrainRequest):
    ok, msg = trainer.start_training(
        character_id=req.character_id,
        epochs=req.epochs or 250,
        batch_size=req.batch_size or 8
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "state": trainer.get_status()}


@app.post("/api/train/stop")
def stop_train():
    trainer.stop_training()
    return {"message": "Đã gửi lệnh dừng tiến trình train.", "state": trainer.get_status()}


@app.get("/api/train/status")
def train_status():
    return trainer.get_status()


# --- VOICE TESTING / TTS PREVIEW ---

@app.post("/api/tts/generate")
async def generate_cloned_voice(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Vui lòng nhập văn bản muốn đọc!")

    try:
        # 1. Generate base speech via Edge-TTS
        temp_tts_mp3 = await tts_engine.generate_edge_tts(text, voice=req.voice)
        temp_tts_wav = temp_tts_mp3.replace(".mp3", ".wav")
        tts_engine.convert_to_wav(temp_tts_mp3, temp_tts_wav)

        # 2. Convert voice via RVC trained model
        converted_wav = tts_engine.convert_voice(
            input_audio_path=temp_tts_wav,
            character_id=req.character_id,
            pitch=req.pitch,
            index_rate=req.index_rate,
        )

        filename = os.path.basename(converted_wav)
        return {
            "success": True,
            "filename": filename,
            "audio_url": f"/audio/preview/{filename}",
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi sinh giọng clone: {str(e)}")


# --- AUDIO PLAYBACK ROUTES ---

@app.get("/audio/preview/{filename}")
def stream_preview(filename: str):
    p = os.path.join(TEMP_DIR, filename)
    if os.path.exists(p):
        return FileResponse(p, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="File preview không tồn tại")


@app.get("/audio/bank/{character_id}/{filename}")
def stream_bank_clip(character_id: str, filename: str):
    p = os.path.join(VOICE_BANKS_DIR, character_id, "clean", filename)
    if os.path.exists(p):
        return FileResponse(p, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="File vocal không tồn tại")


# Serve static web frontend
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auto_studio:app", host="127.0.0.1", port=7865, reload=False)
