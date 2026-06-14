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
const saveBtn = document.getElementById("save-btn");
const saveAllBtn = document.getElementById("save-all-btn");
const saveStatusEl = document.getElementById("save-status");

const DRAFT_PREFIX = "schemagen:draft:";
const pageCache = new Map();
const dirtyPages = new Set();

function draftKey(pageId) {
  return `${DRAFT_PREFIX}${pageId}`;
}

function capturePageState() {
  return {
    bboxes: JSON.parse(JSON.stringify(bboxes)),
    nextSeq,
    image_width: bgImage ? bgImage.naturalWidth : canvas.width,
    image_height: bgImage ? bgImage.naturalHeight : canvas.height,
    updatedAt: Date.now(),
  };
}

function persistPageDraft(pageId = currentPageId) {
  if (!pageId) return;
  const state = pageId === currentPageId ? capturePageState() : pageCache.get(pageId);
  if (!state) return;
  pageCache.set(pageId, state);
  try {
    localStorage.setItem(draftKey(pageId), JSON.stringify(state));
  } catch (err) {
    console.warn("localStorage:", err);
  }
}

function loadLocalDraft(pageId) {
  try {
    const raw = localStorage.getItem(draftKey(pageId));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function applyPageState(state) {
  bboxes = state?.bboxes ? JSON.parse(JSON.stringify(state.bboxes)) : [];
  sortBboxesNewestFirst();
  ensureSeqNumbers();
  if (state?.nextSeq && state.nextSeq > nextSeq) {
    nextSeq = state.nextSeq;
  }
}

function markPageDirty(pageId = currentPageId) {
  if (!pageId) return;
  dirtyPages.add(pageId);
  if (pageId === currentPageId) persistPageDraft(pageId);
  updateSaveStatus();
}

function updateSaveStatus() {
  if (!saveBtn || !saveStatusEl) return;
  const n = bboxes.length;
  const dirty = currentPageId && dirtyPages.has(currentPageId);
  saveBtn.textContent = dirty ? `Zapisz strone (${n})*` : `Zapisz strone (${n})`;
  saveBtn.classList.toggle("dirty", !!dirty);
  const cached = pageCache.size;
  const dirtyCount = dirtyPages.size;
  if (dirtyCount > 0) {
    saveStatusEl.textContent = `Niezapisane: ${dirtyCount} str. — zmiana strony tez zapisuje lokalnie.`;
  } else if (cached > 0) {
    saveStatusEl.textContent = "Wszystko zapisane w bazie.";
  } else {
    saveStatusEl.textContent = "";
  }
}

function buildSavePayload(pageId, state) {
  return {
    record: {
      page_id: pageId,
      image_path: `${pageId}.png`,
      image_width: state.image_width || 0,
      image_height: state.image_height || 0,
      bboxes: state.bboxes.map((b) => ({
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
      })),
      lines: [],
      texts: [],
      connections: [],
    },
  };
}

async function savePageToServer(pageId, { silent = false } = {}) {
  if (!pageId) return false;
  if (pageId === currentPageId) persistPageDraft(pageId);
  const state = pageCache.get(pageId) || (pageId === currentPageId ? capturePageState() : null);
  if (!state) return false;
  try {
    const res = await fetchJson("/api/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildSavePayload(pageId, state)),
    });
    dirtyPages.delete(pageId);
    updateSaveStatus();
    if (!silent) {
      saveStatusEl.textContent = `Zapisano ${pageId}: ${res.bbox_count ?? state.bboxes.length} bbox`;
      document.getElementById("hint").textContent = `Zapisano ✓ ${pageId}`;
    }
    return true;
  } catch (err) {
    if (!silent) {
      alert(`Blad zapisu (${pageId}): ${err.message}`);
      saveStatusEl.textContent = `Blad zapisu ${pageId} — dane sa w localStorage`;
    }
    return false;
  }
}

async function flushCurrentPage() {
  if (!currentPageId) return;
  persistPageDraft(currentPageId);
  if (dirtyPages.has(currentPageId)) {
    await savePageToServer(currentPageId, { silent: true });
  }
}

async function saveAllPages() {
  if (currentPageId) persistPageDraft(currentPageId);
  const ids = new Set([...pageCache.keys(), ...(currentPageId ? [currentPageId] : [])]);
  let ok = 0;
  let fail = 0;
  for (const pageId of ids) {
    if (await savePageToServer(pageId, { silent: true })) ok += 1;
    else fail += 1;
  }
  await loadElementCatalog();
  saveStatusEl.textContent = fail
    ? `Zapisano ${ok} str., bledy: ${fail} (szkice w localStorage)`
    : `Zapisano wszystkie strony (${ok})`;
  updateSaveStatus();
}

function scanLocalDrafts() {
  const drafts = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!key?.startsWith(DRAFT_PREFIX)) continue;
    try {
      const data = JSON.parse(localStorage.getItem(key));
      drafts.push({
        pageId: key.slice(DRAFT_PREFIX.length),
        count: data.bboxes?.length || 0,
        updatedAt: data.updatedAt || 0,
      });
    } catch {
      /* skip */
    }
  }
  return drafts;
}

