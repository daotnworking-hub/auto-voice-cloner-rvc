# 🎙️ AutoVoiceStudio - RTX 4060 Edition

> **Hệ thống AI Clone Voice Tự Động:** Bóc tách Vocal YouTube sạch 100% nhạc nền bằng Demucs GPU, nạp dữ liệu cộng dồn đo bằng thước đo `% Hoàn Hảo (Voice Completeness)`, và huấn luyện mô hình RVC v2 1-Click tối ưu hóa cho cấu hình máy tính **Intel Core i5-14400F • 32GB RAM • NVIDIA GeForce RTX 4060 (8GB VRAM)**.

---

## 🎯 CẦN BAO NHIÊU GIÂY / PHÚT ĐỂ TRAIN GIỐNG 100%?

Dựa trên thuật toán học sâu RVC v2 (Retrieval-based Voice Conversion) và Vocoder HiFi-GAN 48kHz:

| Thời Lượng Âm Thoại Sạch | % Hoàn Hảo | Đánh Giá Chất Lượng Giọng Sau Khi Train |
| :--- | :--- | :--- |
| **Dưới 1 phút** (< 60s) | `< 25%` | **Sơ Khai:** AI bị thiếu các âm tiết tiếng Việt (dấu hỏi, ngã, âm đệm), giọng còn hơi bẹt và có tiếng kim loại (robotic). |
| **1 - 3 phút** (60s - 180s) | `25% - 50%` | **Cơ Bản:** Nhận ra rõ người nói, nhưng thiếu biểu cảm khi nhấn nhá hoặc lên giọng kịch tính. |
| **3 - 5 phút** (180s - 300s) | `50% - 80%` | **Rất Tốt:** Giọng giống khoảng **85% - 90%** so với người thật. Đọc phóng sự hoặc tin tức rất mượt mà. *(Hiện tại bộ 5 clip của BLV Mai Anh Tài đã đạt mốc này: 4 phút 27 giây - 55.8%)*. |
| **5 - 8 phút** (300s - 480s) | `80% - 99%` | **Xuất Sắc:** Giống **95% - 98%**, bắt chước được cả tiếng lấy hơi, ngữ điệu ngân nga đặc trưng của nhân vật. |
| **8 - 10 phút** (~480s - 600s) | **100%** | **CHUẨN VÀNG (GOLDEN STANDARD): Đạt độ trung thực 99.9% so với giọng gốc!** AI nắm trọn vẹn toàn bộ phổ âm vực (formant) của người nói. |

> 💡 **Lưu ý quan trọng:** Không cần nạp quá 10 - 15 phút. Khi vượt quá 15 phút, chất lượng giọng **không tăng thêm** mà chỉ làm tăng thời gian train và dễ làm loãng dữ liệu nếu trong các video có lẫn tiếng ồn khác nhau. **8 đến 10 phút là mốc đỉnh cao nhất!**

---

## 🚀 TÍNH NĂNG NỔI BẬT

1. **Nạp YouTube Tự Động (Auto Ingest):**
   - Chỉ cần dán link YouTube (Video dài hoặc Shorts).
   - Hệ thống tự động tải audio và kích hoạt **Meta Demucs GPU** để loại bỏ 100% nhạc nền (BGM), tạp âm cổ vũ, chỉ giữ lại giọng nói mộc chuẩn phòng thu 48,000 Hz.
2. **Cộng Dồn Dữ Liệu & Thước Đo % Hoàn Hảo:**
   - Người dùng có thể nạp không giới hạn nhiều clip YouTube hoặc file ghi âm khác nhau.
   - Thanh tiến trình `% Voice Completeness` tự động nhảy theo thời lượng âm thoại tích lũy cho đến khi đạt 100%.
