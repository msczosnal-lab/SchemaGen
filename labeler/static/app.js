// COWORK_TASK: sync/prompts/001-labeler-canvas.md
// Interaktywny canvas bbox — rysowanie, zoom, zaznaczanie, usuwanie, zapis

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const DEFAULT_CLASS = "element";
const PALETTE = [
  "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
  "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#e91e63",
];

let currentPageId = null;
let pageIds = [];
let pagesMeta = [];
let bboxes = [];
let selectedIdx = -1;
let expandedIdx = -1;
let pendingTag = "";
let nextSeq = 1;
let focusTextareaIdx = null;

// Zoom/pan state
let scale = 1;
let originX = 0;
let originY = 0;

// Drawing state
let drawing = false;
let drawMoved = false;
let clickSelectCandidate = -1;
let startX = 0;
let startY = 0;
const DRAG_THRESHOLD = 5;

// Loaded image
let bgImage = null;
let catalogLabels = [];

const tagInput = document.getElementById("tag-input");
const editorHint = document.getElementById("editor-hint");
const classHint = document.getElementById("class-hint");
const pagePrevBtn = document.getElementById("page-prev");
const pageNextBtn = document.getElementById("page-next");
const pagePositionEl = document.getElementById("page-position");

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

function colorFromTag(tag, fallbackIdx = 0) {
  if (!tag) return PALETTE[fallbackIdx % PALETTE.length];
  let h = 0;
  for (let i = 0; i < tag.length; i++) h = (h * 31 + tag.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

function bboxIdTime(id) {
  const m = String(id).match(/(\d{13,})/);
  return m ? Number(m[1]) : 0;
}

function sortBboxesNewestFirst() {
  bboxes.sort((a, b) => bboxIdTime(b.id) - bboxIdTime(a.id));
}

function ensureSeqNumbers() {
  const byAge = [...bboxes].sort((a, b) => bboxIdTime(a.id) - bboxIdTime(b.id));
  byAge.forEach((b, i) => {
    b.seq = b.seq || i + 1;
  });
  const maxSeq = bboxes.reduce((m, b) => Math.max(m, b.seq || 0), 0);
  nextSeq = maxSeq + 1;
}

function summaryLine(b) {
  const t = (b.tag || "").trim();
  const oneLine = t.replace(/\s+/g, " ");
  const preview = oneLine
    ? (oneLine.length > 52 ? `${oneLine.slice(0, 52)}…` : oneLine)
    : "(bez opisu)";
  return `#${b.seq || "?"} · ${preview}`;
}

function drawBboxNumber(b, color) {
  const num = String(b.seq || "?");
  const pad = 2 / scale;
  const maxW = Math.max(b.width - pad * 2, 1);
  const maxH = Math.max(b.height - pad * 2, 1);
  let fontSize = Math.min(14 / scale, maxH * 0.45, maxW * 0.85);
  const minSize = 5 / scale;
  fontSize = Math.max(minSize, fontSize);
  ctx.font = `bold ${fontSize}px Segoe UI, Arial, sans-serif`;
  let textW = ctx.measureText(num).width;
  while (fontSize > minSize && (textW + pad * 2 > maxW || fontSize > maxH * 0.55)) {
    fontSize *= 0.88;
    ctx.font = `bold ${fontSize}px Segoe UI, Arial, sans-serif`;
    textW = ctx.measureText(num).width;
  }
  const badgeW = Math.min(textW + pad * 2, b.width);
  const badgeH = Math.min(fontSize + pad * 1.2, b.height);
  ctx.fillStyle = color;
  ctx.fillRect(b.x, b.y, badgeW, badgeH);
  ctx.fillStyle = "#fff";
  ctx.fillText(num, b.x + pad, b.y + fontSize);
}

function drawBboxOnCanvas(b, i) {
  const color = colorFromTag(b.tag, i);
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

  drawBboxNumber(b, color);

  const caption = b.tag || "(bez opisu)";
  let capSize = Math.min(13 / scale, b.height * 0.35);
  capSize = Math.max(6 / scale, capSize);
  ctx.font = `${capSize}px Segoe UI, Arial, sans-serif`;
  ctx.fillStyle = color;
  ctx.fillText(caption, b.x + 2 / scale, Math.max(b.y - 4 / scale, capSize));
}

// ── render ───────────────────────────────────────────────────────────────────

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);

  if (bgImage) ctx.drawImage(bgImage, 0, 0);

  for (let i = bboxes.length - 1; i >= 0; i--) {
    drawBboxOnCanvas(bboxes[i], i);
  }

  ctx.restore();
}

// ── load data ─────────────────────────────────────────────────────────────────

async function loadPages() {
  const pages = await fetchJson("/api/pages");
  pagesMeta = [...pages].sort((a, b) =>
    (a.id || "").localeCompare(b.id || "", undefined, { numeric: true })
  );
  pageIds = pagesMeta.map((p) => p.id);
  renderPageList();
  updatePageNav();
}

function renderPageList() {
  const list = document.getElementById("page-list");
  list.innerHTML = "";
  pagesMeta.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p.filename || p.id;
    if (p.id === currentPageId) li.classList.add("active");
    li.onclick = () => selectPage(p.id);
    list.appendChild(li);
  });
}