function reportRecoveryHints() {
  const drafts = scanLocalDrafts();
  const total = drafts.reduce((s, d) => s + d.count, 0);
  if (total === 0) return;
  saveStatusEl.textContent =
    `Lokalne szkice: ${drafts.length} str., ${total} bbox (localStorage). Otworz strone aby wczytac.`;
}

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

function listLabel(b) {
  return `#${b.seq || "?"}`;
}

// ── hierarchia bboxow (lustro backend/geometry/bbox_layout.py) ─────────────────

const HIER_EPS = 1.0;

function bboxArea(b) {
  return Math.max(b.width, 0) * Math.max(b.height, 0);
}

function bboxContains(outer, inner) {
  if (outer.id === inner.id) return false;
  if (bboxArea(inner) >= bboxArea(outer)) return false;
  return (
    inner.x >= outer.x - HIER_EPS &&
    inner.y >= outer.y - HIER_EPS &&
    inner.x + inner.width <= outer.x + outer.width + HIER_EPS &&
    inner.y + inner.height <= outer.y + outer.height + HIER_EPS
  );
}

function findParentId(b) {
  let best = null;
  for (const o of bboxes) {
    if (o.id === b.id) continue;
    if (bboxContains(o, b)) {
      if (
        best === null ||
        bboxArea(o) < bboxArea(best) ||
        (bboxArea(o) === bboxArea(best) && o.id < best.id)
      ) {
        best = o;
      }
    }
  }
  return best ? best.id : "";
}

function recomputeHierarchy() {
  const byId = new Map(bboxes.map((b) => [b.id, b]));
  const parentMap = new Map();
  for (const b of bboxes) parentMap.set(b.id, findParentId(b));
  for (const b of bboxes) {
    const pid = parentMap.get(b.id) || "";
    b.parent_id = pid;
    let depth = 0;
    const seen = new Set();
    let cur = parentMap.get(b.id) || "";
    while (cur) {
      if (seen.has(cur)) break;
      seen.add(cur);
      depth += 1;
      cur = parentMap.get(cur) || "";
    }
    b.depth = depth;
    const parent = pid ? byId.get(pid) : null;
    if (parent && parent.width > 0 && parent.height > 0) {
      b.rel_bbox = [
        (b.x - parent.x) / parent.width,
        (b.y - parent.y) / parent.height,
        b.width / parent.width,
        b.height / parent.height,
      ];
    } else {
      b.rel_bbox = [];
    }
  }
}

function parentSeqOf(b) {
  if (!b.parent_id) return null;
  const p = bboxes.find((x) => x.id === b.parent_id);
  return p ? p.seq || "?" : null;
}

function treeOrderedIndices() {
  const childrenOf = new Map();
  bboxes.forEach((b, i) => {
    const key = b.parent_id || "";
    if (!childrenOf.has(key)) childrenOf.set(key, []);
    childrenOf.get(key).push(i);
  });
  for (const arr of childrenOf.values()) {
    arr.sort((a, b) => (bboxes[a].seq || 0) - (bboxes[b].seq || 0));
  }
  const order = [];
  const visit = (key) => {
    for (const i of childrenOf.get(key) || []) {
      order.push(i);
      visit(bboxes[i].id);
    }
  };
  visit("");
  bboxes.forEach((b, i) => {
    if (!order.includes(i)) order.push(i);
  });
  return order;
}