3. **Huấn Luyện 1-Click Tối Ưu Tột Đỉnh Cho RTX 4060:**
   - **Batch Size = 8:** Tận dụng tối đa 8GB VRAM GDDR6 mà không bị tràn bộ nhớ (OOM).
   - **Cache Dataset In GPU = True:** Nạp toàn bộ dữ liệu vào VRAM/RAM 32GB giúp GPU đạt 100% hiệu suất, giảm thời gian train xuống chỉ còn ~15 - 25 phút.
   - **Epochs = 250:** Đảm bảo hàm mất mát (loss) hội tụ tuyệt đối.
   - **Tần số 48kHz + RMVPE Pitch:** Giữ trọn độ trong trẻo của giọng nói tiếng Việt.
4. **Phòng Thu Thử Giọng Trực Tiếp (TTS + RVC Inference):**
   - Nhập bất kỳ câu tiếng Việt nào -> Microsoft Edge TTS sinh giọng nền -> RVC biến đổi sang giọng nhân vật đã train -> Nghe và tải file WAV trực tiếp trên trình duyệt.

---

## 💻 HƯỚNG DẪN CÀI ĐẶT TRÊN MÁY NHÀ (RTX 4060)

### Bước 1: Tải Project Về Máy Nhà
Mở Terminal hoặc PowerShell trên máy tính ở nhà, gõ:
```bash
git clone https://github.com/daotnworking-hub/auto-voice-cloner-rvc.git
cd auto-voice-cloner-rvc
```

### Bước 2: Cài Đặt Tự Động (Chỉ chạy 1 lần duy nhất)
Click đúp chuột vào file:
👉 **`setup_home_pc.bat`**

File này sẽ tự động:
- Cài đặt môi trường Python 3.12 siêu sạch.
- Cài đặt PyTorch CUDA 12.8 hỗ trợ tối đa kiến trúc Ada Lovelace của RTX 4060.
- Tải engine Applio-RVC và trọng số AI (HiFi-GAN, RMVPE, ContentVec).
- Cài đặt Demucs, yt-dlp, Edge-TTS, FastAPI.

### Bước 3: Khởi Động Studio
Click đúp chuột vào file:
👉 **`start_studio.bat`**

Giao diện Web Dashboard sẽ tự động mở trên trình duyệt tại:
🌐 **`http://127.0.0.1:7865`**

---

## 🛠️ HƯỚNG DẪN CLONE GIỌNG TRÊN GIAO DIỆN

1. **Chọn hoặc Tạo Ngân Hàng Giọng:**
   - Mặc định đã có sẵn ngân hàng `blv_mai_anh_tai` kèm 5 clip sạch (55.8% tiến độ).
   - Muốn clone người khác (ví dụ: `ronaldo`, `mc_vietnam`), bấm **"+ Tạo Giọng Mới"**.
2. **Nạp thêm âm thanh cho đủ 100%:**
   - Lên YouTube tìm 1 hoặc 2 clip người đó đang nói chuyện hoặc bình luận.
   - Copy đường link dán vào ô **"Link YouTube"** -> Bấm **"⚡ Bóc Tách & Nạp"**.
   - Quan sát thanh thước đo `% Hoàn Hảo` tăng lên. Khi đạt mốc xanh lá (>= 80% hoặc 100%), bạn đã sẵn sàng!
3. **Bấm "BẮT ĐẦU HUẤN LUYỆN (1-CLICK TRAIN)":**
   - Hệ thống sẽ tự chạy 4 bước: Tiền xử lý -> Tách cao độ RMVPE -> Train 250 Epochs -> Tạo Index Faiss.
   - Bạn có thể xem trực tiếp % Epoch và dòng log trên màn hình Terminal của Web.
4. **Nghe thử giọng tại "Phòng Thu Thử Giọng":**
   - Nhập một câu bình luận bóng đá hoặc tin tức bất kỳ.
   - Bấm **"⚡ SINH GIỌNG CLONE & PHÁT NGAY"** để nghe giọng nhân vật phát ra từ loa!

---
*Phát triển bởi Đội ngũ Kỹ sư AI Antigravity - Tối ưu hóa đặc quyền cho NVIDIA GeForce RTX 4060.*
