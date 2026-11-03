// AutoVoiceStudio Frontend Logic

let currentBankId = "blv_mai_anh_tai";
let trainPollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  initUI();
  loadBanks();
  checkTrainStatus();
});

function initUI() {
  // Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).style.display = "block";
    });
  });

  // Slider text updates
  const inputIndex = document.getElementById("inputIndexRate");
  const indexVal = document.getElementById("indexRateVal");
  inputIndex.addEventListener("input", () => {
    indexVal.innerText = inputIndex.value;
  });

  const inputPitch = document.getElementById("inputPitch");
  const pitchVal = document.getElementById("pitchVal");
  inputPitch.addEventListener("input", () => {
    pitchVal.innerText = inputPitch.value;
  });

  // Bank change
  document.getElementById("selectBank").addEventListener("change", (e) => {
    currentBankId = e.target.value;
    loadBankDetails(currentBankId);
  });

  document.getElementById("btnRefreshBank").addEventListener("click", () => {
    loadBankDetails(currentBankId);
  });

  // Modals
  const modal = document.getElementById("modalNewBank");
  document.getElementById("btnNewBankModal").addEventListener("click", () => {
    modal.style.display = "flex";
  });
  document.getElementById("btnCloseModal").addEventListener("click", () => {
    modal.style.display = "none";
  });
  document.getElementById("btnConfirmNewBank").addEventListener("click", createNewBank);

  // Ingest Actions
  document.getElementById("btnIngestYoutube").addEventListener("click", handleYoutubeIngest);

  // Drag & drop upload
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileUploadInput");

  dropZone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // Training buttons
  document.getElementById("btnStartTrain").addEventListener("click", startTraining);
  document.getElementById("btnStopTrain").addEventListener("click", stopTraining);

  // TTS generate
  document.getElementById("btnGenerateTTS").addEventListener("click", generateTTS);
}

// --- BANK MANAGEMENT ---

async function loadBanks() {
  try {
    const res = await fetch("/api/banks");
    const data = await res.json();
    const select = document.getElementById("selectBank");
    select.innerHTML = "";

    if (!data.banks || data.banks.length === 0) {
      // Create default
      await fetch("/api/banks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ character_id: "blv_mai_anh_tai" })
      });
      return loadBanks();
    }

    data.banks.forEach(b => {
      const opt = document.createElement("option");
      opt.value = b.character_id;
      opt.innerText = `${b.character_id} (${b.completeness_percent}%)`;
      if (b.character_id === currentBankId) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });

    if (!currentBankId) {
      currentBankId = data.banks[0].character_id;
    }
    loadBankDetails(currentBankId);
  } catch (err) {
    console.error("Lỗi tải danh sách ngân hàng:", err);
  }
}

async function createNewBank() {
  const val = document.getElementById("newBankId").value.trim();
  if (!val) return alert("Vui lòng nhập mã ngân hàng giọng!");

  try {
    const res = await fetch("/api/banks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character_id: val })
    });
    if (!res.ok) {
      const err = await res.json();
      return alert(err.detail || "Không thể tạo ngân hàng!");
    }
    document.getElementById("modalNewBank").style.display = "none";
    document.getElementById("newBankId").value = "";
    currentBankId = val.toLowerCase().replace(/[^a-z0-9_]/g, "_");
    await loadBanks();
  } catch (err) {
    alert("Lỗi tạo ngân hàng: " + err);
  }
}

async function loadBankDetails(characterId) {
  try {
    const res = await fetch(`/api/banks/${characterId}`);
    if (!res.ok) return;
    const data = await res.json();
    renderBankData(data);
  } catch (err) {
    console.error("Lỗi lấy chi tiết:", err);
  }
}

