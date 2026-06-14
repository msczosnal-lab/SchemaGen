// COWORK_TASK: sync/prompts/001-labeler-canvas.md
// Interaktywny canvas bbox — rysowanie, zoom, zaznaczanie, usuwanie, zapis

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let currentPageId = null;
let classes = [];
let bboxes = [];
let selectedIdx = -1;
let activeClassIdx = 0;

// Zoom/pan state
let scale = 1;
let originX = 0;
let originY = 0;

// Drawing state
let drawing = false;
let startX = 0;
let startY = 0;

// Loaded image
let bgImage = null;
let catalogLabels = [];

const tagInput = document.getElementById("tag-input");
const editorHint = document.getElementById("editor-hint");
const classHint = document.getElementById("class-hint");

// ── helpers ──────────────────────────────────────────────────────────────────

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function canvasToImage(cx, cy) {
  return { x: (cx - originX) / scale, y: (cy - originY) / scale };
}

function clientToCanvas(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    cx: (e.clientX - rect.left) * (canvas.width / rect.width),
    cy: (e.clientY - rect.top) * (canvas.height / rect.height),
  };
}

function colorForClass(name) {
  const palette = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#e91e63",
  ];
  const idx = classes.indexOf(name);
  return palette[idx % palette.length] || "#4a9eff";
}

// ── render ───────────────────────────────────────────────────────────────────

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);

  if (bgImage) ctx.drawImage(bgImage, 0, 0);

  bboxes.forEach((b, i) => {
    const color = colorForClass(b.class_name);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2 / scale;
    ctx.strokeRect(b.x, b.y, b.width, b.height);

    if (i === selectedIdx) {
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 3 / scale;
      ctx.setLineDash([6 / scale, 3 / scale]);
      ctx.strokeRect(b.x, b.y, b.width, b.height);
      ctx.setLineDash([]);
    }

    ctx.fillStyle = color;
    ctx.font = `${13 / scale}px Segoe UI, Arial, sans-serif`;
    const caption = b.tag ? b.tag : `${b.class_name} ${b.id}`;
    ctx.fillText(caption, b.x + 2 / scale, b.y - 4 / scale);
  });

  ctx.restore();
}

// ── load data ─────────────────────────────────────────────────────────────────

async function loadPages() {
  const pages = await fetchJson("/api/pages");
  const list = document.getElementById("page-list");
  list.innerHTML = "";
  pages.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p.filename || p.id;
    li.onclick = () => selectPage(p.id);
    list.appendChild(li);
  });
}

async function loadClasses() {
  const data = await fetchJson("/api/classes");
  classes = data.classes || [];
  const textIdx = classes.indexOf("text_label");
  if (textIdx >= 0) activeClassIdx = textIdx;
  renderClassList();
}

async function loadElementCatalog() {
  const data = await fetchJson("/api/element-catalog");
  catalogLabels = data.labels || [];
  const dl = document.getElementById("element-suggestions");
  dl.innerHTML = "";
  catalogLabels.forEach((label) => {
    const opt = document.createElement("option");
    opt.value = label;
    dl.appendChild(opt);
  });
}

function syncTagEditor() {
  const hasSelection = selectedIdx >= 0 && bboxes[selectedIdx];
  tagInput.disabled = !hasSelection;
  if (!hasSelection) {
    tagInput.value = "";
    editorHint.textContent = "Zaznacz bbox na canvasie.";
    classHint.textContent = "";
    return;
  }
  const b = bboxes[selectedIdx];
  tagInput.value = b.tag || "";
  editorHint.textContent = `Bbox #${selectedIdx + 1}`;
  classHint.textContent = `Klasa YOLO (skrot): ${b.class_name} — szczegoly wpisuj w opisie powyzej.`;
}

function updateSelectedTag(value) {
  if (selectedIdx < 0 || !bboxes[selectedIdx]) return;
  bboxes[selectedIdx].tag = value.trim();
  redraw();
  renderAnnotationList();
}

function renderClassList() {
  const list = document.getElementById("class-list");
  list.innerHTML = "";
  classes.forEach((name, idx) => {
    const li = document.createElement("li");
    li.textContent = `${idx + 1}. ${name}`;
    if (idx === activeClassIdx) li.classList.add("active");
    li.onclick = () => setActiveClass(idx);
    list.appendChild(li);
  });
}

function setActiveClass(idx) {
  activeClassIdx = idx;
  renderClassList();
  document.getElementById("hint").textContent =
    `Aktywna klasa: ${classes[idx] || "—"} (klawisze 1–9, rysuj bbox)`;
}