function currentPageIndex() {
  return pageIds.indexOf(currentPageId);
}

function updatePageNav() {
  const idx = currentPageIndex();
  const total = pageIds.length;
  if (!pagePrevBtn || !pageNextBtn || !pagePositionEl) return;
  if (total === 0) {
    pagePositionEl.textContent = "— / —";
    pagePrevBtn.disabled = true;
    pageNextBtn.disabled = true;
    return;
  }
  if (idx < 0) {
    pagePositionEl.textContent = `— / ${total}`;
    pagePrevBtn.disabled = true;
    pageNextBtn.disabled = false;
    return;
  }
  pagePositionEl.textContent = `${idx + 1} / ${total}`;
  pagePrevBtn.disabled = idx <= 0;
  pageNextBtn.disabled = idx >= total - 1;
}

async function navigatePage(delta) {
  if (!pageIds.length) return;
  let idx = currentPageIndex();
  if (idx < 0) idx = delta > 0 ? -1 : 0;
  idx += delta;
  if (idx < 0 || idx >= pageIds.length) return;
  await selectPage(pageIds[idx]);
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

function syncNewTagEditor() {
  tagInput.value = pendingTag;
  editorHint.textContent = "Wpisz opis nastepnego elementu, potem narysuj bbox.";
}

function clearNewTagEditor() {
  pendingTag = "";
  tagInput.value = "";
  syncNewTagEditor();
}

function onNewTagInput(value) {
  pendingTag = value;
}

function normalizeBboxesForSave() {
  return bboxes.map((b) => ({
    id: b.id,
    class_name: b.class_name || DEFAULT_CLASS,
    x: b.x,
    y: b.y,
    width: b.width,
    height: b.height,
    tag: (b.tag || "").trim(),
    seq: b.seq || 0,
    semantic_group: b.semantic_group || "",
    color_ref: b.color_ref || "",
  }));
}

async function selectPage(pageId) {
  if (!pageId) return;
  currentPageId = pageId;
  scale = 1;
  originX = 0;
  originY = 0;
  selectedIdx = -1;
  expandedIdx = -1;
  pendingTag = "";

  bgImage = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      resolve(img);
    };
    img.onerror = () => reject(new Error(`Nie mozna zaladowac obrazu: ${pageId}`));
    img.src = `/api/pages/${pageId}/image?t=${Date.now()}`;
  });

  try {
    const ann = await fetchJson(`/api/annotations/${pageId}`);
    bboxes = ann.bboxes || [];
    sortBboxesNewestFirst();
    ensureSeqNumbers();
  } catch {
    bboxes = [];
    nextSeq = 1;
  }

  redraw();
  renderAnnotationList();
  renderPageList();
  clearNewTagEditor();
  updatePageNav();
  const idx = currentPageIndex();
  const pos = idx >= 0 ? `${idx + 1}/${pageIds.length}` : "?";
  document.getElementById("hint").textContent =
    `Strona ${pos}: ${pageId} — przeciagnij = nowy bbox | klik = zaznacz | ←/→ strony`;
}

function toggleAccordion(i, focusTextarea = false) {
  if (expandedIdx === i) {
    expandedIdx = -1;
    focusTextareaIdx = null;
  } else {
    expandedIdx = i;
    selectedIdx = i;
    if (focusTextarea) focusTextareaIdx = i;
  }
  renderAnnotationList();
  redraw();
}

function renderAnnotationList() {
  const list = document.getElementById("annotation-list");
  list.innerHTML = "";
  if (!bboxes.length) {
    const empty = document.createElement("li");
    empty.className = "muted";
    empty.textContent = "Brak elementow — wpisz opis i narysuj bbox.";
    empty.style.background = "transparent";
    empty.style.border = "none";
    empty.style.cursor = "default";
    list.appendChild(empty);
    return;
  }
  bboxes.forEach((b, i) => {
    const row = document.createElement("li");
    row.className = "annotation-accordion";
    if (i === selectedIdx) row.classList.add("active");
    if (i === expandedIdx) row.classList.add("expanded");

    const summary = document.createElement("div");
    summary.className = "accordion-summary";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "accordion-toggle";
    toggle.textContent = "▶";
    toggle.title = "Rozwin / zwin";
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleAccordion(i);
    });

    const line = document.createElement("button");
    line.type = "button";
    line.className = "summary-line";
    line.textContent = summaryLine(b);
    line.title = b.tag || "(bez opisu)";
    line.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleAccordion(i, expandedIdx !== i);
    });

    const del = document.createElement("button");
    del.type = "button";
    del.className = "delete-btn";
    del.textContent = "×";
    del.title = "Usun element";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      removeBboxAt(i);
    });

    summary.appendChild(toggle);
    summary.appendChild(line);
    summary.appendChild(del);

    const body = document.createElement("div");
    body.className = "accordion-body";
    const textarea = document.createElement("textarea");
    textarea.className = "row-tag tag-textarea";
    textarea.dataset.idx = String(i);
    textarea.rows = 4;
    textarea.value = b.tag || "";
    textarea.placeholder = "Pelny opis elementu…";
    bindRowTextarea(textarea, line, i);
    body.appendChild(textarea);

    row.appendChild(summary);
    row.appendChild(body);
    list.appendChild(row);

    if (focusTextareaIdx === i) {
      requestAnimationFrame(() => {
        textarea.focus();
        textarea.selectionStart = textarea.selectionEnd = textarea.value.length;
        focusTextareaIdx = null;
      });
    }
  });
}

