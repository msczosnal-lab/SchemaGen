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

// ── render ───────────────────────────────────────────────────────────────────

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);

  if (bgImage) ctx.drawImage(bgImage, 0, 0);

  bboxes.forEach((b, i) => {
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

    ctx.fillStyle = color;
    ctx.font = `${13 / scale}px Segoe UI, Arial, sans-serif`;
    const caption = b.tag || "(bez opisu)";
    ctx.fillText(caption, b.x + 2 / scale, b.y - 4 / scale);
  });

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
  } catch {
    bboxes = [];
  }

  redraw();
  renderAnnotationList();
  renderPageList();
  clearNewTagEditor();
  updatePageNav();
  const idx = currentPageIndex();
  const pos = idx >= 0 ? `${idx + 1}/${pageIds.length}` : "?";
  document.getElementById("hint").textContent =
    `Strona ${pos}: ${pageId} — opis → bbox → Zapisz | ←/→ strony | scroll zoom | Del usuwa`;
}

function summaryTag(tag, i) {
  const t = (tag || "").trim();
  const oneLine = t.replace(/\s+/g, " ");
  const preview = oneLine
    ? (oneLine.length > 56 ? `${oneLine.slice(0, 56)}…` : oneLine)
    : "(bez opisu)";
  return `#${i + 1} · ${preview}`;
}

function isTextField(el) {
  return el === tagInput || el?.classList?.contains("row-tag");
}

// ── annotation list ───────────────────────────────────────────────────────────

function renderAnnotationList() {
  const list = document.getElementById("annotation-list");
  const focusIdx = document.activeElement?.dataset?.idx;
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

    const header = document.createElement("button");
    header.type = "button";
    header.className = "accordion-header";
    header.innerHTML = `<span class="accordion-chevron">▶</span><span class="accordion-title"></span>`;
    header.querySelector(".accordion-title").textContent = summaryTag(b.tag, i);
    header.addEventListener("click", () => {
      if (expandedIdx === i) {
        expandedIdx = -1;
      } else {
        expandedIdx = i;
        selectedIdx = i;
      }
      renderAnnotationList();
      redraw();
      if (expandedIdx === i) {
        row.querySelector("textarea")?.focus();
      }
    });

    const body = document.createElement("div");
    body.className = "accordion-body";

    const textarea = document.createElement("textarea");
    textarea.className = "row-tag tag-textarea";
    textarea.dataset.idx = String(i);
    textarea.rows = 5;
    textarea.value = b.tag || "";
    textarea.placeholder = "Pelny opis elementu…";
    textarea.addEventListener("mousedown", (e) => e.stopPropagation());
    textarea.addEventListener("focus", () => {
      selectedIdx = i;
      expandedIdx = i;
      list.querySelectorAll(".annotation-accordion").forEach((el, j) => {
        el.classList.toggle("active", j === i);
        el.classList.toggle("expanded", j === i);
      });
      redraw();
    });
    textarea.addEventListener("input", (e) => {
      bboxes[i].tag = e.target.value;
      header.querySelector(".accordion-title").textContent = summaryTag(e.target.value, i);
      redraw();
    });

    body.appendChild(textarea);
    row.appendChild(header);
    row.appendChild(body);
    list.appendChild(row);

    if (focusIdx === String(i)) {
      textarea.focus();
      textarea.selectionStart = textarea.selectionEnd = textarea.value.length;
    }
  });
}

function selectBbox(idx, expand = true) {
  selectedIdx = idx;
  if (expand) expandedIdx = idx;
  renderAnnotationList();
  redraw();
  if (expand) {
    document.querySelector(`textarea.row-tag[data-idx="${idx}"]`)?.focus();
  }
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
    selectBbox(hit);
    return;
  }

  pendingTag = tagInput.value;
  drawing = true;
  selectedIdx = -1;
  document.querySelectorAll(".annotation-row").forEach((el) => el.classList.remove("active"));
  redraw();
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

  if (w < 4 || h < 4) { redraw(); return; } // too small — ignore

  const tag = tagInput.value.trim();
  const id = `${DEFAULT_CLASS}_${Date.now()}`;
  bboxes.push({
    id,
    class_name: DEFAULT_CLASS,
    x,
    y,
    width: w,
    height: h,
    tag,
  });
  selectedIdx = -1;
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
  if (e.target === tagInput || e.target.classList?.contains("row-tag")) return;
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
    bboxes.splice(selectedIdx, 1);
    selectedIdx = -1;
    redraw();
    renderAnnotationList();
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