function renderBankData(data) {
  // Meter updates
  const percent = data.completeness_percent || 0;
  document.getElementById("meterPercent").innerText = `${percent}%`;
  document.getElementById("meterDuration").innerText = `${data.total_formatted} / 8 phút chuẩn`;
  document.getElementById("meterFill").style.width = `${percent}%`;

  const badge = document.getElementById("qualityBadge");
  badge.className = `badge ${data.quality_badge}`;
  badge.innerText = `Độ Giống: ${percent}%`;

  document.getElementById("qualityText").innerText = data.quality_label;

  // Model status badge
  const mBadge = document.getElementById("modelStatusBadge");
  if (data.has_model) {
    mBadge.className = "badge-status ready";
    mBadge.innerText = "✓ Model RVC Đã Sẵn Sàng";
  } else {
    mBadge.className = "badge-status not-ready";
    mBadge.innerText = "⚠️ Chưa Train Model";
  }

  // Clips list
  const clipList = document.getElementById("clipList");
  const countEl = document.getElementById("clipCount");
  countEl.innerText = data.clips ? data.clips.length : 0;
  clipList.innerHTML = "";

  if (!data.clips || data.clips.length === 0) {
    clipList.innerHTML = `<div class="empty-state">Chưa có clip nào trong ngân hàng này. Hãy dán link YouTube bên dưới!</div>`;
    return;
  }

  data.clips.forEach(clip => {
    const item = document.createElement("div");
    item.className = "clip-item";
    item.innerHTML = `
      <div class="clip-info">
        <span class="clip-name">🎵 ${clip.name}</span>
        <span class="clip-meta">${clip.duration}s • ${clip.size_mb} MB</span>
      </div>
      <div class="clip-actions">
        <audio controls src="/audio/bank/${data.character_id}/${clip.name}" style="height: 30px;"></audio>
        <button class="btn-icon" title="Xóa clip" onclick="deleteClip('${data.character_id}', '${clip.name}')">🗑️</button>
      </div>
    `;
    clipList.appendChild(item);
  });
}

async function deleteClip(characterId, filename) {
  if (!confirm(`Bạn có chắc muốn xóa file ${filename}?`)) return;
  try {
    const res = await fetch(`/api/banks/${characterId}/clips/${filename}`, {
      method: "DELETE"
    });
    if (res.ok) {
      const data = await res.json();
      renderBankData(data);
    }
  } catch (err) {
    alert("Lỗi xóa file: " + err);
  }
}

// --- AUDIO INGESTION ---

async function handleYoutubeIngest() {
  const url = document.getElementById("inputYoutubeUrl").value.trim();
  if (!url) return alert("Vui lòng nhập link YouTube!");

  const loading = document.getElementById("ytLoading");
  const btn = document.getElementById("btnIngestYoutube");
  loading.style.display = "flex";
  btn.disabled = true;

  try {
    const res = await fetch(`/api/banks/${currentBankId}/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi xử lý");
    }
    const data = await res.json();
    document.getElementById("inputYoutubeUrl").value = "";
    renderBankData(data);
    alert(`Bóc tách Vocal thành công! Ngân hàng giọng đã đạt ${data.completeness_percent}% (${data.total_formatted}).`);
  } catch (err) {
    alert("Lỗi khi tải hoặc bóc tách: " + err.message);
  } finally {
    loading.style.display = "none";
    btn.disabled = false;
  }
}

async function handleFileUpload(file) {
  const loading = document.getElementById("uploadLoading");
  loading.style.display = "flex";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`/api/banks/${currentBankId}/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi xử lý file");
    }
    const data = await res.json();
    renderBankData(data);
    alert(`Đã lọc sạch âm thanh và cộng dồn vào ngân hàng giọng! Hiện tại: ${data.completeness_percent}%.`);
  } catch (err) {
    alert("Lỗi nạp file: " + err.message);
  } finally {
    loading.style.display = "none";
  }
}

// --- TRAINING ---