function removeBboxAt(idx) {
  if (idx < 0 || idx >= bboxes.length) return;
  bboxes.splice(idx, 1);
  selectedIdx = -1;
  expandedIdx = -1;
  focusTextareaIdx = null;
  renderAnnotationList();
  redraw();
}

function bindRowTextarea(textarea, summaryBtn, i) {
  textarea.addEventListener("mousedown", (e) => e.stopPropagation());
  textarea.addEventListener("input", (e) => {
    bboxes[i].tag = e.target.value;
    summaryBtn.textContent = summaryLine(bboxes[i]);
    summaryBtn.title = e.target.value || "(bez opisu)";
    redraw();
  });
}

function selectBbox(idx, expand = false) {
  selectedIdx = idx;
  if (expand) {
    expandedIdx = idx;
    focusTextareaIdx = idx;
  }
  renderAnnotationList();
  redraw();
}

function isTextField(el) {
  return el === tagInput || el?.classList?.contains("row-tag");
}

// ── bbox drawing ──────────────────────────────────────────────────────────────

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);

  clickSelectCandidate = bboxes.findIndex(
    (b) => pt.x >= b.x && pt.x <= b.x + b.width && pt.y >= b.y && pt.y <= b.y + b.height
  );
  pendingTag = tagInput.value;
  drawing = true;
  drawMoved = false;
  startX = pt.x;
  startY = pt.y;
});

canvas.addEventListener("mousemove", (e) => {
  if (!drawing) return;
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);
  const w = Math.abs(pt.x - startX);
  const h = Math.abs(pt.y - startY);
  if (w >= DRAG_THRESHOLD || h >= DRAG_THRESHOLD) drawMoved = true;
  redraw();

  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  ctx.strokeStyle = colorFromTag(pendingTag || tagInput.value, bboxes.length);
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

  if (!drawMoved) {
    if (clickSelectCandidate >= 0) {
      selectBbox(clickSelectCandidate);
    } else {
      selectedIdx = -1;
      expandedIdx = -1;
      renderAnnotationList();
      redraw();
    }
    return;
  }

  if (w < DRAG_THRESHOLD || h < DRAG_THRESHOLD) {
    redraw();
    return;
  }

  const tag = tagInput.value.trim();
  const id = `${DEFAULT_CLASS}_${Date.now()}`;
  bboxes.unshift({
    id,
    class_name: DEFAULT_CLASS,
    x,
    y,
    width: w,
    height: h,
    tag,
    seq: nextSeq++,
  });
  selectedIdx = -1;
  expandedIdx = -1;
  redraw();
  renderAnnotationList();
  clearNewTagEditor();
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
  if (isTextField(e.target)) return;
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    navigatePage(-1);
    return;
  }
  if (e.key === "ArrowRight") {
    e.preventDefault();
    navigatePage(1);
    return;
  }
  if ((e.key === "Delete" || e.key === "Backspace") && selectedIdx >= 0) {
    removeBboxAt(selectedIdx);
  }
});

tagInput.addEventListener("input", (e) => onNewTagInput(e.target.value));

pagePrevBtn?.addEventListener("click", () => navigatePage(-1));
pageNextBtn?.addEventListener("click", () => navigatePage(1));

async function init() {
  await loadPages();
  if (pageIds.length && currentPageId == null) {
    await selectPage(pageIds[0]);
  } else {
    updatePageNav();
  }
  await loadElementCatalog();
  clearNewTagEditor();
}

document.getElementById("save-btn").addEventListener("click", async () => {
  if (!currentPageId) {
    alert("Wybierz strone z listy.");
    return;
  }
  const saveBtn = document.getElementById("save-btn");
  saveBtn.disabled = true;
  try {
    const payload = {
      record: {
        page_id: currentPageId,
        image_path: `${currentPageId}.png`,
        image_width: bgImage ? bgImage.naturalWidth : canvas.width,
        image_height: bgImage ? bgImage.naturalHeight : canvas.height,
        bboxes: normalizeBboxesForSave(),
        lines: [],
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
  } catch (err) {
    alert(`Blad zapisu: ${err.message}`);
    document.getElementById("hint").textContent = "Blad zapisu — sprawdz konsole.";
  } finally {
    saveBtn.disabled = false;
  }
});

document.getElementById("export-btn").addEventListener("click", async () => {
  if (!currentPageId) return alert("Wybierz strone");
  try {
    const paths = await fetchJson(`/api/export/${currentPageId}`, { method: "POST" });
    alert("Eksport:\n" + JSON.stringify(paths, null, 2));
  } catch (err) {
    alert(`Blad eksportu: ${err.message}`);
  }
});

init();
