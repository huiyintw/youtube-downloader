const form = document.getElementById("download-form");
const urlInput = document.getElementById("url");
const browserSelect = document.getElementById("browser");
const submitBtn = document.getElementById("submit-btn");
const btnText = submitBtn.querySelector(".btn-text");
const btnLoading = submitBtn.querySelector(".btn-loading");
const audioFormatSelector = document.getElementById("audio-format-selector");

const previewSection = document.getElementById("preview");
const resultSection = document.getElementById("result");
const errorSection = document.getElementById("error");

let debounceTimer;

function hideAll() {
  previewSection.classList.add("hidden");
  resultSection.classList.add("hidden");
  errorSection.classList.add("hidden");
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  btnText.classList.toggle("hidden", loading);
  btnLoading.classList.toggle("hidden", !loading);
}

function formatDuration(seconds) {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function showError(message) {
  hideAll();
  document.getElementById("error-message").textContent = message;
  errorSection.classList.remove("hidden");
}

function getBrowser() {
  return browserSelect.value;
}

function getAudioFormat() {
  const checked = form.querySelector('input[name="audio_format"]:checked');
  return checked ? checked.value : "m4a";
}

function updateAudioFormatVisibility() {
  const mode = form.querySelector('input[name="mode"]:checked')?.value;
  audioFormatSelector.classList.toggle("hidden", mode !== "audio");
}

form.querySelectorAll('input[name="mode"]').forEach((radio) => {
  radio.addEventListener("change", updateAudioFormatVisibility);
});

async function fetchInfo(url) {
  const res = await fetch("/api/info", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, browser: getBrowser() }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "無法取得影片資訊");
  return data.data;
}

function showPreview(info) {
  hideAll();
  document.getElementById("thumbnail").src = info.thumbnail || "";
  document.getElementById("video-title").textContent = info.title;
  document.getElementById("video-uploader").textContent = info.uploader || "";
  document.getElementById("video-duration").textContent = formatDuration(info.duration);
  previewSection.classList.remove("hidden");
}

urlInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const url = urlInput.value.trim();
  if (!url || !url.includes("youtube")) return;

  debounceTimer = setTimeout(async () => {
    try {
      const info = await fetchInfo(url);
      showPreview(info);
    } catch {
      hideAll();
    }
  }, 600);
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideAll();

  const url = urlInput.value.trim();
  const mode = form.querySelector('input[name="mode"]:checked').value;
  const browser = getBrowser();
  const audio_format = getAudioFormat();

  if (!url) {
    showError("請輸入 YouTube 網址");
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, mode, browser, audio_format }),
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "下載失敗");
    }

    const { filename } = data.data;
    document.getElementById("result-filename").textContent = filename;
    const link = document.getElementById("download-link");
    link.href = `/api/files/${encodeURIComponent(filename)}`;
    link.download = filename;
    resultSection.classList.remove("hidden");
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});