function drawBboxNumber(b, color) {
  const num = String(b.seq || "?");
  const pad = 5 / scale;
  const maxW = Math.max(b.width - pad * 2, 16 / scale);
  const maxH = Math.max(b.height - pad * 2, 16 / scale);
  const minSize = 26 / scale;
  let fontSize = Math.min(48 / scale, maxH * 0.72, maxW * 0.98);
  fontSize = Math.max(minSize, fontSize);
  ctx.font = `bold ${fontSize}px Segoe UI, Arial, sans-serif`;
  let textW = ctx.measureText(num).width;
  while (fontSize > minSize && (textW + pad * 2 > maxW || fontSize > maxH * 0.78)) {
    fontSize *= 0.88;
    ctx.font = `bold ${fontSize}px Segoe UI, Arial, sans-serif`;
    textW = ctx.measureText(num).width;
  }
  const badgeW = Math.min(textW + pad * 2, b.width);
  const badgeH = Math.min(fontSize + pad * 1.5, b.height);
  const tx = b.x + pad;
  const ty = b.y + fontSize + pad * 0.35;
  ctx.fillStyle = color;
  ctx.fillRect(b.x, b.y, badgeW, badgeH);
  ctx.strokeStyle = "rgba(0,0,0,0.45)";
  ctx.lineWidth = 1.5 / scale;
  ctx.strokeRect(b.x, b.y, badgeW, badgeH);
  ctx.fillStyle = "#fff";
  ctx.fillText(num, tx, ty);
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
  return capturePageState().bboxes.map((b) => ({
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
  if (currentPageId && currentPageId !== pageId) {
    persistPageDraft(currentPageId);
    if (dirtyPages.has(currentPageId)) {
      const ok = await savePageToServer(currentPageId, { silent: true });
      if (!ok) {
        saveStatusEl.textContent =
          `Auto-zapis ${currentPageId} nieudany — szkic w localStorage, kliknij Zapisz wszystkie`;
      }
    }
  }

  currentPageId = pageId;
  scale = 1;
  originX = 0;
  originY = 0;
  selectedIdx = -1;
  expandedIdx = -1;
  focusTextareaIdx = null;
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

  let serverBboxes = [];
  try {
    const ann = await fetchJson(`/api/annotations/${pageId}`);
    serverBboxes = ann.bboxes || [];
  } catch {
    serverBboxes = [];
  }

  const cached = pageCache.get(pageId) || loadLocalDraft(pageId);
  if (cached?.bboxes?.length >= serverBboxes.length) {
    applyPageState(cached);
    if (cached.bboxes.length > serverBboxes.length) {
      dirtyPages.add(pageId);
    }
  } else {
    bboxes = serverBboxes;
    sortBboxesNewestFirst();
    ensureSeqNumbers();
    persistPageDraft(pageId);
  }

  redraw();
  renderAnnotationList();
  renderPageList();
  clearNewTagEditor();
  updatePageNav();
  updateSaveStatus();
  const idx = currentPageIndex();
  const pos = idx >= 0 ? `${idx + 1}/${pageIds.length}` : "?";
  document.getElementById("hint").textContent =
    `Strona ${pos}: ${pageId} — zmiana strony auto-zapisuje | Ctrl+S = zapisz`;
}

function toggleAccordion(i) {
  if (expandedIdx === i) {
    expandedIdx = -1;
    focusTextareaIdx = null;
  } else {
    expandedIdx = i;
    selectedIdx = i;
    focusTextareaIdx = i;
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
    const isExpanded = i === expandedIdx;
    const row = document.createElement("li");
    row.className = "annotation-accordion";
    if (i === selectedIdx) row.classList.add("active");
    if (isExpanded) row.classList.add("expanded");

    const summary = document.createElement("div");
    summary.className = "accordion-summary";

    const line = document.createElement("button");
    line.type = "button";
    line.className = "summary-line";
    line.textContent = listLabel(b);
    line.title = isExpanded ? "Zwin" : (b.tag || "Kliknij aby edytowac opis");
    line.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleAccordion(i);
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

    summary.appendChild(line);
    summary.appendChild(del);
    row.appendChild(summary);

    if (isExpanded) {
      const body = document.createElement("div");
      body.className = "accordion-body";
      const textarea = document.createElement("textarea");
      textarea.className = "row-tag tag-textarea";
      textarea.dataset.idx = String(i);
      textarea.rows = 5;
      textarea.value = b.tag || "";
      textarea.placeholder = "Opis elementu…";
      bindRowTextarea(textarea, i);
      body.appendChild(textarea);
      row.appendChild(body);

      if (focusTextareaIdx === i) {
        requestAnimationFrame(() => {
          textarea.focus();
          textarea.selectionStart = textarea.selectionEnd = textarea.value.length;
          focusTextareaIdx = null;
        });
      }
    }

    list.appendChild(row);
  });
}

function removeBboxAt(idx) {
  if (idx < 0 || idx >= bboxes.length) return;
  bboxes.splice(idx, 1);
  selectedIdx = -1;
  expandedIdx = -1;
  focusTextareaIdx = null;
  markPageDirty();
  renderAnnotationList();
  redraw();
}

function bindRowTextarea(textarea, i) {
  textarea.addEventListener("mousedown", (e) => e.stopPropagation());
  textarea.addEventListener("input", (e) => {
    bboxes[i].tag = e.target.value;
    markPageDirty();
    redraw();
  });
}

function selectBbox(idx) {
  selectedIdx = idx;
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
  focusTextareaIdx = null;
  markPageDirty();
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
  if (isTextField(e.target)) {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      savePageToServer(currentPageId);
    }
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    savePageToServer(currentPageId);
    return;
  }
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
  reportRecoveryHints();
  if (pageIds.length && currentPageId == null) {
    await selectPage(pageIds[0]);
  } else {
    updatePageNav();
  }
  await loadElementCatalog();
  clearNewTagEditor();
  updateSaveStatus();
}

window.addEventListener("beforeunload", (e) => {
  if (currentPageId) persistPageDraft(currentPageId);
  if (dirtyPages.size > 0) {
    e.preventDefault();
    e.returnValue = "";
  }
});

saveBtn?.addEventListener("click", async () => {
  if (!currentPageId) {
    alert("Wybierz strone z listy.");
    return;
  }
  saveBtn.disabled = true;
  persistPageDraft(currentPageId);
  try {
    const ok = await savePageToServer(currentPageId);
    if (ok) await loadElementCatalog();
  } finally {
    saveBtn.disabled = false;
  }
});

saveAllBtn?.addEventListener("click", async () => {
  saveAllBtn.disabled = true;
  try {
    await saveAllPages();
  } finally {
    saveAllBtn.disabled = false;
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