async function startTraining() {
  const epochs = parseInt(document.getElementById("inputEpochs").value) || 250;
  const batchSize = parseInt(document.getElementById("inputBatchSize").value) || 8;

  try {
    const res = await fetch("/api/train/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        character_id: currentBankId,
        epochs: epochs,
        batch_size: batchSize
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Không thể bắt đầu train");

    startTrainPolling();
  } catch (err) {
    alert("Lỗi: " + err.message);
  }
}

async function stopTraining() {
  if (!confirm("Bạn có chắc chắn muốn dừng tiến trình train không?")) return;
  try {
    await fetch("/api/train/stop", { method: "POST" });
  } catch (err) {
    console.error(err);
  }
}

function startTrainPolling() {
  if (trainPollInterval) clearInterval(trainPollInterval);

  document.getElementById("btnStartTrain").style.display = "none";
  document.getElementById("btnStopTrain").style.display = "block";
  document.getElementById("trainProgressBox").style.display = "block";

  trainPollInterval = setInterval(async () => {
    await checkTrainStatus();
  }, 2000);
}

async function checkTrainStatus() {
  try {
    const res = await fetch("/api/train/status");
    if (!res.ok) return;
    const s = await res.json();

    const isRunning = ["preprocessing", "extracting", "training", "indexing"].includes(s.status);
    const startBtn = document.getElementById("btnStartTrain");
    const stopBtn = document.getElementById("btnStopTrain");
    const progressBox = document.getElementById("trainProgressBox");

    if (isRunning) {
      startBtn.style.display = "none";
      stopBtn.style.display = "block";
      progressBox.style.display = "block";
      if (!trainPollInterval) {
        trainPollInterval = setInterval(checkTrainStatus, 2000);
      }
    } else {
      startBtn.style.display = "block";
      stopBtn.style.display = "none";
      if (s.status === "completed") {
        progressBox.style.display = "block";
      }
      if (trainPollInterval) {
        clearInterval(trainPollInterval);
        trainPollInterval = null;
      }
    }

    // Update UI elements
    document.getElementById("trainStepName").innerText = s.step_name || "Sẵn sàng";
    document.getElementById("trainFill").style.width = `${s.percent}%`;
    document.getElementById("trainPercentText").innerText = `${s.percent}%`;
    document.getElementById("terminalStatus").innerText = s.status.toUpperCase();

    // Render terminal logs
    if (s.logs && s.logs.length > 0) {
      const term = document.getElementById("terminalBody");
      term.innerHTML = s.logs.map(line => `<div class="term-line">${escapeHtml(line)}</div>`).join("");
      term.scrollTop = term.scrollHeight;
    }

    if (s.status === "completed") {
      loadBankDetails(currentBankId);
    }
  } catch (err) {
    console.error("Lỗi kiểm tra tiến trình train:", err);
  }
}

// --- VOICE TESTING / TTS ---

async function generateTTS() {
  const text = document.getElementById("ttsTextInput").value.trim();
  if (!text) return alert("Vui lòng nhập đoạn văn bản tiếng Việt!");

  const voice = document.getElementById("ttsVoiceSelect").value;
  const pitch = parseInt(document.getElementById("inputPitch").value) || 0;
  const indexRate = parseFloat(document.getElementById("inputIndexRate").value) || 0.95;

  const btn = document.getElementById("btnGenerateTTS");
  btn.disabled = true;
  btn.innerText = "⏳ Đang sinh giọng tiếng Việt & RVC Inference trên GPU...";

  try {
    const res = await fetch("/api/tts/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        character_id: currentBankId,
        voice: voice,
        pitch: pitch,
        index_rate: indexRate
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi chuyển đổi giọng");
    }
    const data = await res.json();
    const resultBox = document.getElementById("ttsResult");
    resultBox.style.display = "flex";

    const audioPlayer = document.getElementById("audioPlayer");
    audioPlayer.src = data.audio_url;
    audioPlayer.play();

    const dlBtn = document.getElementById("btnDownloadAudio");
    dlBtn.href = data.audio_url;
  } catch (err) {
    alert("Lỗi: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "⚡ SINH GIỌNG CLONE & PHÁT NGAY";
  }
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
