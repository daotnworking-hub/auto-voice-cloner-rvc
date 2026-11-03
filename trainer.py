"""
Training Coordinator for AutoVoiceStudio & RTX 4060
Wraps Applio RVC training pipeline with live progress monitoring and model export.
"""

import os
import sys
import glob
import time
import shutil
import threading
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPLIO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Applio-RVC"))
VOICE_BANKS_DIR = os.path.join(BASE_DIR, "voice_banks")

# Ensure Applio is in sys.path
if APPLIO_DIR not in sys.path:
    sys.path.insert(0, APPLIO_DIR)


class TrainingManager:
    def __init__(self):
        self.state = {
            "status": "idle",  # idle, preprocessing, extracting, training, indexing, completed, error
            "character_id": None,
            "step_name": "",
            "epoch": 0,
            "total_epoch": 250,
            "percent": 0.0,
            "logs": [],
            "error": None,
            "model_path": None,
            "index_path": None,
        }
        self._thread = None
        self._process = None
        self._stop_requested = False

    def get_status(self):
        return dict(self.state)

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.state["logs"].append(entry)
        if len(self.state["logs"]) > 200:
            self.state["logs"].pop(0)
        print(entry)

    def stop_training(self):
        self._stop_requested = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
        self.state["status"] = "idle"
        self.state["step_name"] = "Đã dừng bởi người dùng"
        self.log("Quá trình train đã được dừng.")

    def start_training(self, character_id: str, epochs: int = 250, batch_size: int = 8):
        if self.state["status"] in ["preprocessing", "extracting", "training", "indexing"]:
            return False, "Một tiến trình train khác đang chạy!"

        dataset_path = os.path.join(VOICE_BANKS_DIR, character_id, "clean")
        wav_files = glob.glob(os.path.join(dataset_path, "*.wav"))
        if not wav_files:
            return False, f"Không tìm thấy file vocal sạch nào trong ngân hàng {character_id}!"

        self._stop_requested = False
        self.state.update({
            "status": "preprocessing",
            "character_id": character_id,
            "step_name": "Đang tiền xử lý cắt mẫu âm thanh (Preprocessing)...",
            "epoch": 0,
            "total_epoch": epochs,
            "percent": 1.0,
            "logs": [],
            "error": None,
            "model_path": None,
            "index_path": None,
        })

        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(character_id, dataset_path, epochs, batch_size),
            daemon=True
        )
        self._thread.start()
        return True, "Bắt đầu tiến trình train tối ưu cho RTX 4060!"

    def _run_pipeline(self, character_id: str, dataset_path: str, epochs: int, batch_size: int):
        try:
            import core
            from rvc.lib.tools.prerequisites_download import ensure_pretrained

            python_exe = sys.executable
            sample_rate = 48000
            cpu_cores = min(os.cpu_count() or 8, 12)

            # --- BƯỚC 1: PREPROCESS ---
            self.log(f"Bắt đầu Preprocess cho model '{character_id}' (Tách cắt 48kHz HiFi, {cpu_cores} CPUs)...")
            self.state["status"] = "preprocessing"
            self.state["step_name"] = "Bước 1/4: Phân đoạn dữ liệu âm thanh thoại (Preprocessing)"
            self.state["percent"] = 5.0

            res_pre = core.run_preprocess_script(
                model_name=character_id,
                dataset_path=dataset_path,
                sample_rate=sample_rate,
                cpu_cores=cpu_cores,
                cut_preprocess="True",
                process_effects=False,
                chunk_len=3.0,
                overlap_len=0.3,
                normalization_mode="none",
            )
            self.log(f"Preprocess hoàn tất: {res_pre}")

            if self._stop_requested:
                return

            # --- BƯỚC 2: EXTRACT PITCH (RMVPE) & FEATURES ---
            self.log(f"Bắt đầu trích xuất cao độ F0 (RMVPE) & ContentVec Features trên GPU CUDA...")
            self.state["status"] = "extracting"
            self.state["step_name"] = "Bước 2/4: Trích xuất cao độ chuẩn RMVPE và đặc trưng giọng nói"
            self.state["percent"] = 15.0

            res_ext = core.run_extract_script(
                model_name=character_id,
                f0_method="rmvpe",
                cpu_cores=cpu_cores,
                gpu=0,
                sample_rate=sample_rate,
                embedder_model="contentvec",
                embedder_model_custom=None,
                include_mutes=2,
            )
            self.log(f"Extract hoàn tất: {res_ext}")

            if self._stop_requested:
                return

            # --- BƯỚC 3: TRAIN VỚI CẤU HÌNH TỐI ƯU RTX 4060 ---
            self.log(f"Bắt đầu huấn luyện mạng nơ-ron (HiFi-GAN v2, Epochs={epochs}, BatchSize={batch_size}, CacheGPU=ON)...")
            self.state["status"] = "training"
            self.state["step_name"] = f"Bước 3/4: Huấn luyện mạng nơ-ron sâu (Deep Neural Training: 0/{epochs})"
            self.state["percent"] = 20.0

            pg, pd = ensure_pretrained("HiFi-GAN", sample_rate)
            train_py = os.path.join(APPLIO_DIR, "rvc", "train", "train.py")

            cmd = [
                python_exe,
                "-u",
                train_py,
                character_id,
                "25",  # save_every_epoch
                str(epochs),
                pg,
                pd,
                "0",  # GPU 0
                str(batch_size),
                str(sample_rate),
                "False",  # save_only_latest
                "True",   # save_every_weights
                "True",   # cache_data_in_gpu (32GB RAM + 8GB VRAM)
                "False",  # cleanup
                "HiFi-GAN",
                "False",  # checkpointing
            ]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
                cwd=APPLIO_DIR,
            )

            # Đọc log trực tiếp từ tiến trình train
            for line in self._process.stdout:
                if self._stop_requested:
                    break
                line = line.strip()
                if not line:
                    continue

                if "epoch=" in line:
                    try:
                        parts = line.split("|")
                        for p in parts:
                            if "epoch=" in p:
                                ep = int(p.split("=")[1].strip())
                                self.state["epoch"] = ep
                                train_pct = 20.0 + round((ep / float(epochs)) * 70.0, 1)
                                self.state["percent"] = min(90.0, train_pct)
                                self.state["step_name"] = f"Bước 3/4: Huấn luyện mạng nơ-ron sâu ({ep}/{epochs} Epochs - {round((ep/epochs)*100, 1)}%)"
                    except Exception:
                        pass
                    self.log(line)
                elif any(keyword in line.lower() for keyword in ["step", "loss", "saving", "optimizer", "starting"]):
                    self.log(line)

            self._process.wait()

            if self._stop_requested:
                return

            # --- BƯỚC 4: INDEX CREATION (Faiss) ---
            self.log(f"Bắt đầu tạo chỉ mục nhận diện giọng nói (Feature Indexing - Faiss)...")
            self.state["status"] = "indexing"
            self.state["step_name"] = "Bước 4/4: Xây dựng chỉ mục âm vực Faiss Index (Tối ưu độ giống)"
            self.state["percent"] = 92.0

            core.run_index_script(character_id, "Auto")
            self.log("Index xây dựng hoàn tất!")

            # --- BƯỚC 5: XUẤT VÀ LƯU TRỮ MODEL VÀO VOICE BANK ---
            model_bank_dir = os.path.join(VOICE_BANKS_DIR, character_id, "model")
            os.makedirs(model_bank_dir, exist_ok=True)

            # Copy .pth
            pth_src = os.path.join(APPLIO_DIR, "assets", "weights", f"{character_id}.pth")
            if os.path.exists(pth_src):
                pth_dest = os.path.join(model_bank_dir, f"{character_id}.pth")
                shutil.copy2(pth_src, pth_dest)
                self.state["model_path"] = pth_dest
                self.log(f"Đã lưu trọng số giọng: {pth_dest}")

            # Copy .index
            index_candidates = glob.glob(os.path.join(APPLIO_DIR, "logs", character_id, "added_*.index"))
            if index_candidates:
                latest_index = max(index_candidates, key=os.path.getmtime)
                index_dest = os.path.join(model_bank_dir, f"{character_id}.index")
                shutil.copy2(latest_index, index_dest)
                self.state["index_path"] = index_dest
                self.log(f"Đã lưu chỉ mục Index: {index_dest}")

            self.state["status"] = "completed"
            self.state["step_name"] = f"Huấn luyện thành công hoàn hảo 100%! Model {character_id} sẵn sàng sử dụng."
            self.state["percent"] = 100.0
            self.log(f"=== HUẤN LUYỆN MODEL {character_id} HOÀN TẤT THÀNH CÔNG RỰC RỠ! ===")

        except Exception as e:
            self.state["status"] = "error"
            self.state["error"] = str(e)
            self.state["step_name"] = f"Lỗi trong quá trình train: {str(e)}"
            self.log(f"[LỖI CRITICAL]: {str(e)}")
        finally:
            self._process = None


trainer = TrainingManager()
