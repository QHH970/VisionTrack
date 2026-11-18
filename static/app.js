/* =========================================================
   瞰途 VisionTrack · 前端交互
   保留原有检测流程与全部 API 调用，仅做体验增强
   ========================================================= */

const state = {
  lastSummary: { total: 0, counts: {}, detections: [] },
  selectedImage: null,
  selectedVideo: null,
  cameraStream: null,
  cameraTimer: null,
  busyFrame: false,
};

const $ = (id) => document.getElementById(id);

/* ---------- 通用工具 ---------- */

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function closeMobileNav() {
  $("sidebar").classList.remove("open");
  $("mobileOverlay").classList.remove("show");
}

function activateTab(mode) {
  document.querySelectorAll(".tab").forEach((item) => {
    item.classList.toggle("active", item.dataset.tab === mode);
  });
  document.querySelectorAll(".panel").forEach((item) => item.classList.remove("active"));
  const panel = $(`${mode}Panel`);
  if (panel) panel.classList.add("active");
  closeMobileNav();
}

async function withBusy(button, viewer, task) {
  if (button) button.classList.add("loading");
  if (viewer) viewer.classList.add("is-loading");
  try {
    return await task();
  } finally {
    if (button) button.classList.remove("loading");
    if (viewer) viewer.classList.remove("is-loading");
  }
}

function setFileName(id, name) {
  const el = $(id);
  el.textContent = name || "未选择文件";
  el.classList.toggle("has-file", Boolean(name));
}

function updateClock() {
  $("clock").textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });
}

/* ---------- 导航与模式切换 ---------- */

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.tab));
});

$("menuBtn").addEventListener("click", () => {
  const opened = $("sidebar").classList.toggle("open");
  $("mobileOverlay").classList.toggle("show", opened);
});

$("mobileOverlay").addEventListener("click", closeMobileNav);

updateClock();
window.setInterval(updateClock, 1000);

/* ---------- 图片检测 ---------- */

$("imageInput").addEventListener("change", (event) => {
  state.selectedImage = event.target.files[0] || null;
  if (state.selectedImage) {
    $("imageResult").src = URL.createObjectURL(state.selectedImage);
    $("imagePlaceholder").classList.add("hidden");
    setFileName("imageFileName", state.selectedImage.name);
  } else {
    setFileName("imageFileName", "");
  }
});

$("imageDetectBtn").addEventListener("click", async () => {
  if (!state.selectedImage) {
    setAdvice("请先选择图片。");
    return;
  }
  const body = new FormData();
  body.append("image", state.selectedImage);
  const data = await withBusy($("imageDetectBtn"), $("imageViewer"), () =>
    postForm("/api/detect-image", body),
  );
  if (!data) return;
  $("imageResult").src = data.image;
  $("imagePlaceholder").classList.add("hidden");
  updateSummary(data);
});

/* ---------- 视频检测 ---------- */

$("videoInput").addEventListener("change", (event) => {
  state.selectedVideo = event.target.files[0] || null;
  if (state.selectedVideo) {
    $("videoPlaceholderTitle").textContent = state.selectedVideo.name;
    $("videoPlaceholder").classList.remove("hidden");
    setFileName("videoFileName", state.selectedVideo.name);
  } else {
    $("videoPlaceholderTitle").textContent = "上传视频文件开始检测";
    setFileName("videoFileName", "");
  }
});

$("videoDetectBtn").addEventListener("click", async () => {
  if (!state.selectedVideo) {
    setAdvice("请先选择视频。");
    return;
  }
  const body = new FormData();
  body.append("video", state.selectedVideo);
  const data = await withBusy($("videoDetectBtn"), $("videoViewer"), () =>
    postForm("/api/upload-video", body),
  );
  if (!data) return;
  $("videoResult").src = `${data.stream_url}?t=${Date.now()}`;
  $("videoPlaceholder").classList.add("hidden");
  pollSummary();
});

/* ---------- 摄像头实时检测 ---------- */