async function selectPage(pageId) {
  currentPageId = pageId;
  scale = 1;
  originX = 0;
  originY = 0;
  selectedIdx = -1;

  bgImage = await new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      resolve(img);
    };
    img.src = `/api/pages/${pageId}/image?t=${Date.now()}`;
  });

  try {
    const ann = await fetchJson(`/api/annotations/${pageId}`);
    bboxes = ann.bboxes || [];
  } catch {
    bboxes = [];
  }

  redraw();
  renderAnnotationList();
  syncTagEditor();
  document.getElementById("hint").textContent =
    `Strona: ${pageId} — rysuj bbox | scroll=zoom | Del=usuń | opis po zaznaczeniu`;
}

// ── annotation list ───────────────────────────────────────────────────────────

function renderAnnotationList() {
  const list = document.getElementById("annotation-list");
  list.innerHTML = "";
  bboxes.forEach((b, i) => {
    const li = document.createElement("li");
    li.textContent = b.tag ? b.tag : `${b.class_name} (${b.id})`;
    if (i === selectedIdx) li.classList.add("active");
    li.onclick = () => { selectedIdx = i; redraw(); renderAnnotationList(); syncTagEditor(); };
    list.appendChild(li);
  });
}

// ── bbox drawing ──────────────────────────────────────────────────────────────

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);

  // Check if clicking existing bbox (select)
  const hit = bboxes.findLastIndex(
    (b) => pt.x >= b.x && pt.x <= b.x + b.width && pt.y >= b.y && pt.y <= b.y + b.height
  );
  if (hit >= 0) {
    selectedIdx = hit;
    redraw();
    renderAnnotationList();
    syncTagEditor();
    return;
  }

  // Start drawing
  drawing = true;
  selectedIdx = -1;
  startX = pt.x;
  startY = pt.y;
});

canvas.addEventListener("mousemove", (e) => {
  if (!drawing) return;
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);
  redraw();

  // Preview rect
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  ctx.strokeStyle = colorForClass(classes[activeClassIdx] || "");
  ctx.lineWidth = 2 / scale;
  ctx.setLineDash([6 / scale, 3 / scale]);
  ctx.strokeRect(startX, startY, pt.x - startX, pt.y - startY);
  ctx.setLineDash([]);
  ctx.restore();
});

canvas.addEventListener("mouseup", (e) => {
  if (!drawing) return;
  drawing = false;
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);

  const x = Math.min(startX, pt.x);
  const y = Math.min(startY, pt.y);
  const w = Math.abs(pt.x - startX);
  const h = Math.abs(pt.y - startY);

  if (w < 4 || h < 4) { redraw(); return; } // too small — ignore

  const className = classes[activeClassIdx] || "unknown";
  const id = `${className}_${Date.now()}`;
  bboxes.push({ id, class_name: className, x, y, width: w, height: h, tag: "" });
  selectedIdx = bboxes.length - 1;
  redraw();
  renderAnnotationList();
  syncTagEditor();
  tagInput.focus();
});

// ── zoom ──────────────────────────────────────────────────────────────────────

canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  const { cx, cy } = clientToCanvas(e);
  const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
  originX = cx - factor * (cx - originX);
  originY = cy - factor * (cy - originY);
  scale *= factor;
  redraw();
}, { passive: false });

// ── keyboard ──────────────────────────────────────────────────────────────────

document.addEventListener("keydown", (e) => {
  const n = parseInt(e.key, 10);
  if (n >= 1 && n <= 9 && n <= classes.length) {
    setActiveClass(n - 1);
    return;
  }
  if ((e.key === "Delete" || e.key === "Backspace") && selectedIdx >= 0) {
    if (e.target === tagInput) return;
    bboxes.splice(selectedIdx, 1);
    selectedIdx = -1;
    redraw();
    renderAnnotationList();
    syncTagEditor();
  }
});

tagInput.addEventListener("input", (e) => updateSelectedTag(e.target.value));
tagInput.addEventListener("change", (e) => updateSelectedTag(e.target.value));

// ── save / export ─────────────────────────────────────────────────────────────

document.getElementById("save-btn").onclick = async () => {
  if (!currentPageId) return alert("Wybierz stronę");
  const payload = {
    record: {
      page_id: currentPageId,
      image_path: `${currentPageId}.png`,
      image_width: bgImage ? bgImage.naturalWidth : canvas.width,
      image_height: bgImage ? bgImage.naturalHeight : canvas.height,
      bboxes,
      texts: [],
      connections: [],
    },
  };
  await fetchJson("/api/annotations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadElementCatalog();
  document.getElementById("hint").textContent = "Zapisano ✓ (katalog uaktualniony)";
};

document.getElementById("export-btn").onclick = async () => {
  if (!currentPageId) return alert("Wybierz stronę");
  const paths = await fetchJson(`/api/export/${currentPageId}`, { method: "POST" });
  alert("Eksport:\n" + JSON.stringify(paths, null, 2));
};

// ── init ──────────────────────────────────────────────────────────────────────

loadPages();
loadClasses();
loadElementCatalog();
syncTagEditor();