$("startCameraBtn").addEventListener("click", async () => {
  try {
    state.cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    $("cameraVideo").srcObject = state.cameraStream;
    $("camVideoEmpty").classList.add("hidden");
    $("cameraPlaceholder").classList.add("hidden");
    $("startCameraBtn").disabled = true;
    $("stopCameraBtn").disabled = false;
    $("cameraHint").textContent = "实时检测中 · 每 0.7 秒分析一帧";
    $("cameraHint").classList.add("live");
    state.cameraTimer = window.setInterval(sendCameraFrame, 700);
  } catch (error) {
    setAdvice(`摄像头打开失败：${error.message}`);
  }
});

$("stopCameraBtn").addEventListener("click", stopCamera);
$("adviceBtn").addEventListener("click", requestAdvice);

async function sendCameraFrame() {
  if (state.busyFrame || !$("cameraVideo").videoWidth) return;
  state.busyFrame = true;
  const video = $("cameraVideo");
  const canvas = $("cameraCanvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  const image = canvas.toDataURL("image/jpeg", 0.82);

  try {
    const response = await fetch("/api/detect-frame", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "实时检测失败");
    $("cameraResult").src = data.image;
    updateSummary(data);
  } catch (error) {
    setAdvice(error.message);
  } finally {
    state.busyFrame = false;
  }
}

function stopCamera() {
  if (state.cameraTimer) window.clearInterval(state.cameraTimer);
  state.cameraTimer = null;
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach((track) => track.stop());
  }
  state.cameraStream = null;
  $("cameraVideo").srcObject = null;
  $("cameraResult").removeAttribute("src");
  $("camVideoEmpty").classList.remove("hidden");
  $("cameraPlaceholder").classList.remove("hidden");
  $("cameraHint").textContent = "摄像头待连接";
  $("cameraHint").classList.remove("live");
  $("startCameraBtn").disabled = false;
  $("stopCameraBtn").disabled = true;
}

/* ---------- 请求封装 ---------- */

async function postForm(url, body) {
  try {
    const response = await fetch(url, { method: "POST", body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "请求失败");
    return data;
  } catch (error) {
    setAdvice(error.message);
    return null;
  }
}

async function requestAdvice() {
  setAdvice("正在生成建议...");
  try {
    const response = await fetch("/api/ai-advice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.lastSummary),
    });
    const data = await response.json();
    setAdvice(data.text || "暂无建议。");
  } catch (error) {
    setAdvice(error.message);
  }
}

async function pollSummary() {
  for (let i = 0; i < 120; i += 1) {
    try {
      const response = await fetch("/api/summary");
      const data = await response.json();
      updateSummary(data);
    } catch (error) {
      setAdvice(error.message);
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}

/* ---------- 结果渲染 ---------- */

function updateSummary(data) {
  state.lastSummary = {
    total: data.total || 0,
    counts: data.counts || {},
    detections: data.detections || [],
  };
  $("latency").textContent = `${data.elapsed_ms || "--"} ms`;
  $("totalCount").textContent = state.lastSummary.total;
  $("classCount").textContent = Object.keys(state.lastSummary.counts).length;

  const counts = Object.entries(state.lastSummary.counts);
  const maxCount = Math.max(1, ...counts.map(([, count]) => Number(count) || 0));
  $("countsList").classList.toggle("empty", counts.length === 0);
  $("countsList").innerHTML = counts.length
    ? counts
        .map(
          ([name, count]) => `
            <div class="countItem">
              <span class="count-bar" style="width:${Math.round((Number(count) / maxCount) * 100)}%"></span>
              <span class="count-name">${escapeHtml(name)}</span>
              <span class="badge">${count}</span>
            </div>`,
        )
        .join("")
    : "暂无检测结果";

  const detections = state.lastSummary.detections.slice(0, 30);
  $("detectionCount").textContent = `${state.lastSummary.detections.length} 项目标`;
  $("detectionsList").classList.toggle("empty", detections.length === 0);
  $("detectionsList").innerHTML = detections.length
    ? detections
        .map(
          (item, index) => `
            <div class="detectionItem">
              <span class="det-index">${String(index + 1).padStart(2, "0")}</span>
              <span class="det-label">${escapeHtml(item.label)}</span>
              <span class="confidence">${Math.round(item.confidence * 100)}%</span>
            </div>`,
        )
        .join("")
    : "暂无目标";
}

function setAdvice(text) {
  $("adviceText").textContent = text;
}
