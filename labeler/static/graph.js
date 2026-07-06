/** GT v2 labeler — bbox + terminale (krok 5, prompt 022). */

const BBOX_COLOR = "#f76707";
const BBOX_SEL = "#ffd43b";
const TERMINAL_COLOR = "#ffd43b";
const TERMINAL_SEL = "#fa5252";
const TERMINAL_R = 10;
const DRAG_THRESHOLD = 4;

const RECENT_PAGES_KEY = "graphRecentPages";
const RECENT_PAGES_MAX = 3;

let pageIds = [];
let pagesMeta = [];
let currentPageId = null;
let bgImage = null;
let scale = 1;
let originX = 0;
let originY = 0;

/** @type {{ version: number, page_id: string, image_width: number, image_height: number, symbols: object[], lines: object[] }} */
let graph = { version: 2, page_id: "", image_width: 800, image_height: 600, symbols: [], lines: [] };

let selectedSymIdx = -1;
let selectedTermIdx = -1;
let dirty = false;

let drawing = false;
let drawMoved = false;
let startX = 0;
let startY = 0;
let clickSelectCandidate = -1;
let draggingTerminal = null;
let terminalDragMoved = false;

let symSeq = 0;
let paletteTimer = null;

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const saveStatusEl = document.getElementById("save-status");
const pagePrevBtn = document.getElementById("page-prev");
const pageNextBtn = document.getElementById("page-next");
const pagePositionEl = document.getElementById("page-position");
const symTypeInput = document.getElementById("sym-type-input");
const symTagInput = document.getElementById("sym-tag-input");
const paletteResults = document.getElementById("palette-results");
const symbolEditor = document.getElementById("symbol-editor");

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let msg = await res.text();
    try {
      const j = JSON.parse(msg);
      if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* keep text */
    }
    throw new Error(msg);
  }
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

function imgPointFromEvent(e) {
  const { cx, cy } = clientToCanvas(e);
  return canvasToImage(cx, cy);
}

function bboxRect(sym) {
  const [x1, y1, x2, y2] = sym.bbox;
  const x = Math.min(x1, x2);
  const y = Math.min(y1, y2);
  return { x, y, width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) };
}

function rectToBbox(x, y, w, h) {
  return [Math.round(x), Math.round(y), Math.round(x + w), Math.round(y + h)];
}

function nextSymId() {
  const used = new Set(graph.symbols.map((s) => s.id));
  let n = symSeq;
  while (used.has(`sym_${n}`)) n += 1;
  symSeq = n + 1;
  return `sym_${n}`;
}

function nextTerminalId(sym) {
  const used = new Set((sym.terminals || []).map((t) => String(t.id)));
  let n = 1;
  while (used.has(String(n))) n += 1;
  return String(n);
}

function snapTerminalRel(b, imgPt) {
  const rx = Math.max(0, Math.min(1, (imgPt.x - b.x) / (b.width || 1)));
  const ry = Math.max(0, Math.min(1, (imgPt.y - b.y) / (b.height || 1)));
  const dLeft = rx;
  const dRight = 1 - rx;
  const dTop = ry;
  const dBottom = 1 - ry;
  const m = Math.min(dLeft, dRight, dTop, dBottom);
  let x = rx;
  let y = ry;
  if (m === dLeft) x = 0;
  else if (m === dRight) x = 1;
  else if (m === dTop) y = 0;
  else y = 1;
  return { x: +x.toFixed(4), y: +y.toFixed(4) };
}

function terminalAbsPos(sym, t) {
  const b = bboxRect(sym);
  return { x: b.x + t.x * b.width, y: b.y + t.y * b.height };
}

function nearBbox(b, imgPt) {
  const m = Math.max(20, 0.4 * Math.min(b.width, b.height));
  return (
    imgPt.x >= b.x - m &&
    imgPt.x <= b.x + b.width + m &&
    imgPt.y >= b.y - m &&
    imgPt.y <= b.y + b.height + m
  );
}

function terminalHitTest(sym, imgPt) {
  const ts = sym.terminals || [];
  if (!ts.length) return -1;
  const tolImg = Math.max(8, (TERMINAL_R + 6) / (scale || 1));
  let best = -1;
  let bestD = tolImg;
  ts.forEach((t, i) => {
    const a = terminalAbsPos(sym, t);
    const d = Math.hypot(imgPt.x - a.x, imgPt.y - a.y);
    if (d <= bestD) {
      bestD = d;
      best = i;
    }
  });
  return best;
}

function symbolHitTest(imgPt) {
  for (let i = graph.symbols.length - 1; i >= 0; i--) {
    const r = bboxRect(graph.symbols[i]);
    if (
      imgPt.x >= r.x &&
      imgPt.x <= r.x + r.width &&
      imgPt.y >= r.y &&
      imgPt.y <= r.y + r.height
    ) {
      return i;
    }
  }
  return -1;
}

function markDirty() {
  dirty = true;
  saveStatusEl.textContent = "Niezapisane zmiany";
  touchRecentPage(currentPageId);
  renderRecentPages();
}

function applyGraph(data) {
  graph = {
    version: data.version ?? 2,
    page_id: data.page_id || currentPageId || "",
    image_width: data.image_width || canvas.width,
    image_height: data.image_height || canvas.height,
    symbols: (data.symbols || []).map((s) => ({
      id: s.id,
      type: typeStr(s.type),
      tag: s.tag || "",
      bbox: [...s.bbox],
      terminals: (s.terminals || []).map((t) => ({
        id: String(t.id),
        x: t.x,
        y: t.y,
        name: t.name || "",
      })),
    })),
    lines: data.lines || [],
  };
  symSeq = graph.symbols.reduce((m, s) => {
    const match = String(s.id).match(/^sym_(\d+)$/);
    return match ? Math.max(m, Number(match[1]) + 1) : m;
  }, 0);
  dirty = false;
}

function buildPayload() {
  return {
    version: 2,
    page_id: currentPageId,
    image_width: bgImage ? bgImage.naturalWidth : graph.image_width,
    image_height: bgImage ? bgImage.naturalHeight : graph.image_height,
    symbols: graph.symbols.map((s) => ({
      id: s.id,
      type: typeStr(s.type) || "unknown",
      tag: s.tag || undefined,
      bbox: s.bbox,
      terminals: (s.terminals || []).map((t) => ({
        id: t.id,
        x: t.x,
        y: t.y,
        name: t.name || "",
      })),
    })),
    lines: graph.lines,
  };
}

async function saveGraph() {
  if (!currentPageId) return;
  try {
    const payload = buildPayload();
    const res = await fetchJson(`/api/graph/${currentPageId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    dirty = false;
    const warn = res.warnings?.length ? ` (${res.warnings.length} ostrz.)` : "";
    saveStatusEl.textContent = `Zapisano: ${res.symbol_count} sym., ${res.line_count} linii${warn}`;
    touchRecentPage(currentPageId);
    const meta = pageMeta(currentPageId);
    if (meta) {
      meta.graph_updated_at = new Date().toISOString();
      meta.status = "labeled";
    }
    renderRecentPages();
    renderPageList();
  } catch (err) {
    saveStatusEl.textContent = `Błąd zapisu: ${err.message}`;
  }
}

async function runPrefill() {
  if (!currentPageId) return;
  if (graph.symbols.length && !window.confirm("Nadpisać bieżący graf draftem YOLO?")) return;
  try {
    saveStatusEl.textContent = "Import draft…";
    const res = await fetchJson(`/api/graph/${currentPageId}/prefill`, { method: "POST" });
    const data = await fetchJson(`/api/graph/${currentPageId}`);
    applyGraph(data);
    selectedSymIdx = -1;
    selectedTermIdx = -1;
    renderSymbolList();
    renderSymbolEditor();
    redraw();
    dirty = false;
    saveStatusEl.textContent =
      `Draft: ${res.symbol_count} sym., ${res.terminal_count} term.`;
    touchRecentPage(currentPageId);
    const meta = pageMeta(currentPageId);
    if (meta) meta.graph_updated_at = new Date().toISOString();
    renderRecentPages();
    renderPageList();
  } catch (err) {
    saveStatusEl.textContent = `Prefill: ${err.message}`;
  }
}

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  if (bgImage) ctx.drawImage(bgImage, 0, 0);

  graph.symbols.forEach((sym, i) => {
    const r = bboxRect(sym);
    const sel = i === selectedSymIdx;
    ctx.strokeStyle = sel ? BBOX_SEL : BBOX_COLOR;
    ctx.lineWidth = (sel ? 3 : 2) / scale;
    ctx.strokeRect(r.x, r.y, r.width, r.height);
    const label = [typeStr(sym.type), sym.tag].filter(Boolean).join(" ");
    if (label) {
      ctx.font = `bold ${14 / scale}px sans-serif`;
      ctx.fillStyle = "#fff";
      ctx.strokeStyle = "#111";
      ctx.lineWidth = 3 / scale;
      ctx.strokeText(label, r.x + 4 / scale, r.y - 6 / scale);
      ctx.fillText(label, r.x + 4 / scale, r.y - 6 / scale);
    }
  });

  graph.symbols.forEach((sym, i) => {
    const ts = sym.terminals || [];
    if (!ts.length) return;
    const selSym = i === selectedSymIdx;
    const r = TERMINAL_R / scale;
    ts.forEach((t, ti) => {
      const a = terminalAbsPos(sym, t);
      const selTerm = selSym && ti === selectedTermIdx;
      ctx.beginPath();
      ctx.arc(a.x, a.y, r + 2 / scale, 0, Math.PI * 2);
      ctx.fillStyle = "#fff";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(a.x, a.y, r, 0, Math.PI * 2);
      ctx.fillStyle = selTerm ? TERMINAL_SEL : TERMINAL_COLOR;
      ctx.fill();
      ctx.lineWidth = 2 / scale;
      ctx.strokeStyle = "#1a1a1a";
      ctx.stroke();
      const label = String(t.id);
      ctx.font = `bold ${12 / scale}px sans-serif`;
      ctx.fillStyle = "#111";
      ctx.fillText(label, a.x + r + 2 / scale, a.y - r);
    });
  });

  ctx.restore();
}

function pageMeta(pageId) {
  return pagesMeta.find((p) => p.id === pageId);
}

function pageEditedAt(page) {
  if (!page) return "";
  return page.graph_updated_at || page.annotation_updated_at || "";
}

function loadRecentPageIds() {
  try {
    const raw = localStorage.getItem(RECENT_PAGES_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (Array.isArray(parsed)) {
      return parsed.filter((id) => typeof id === "string" && id).slice(0, RECENT_PAGES_MAX);
    }
  } catch {
    /* ignore */
  }
  return [];
}

function saveRecentPageIds(ids) {
  localStorage.setItem(RECENT_PAGES_KEY, JSON.stringify(ids.slice(0, RECENT_PAGES_MAX)));
}

function touchRecentPage(pageId) {
  if (!pageId) return;
  const ids = loadRecentPageIds().filter((id) => id !== pageId);
  ids.unshift(pageId);
  saveRecentPageIds(ids);
}

function recentPageIds() {
  const seen = new Set();
  const out = [];
  for (const id of loadRecentPageIds()) {
    if (seen.has(id) || !pageMeta(id)) continue;
    seen.add(id);
    out.push(id);
    if (out.length >= RECENT_PAGES_MAX) return out;
  }
  const byServer = [...pagesMeta]
    .filter((p) => pageEditedAt(p))
    .sort((a, b) => pageEditedAt(b).localeCompare(pageEditedAt(a)));
  for (const p of byServer) {
    if (seen.has(p.id)) continue;
    seen.add(p.id);
    out.push(p.id);
    if (out.length >= RECENT_PAGES_MAX) break;
  }
  return out;
}

function renderRecentPages() {
  const list = document.getElementById("recent-page-list");
  if (!list) return;
  list.innerHTML = "";
  const ids = recentPageIds();
  if (!ids.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Brak historii edycji";
    list.appendChild(li);
    return;
  }
  ids.forEach((id) => {
    const p = pageMeta(id);
    const li = document.createElement("li");
    li.textContent = p?.filename || id;
    if (id === currentPageId) li.classList.add("active");
    li.title = id;
    li.onclick = () => selectPage(id);
    list.appendChild(li);
  });
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

function renderSymbolList() {
  const list = document.getElementById("symbol-list");
  list.innerHTML = "";
  graph.symbols.forEach((sym, i) => {
    const li = document.createElement("li");
    const nTerm = (sym.terminals || []).length;
    li.textContent = `${sym.id}: ${typeStr(sym.type) || "?"} ${sym.tag || ""} (${nTerm} term.)`;
    if (i === selectedSymIdx) li.classList.add("active");
    li.onclick = () => selectSymbol(i);
    list.appendChild(li);
  });
}

function renderTerminalList() {
  const list = document.getElementById("terminal-list");
  list.innerHTML = "";
  const sym = graph.symbols[selectedSymIdx];
  if (!sym) return;
  (sym.terminals || []).forEach((t, i) => {
    const li = document.createElement("li");
    li.textContent = `${t.id} @ (${t.x}, ${t.y})`;
    if (i === selectedTermIdx) li.style.color = TERMINAL_SEL;
    li.onclick = () => {
      selectedTermIdx = i;
      renderTerminalList();
      redraw();
    };
    list.appendChild(li);
  });
}

function renderSymbolEditor() {
  const sym = graph.symbols[selectedSymIdx];
  if (!sym) {
    symbolEditor.classList.add("hidden");
    return;
  }
  symbolEditor.classList.remove("hidden");
  symTypeInput.value = typeStr(sym.type);
  symTagInput.value = sym.tag || "";
  renderTerminalList();
}

function selectSymbol(idx) {
  selectedSymIdx = idx;
  selectedTermIdx = -1;
  renderSymbolList();
  renderSymbolEditor();
  redraw();
}

function deleteSelectedSymbol() {
  if (selectedSymIdx < 0) return;
  graph.symbols.splice(selectedSymIdx, 1);
  selectedSymIdx = -1;
  selectedTermIdx = -1;
  markDirty();
  renderSymbolList();
  renderSymbolEditor();
  redraw();
}

function deleteSelectedTerminal() {
  const sym = graph.symbols[selectedSymIdx];
  if (!sym || selectedTermIdx < 0) return;
  sym.terminals.splice(selectedTermIdx, 1);
  selectedTermIdx = -1;
  markDirty();
  renderTerminalList();
  redraw();
}

function typeStr(v) {
  if (typeof v === "string") return v;
  if (v && typeof v === "object") return String(v.id || v.label_pl || "");
  return v ? String(v) : "";
}

async function searchPalette(q) {
  if (!q.trim()) {
    paletteResults.innerHTML = "";
    return;
  }
  try {
    const data = await fetchJson(`/api/symbol-palette?q=${encodeURIComponent(q)}&limit=20`);
    paletteResults.innerHTML = "";
    (data.symbols || []).forEach((entry) => {
      const slug = typeStr(entry.id || entry);
      const label = entry.label_pl || slug || "?";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.onclick = () => {
        const sym = graph.symbols[selectedSymIdx];
        if (sym) {
          sym.type = slug;
          symTypeInput.value = slug;
          markDirty();
          renderSymbolList();
          redraw();
        }
        paletteResults.innerHTML = "";
      };
      paletteResults.appendChild(btn);
    });
  } catch {
    paletteResults.innerHTML = "";
  }
}

function addTerminalAt(symIdx, imgPt) {
  const sym = graph.symbols[symIdx];
  if (!sym) return;
  const b = bboxRect(sym);
  sym.terminals = sym.terminals || [];
  const rel = snapTerminalRel(b, imgPt);
  sym.terminals.push({ id: nextTerminalId(sym), x: rel.x, y: rel.y, name: "" });
  markDirty();
  renderTerminalList();
  renderSymbolList();
  redraw();
}

async function loadPages() {
  const pages = await fetchJson("/api/pages");
  pagesMeta = [...pages].sort((a, b) =>
    (a.id || "").localeCompare(b.id || "", undefined, { numeric: true })
  );
  pageIds = pagesMeta.map((p) => p.id);
  renderRecentPages();
  renderPageList();
  updatePageNav();
}

function currentPageIndex() {
  return pageIds.indexOf(currentPageId);
}

function updatePageNav() {
  const idx = currentPageIndex();
  const total = pageIds.length;
  if (total === 0) {
    pagePositionEl.textContent = "— / —";
    pagePrevBtn.disabled = true;
    pageNextBtn.disabled = true;
    return;
  }
  pagePositionEl.textContent = idx >= 0 ? `${idx + 1} / ${total}` : `— / ${total}`;
  pagePrevBtn.disabled = idx <= 0;
  pageNextBtn.disabled = idx >= total - 1;
}

async function selectPage(pageId) {
  if (!pageId) return;
  if (currentPageId && dirty) {
    const ok = window.confirm(`Zapisać zmiany na ${currentPageId} przed przejściem?`);
    if (ok) await saveGraph();
  }

  currentPageId = pageId;
  scale = 1;
  originX = 0;
  originY = 0;
  selectedSymIdx = -1;
  selectedTermIdx = -1;

  bgImage = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      resolve(img);
    };
    img.onerror = () => reject(new Error(`Nie można załadować: ${pageId}`));
    img.src = `/api/pages/${pageId}/image?t=${Date.now()}`;
  });

  try {
    const data = await fetchJson(`/api/graph/${pageId}`);
    applyGraph(data);
  } catch {
    applyGraph({
      version: 2,
      page_id: pageId,
      image_width: canvas.width,
      image_height: canvas.height,
      symbols: [],
      lines: [],
    });
  }

  renderSymbolList();
  renderSymbolEditor();
  renderPageList();
  renderRecentPages();
  updatePageNav();
  redraw();
  const idx = currentPageIndex();
  saveStatusEl.textContent = graph.symbols.length ? "Wczytano graf" : "Pusty graf — Import draft lub rysuj bbox";
  document.getElementById("hint").textContent =
    `Strona ${idx >= 0 ? idx + 1 : "?"} / ${pageIds.length}: ${pageId} — B = bbox | zaznacz → krawędź = terminal`;
}

function isTypingField(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  const imgPt = imgPointFromEvent(e);

  if (selectedSymIdx >= 0) {
    const sym = graph.symbols[selectedSymIdx];
    const hit = terminalHitTest(sym, imgPt);
    if (hit >= 0) {
      draggingTerminal = { symIdx: selectedSymIdx, termIdx: hit };
      selectedTermIdx = hit;
      terminalDragMoved = false;
      renderTerminalList();
      return;
    }
    const b = bboxRect(sym);
    if (nearBbox(b, imgPt)) {
      addTerminalAt(selectedSymIdx, imgPt);
      return;
    }
  }

  clickSelectCandidate = symbolHitTest(imgPt);
  drawing = true;
  drawMoved = false;
  startX = imgPt.x;
  startY = imgPt.y;
});

canvas.addEventListener("mousemove", (e) => {
  if (draggingTerminal) {
    const sym = graph.symbols[draggingTerminal.symIdx];
    const t = sym?.terminals?.[draggingTerminal.termIdx];
    if (!sym || !t) return;
    const rel = snapTerminalRel(bboxRect(sym), imgPointFromEvent(e));
    t.x = rel.x;
    t.y = rel.y;
    terminalDragMoved = true;
    redraw();
    return;
  }
  if (!drawing) return;
  const imgPt = imgPointFromEvent(e);
  const w = Math.abs(imgPt.x - startX);
  const h = Math.abs(imgPt.y - startY);
  if (w >= DRAG_THRESHOLD || h >= DRAG_THRESHOLD) drawMoved = true;
  redraw();
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  ctx.strokeStyle = BBOX_COLOR;
  ctx.lineWidth = 2 / scale;
  ctx.setLineDash([6 / scale, 3 / scale]);
  ctx.strokeRect(startX, startY, imgPt.x - startX, imgPt.y - startY);
  ctx.setLineDash([]);
  ctx.restore();
});

canvas.addEventListener("mouseup", (e) => {
  if (draggingTerminal) {
    if (terminalDragMoved) {
      markDirty();
      renderTerminalList();
    }
    draggingTerminal = null;
    return;
  }
  if (!drawing) return;
  drawing = false;
  const imgPt = imgPointFromEvent(e);

  if (!drawMoved) {
    if (clickSelectCandidate >= 0) {
      selectSymbol(clickSelectCandidate);
    } else {
      selectedSymIdx = -1;
      selectedTermIdx = -1;
      renderSymbolList();
      renderSymbolEditor();
      redraw();
    }
    return;
  }

  const x = Math.min(startX, imgPt.x);
  const y = Math.min(startY, imgPt.y);
  const w = Math.abs(imgPt.x - startX);
  const h = Math.abs(imgPt.y - startY);
  if (w < DRAG_THRESHOLD || h < DRAG_THRESHOLD) return;

  const sym = {
    id: nextSymId(),
    type: "",
    tag: "",
    bbox: rectToBbox(x, y, w, h),
    terminals: [],
  };
  graph.symbols.push(sym);
  selectedSymIdx = graph.symbols.length - 1;
  selectedTermIdx = -1;
  markDirty();
  renderSymbolList();
  renderSymbolEditor();
  symTypeInput.focus();
  redraw();
});

canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  const { cx, cy } = clientToCanvas(e);
  const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
  originX = cx - factor * (cx - originX);
  originY = cy - factor * (cy - originY);
  scale *= factor;
  redraw();
}, { passive: false });

document.addEventListener("keydown", (e) => {
  if (isTypingField(e.target)) {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      saveGraph();
    }
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    saveGraph();
    return;
  }
  if (e.key === "Escape") {
    selectedTermIdx = -1;
    if (selectedSymIdx >= 0) {
      selectedSymIdx = -1;
      renderSymbolList();
      renderSymbolEditor();
      redraw();
    }
    return;
  }
  if (e.key === "Delete" || e.key === "Backspace") {
    if (selectedSymIdx >= 0 && selectedTermIdx >= 0) {
      e.preventDefault();
      deleteSelectedTerminal();
      return;
    }
    if (selectedSymIdx >= 0) {
      e.preventDefault();
      deleteSelectedSymbol();
    }
  }
});

symTypeInput.addEventListener("input", () => {
  clearTimeout(paletteTimer);
  paletteTimer = setTimeout(() => searchPalette(symTypeInput.value), 200);
  const sym = graph.symbols[selectedSymIdx];
  if (sym) {
    sym.type = symTypeInput.value.trim();
    markDirty();
    renderSymbolList();
    redraw();
  }
});

symTagInput.addEventListener("input", () => {
  const sym = graph.symbols[selectedSymIdx];
  if (sym) {
    sym.tag = symTagInput.value.trim();
    markDirty();
    renderSymbolList();
    redraw();
  }
});

document.getElementById("save-btn").addEventListener("click", saveGraph);
document.getElementById("prefill-btn").addEventListener("click", runPrefill);
document.getElementById("delete-symbol-btn").addEventListener("click", deleteSelectedSymbol);
pagePrevBtn.addEventListener("click", () => {
  const idx = currentPageIndex();
  if (idx > 0) selectPage(pageIds[idx - 1]);
});
pageNextBtn.addEventListener("click", () => {
  const idx = currentPageIndex();
  if (idx >= 0 && idx < pageIds.length - 1) selectPage(pageIds[idx + 1]);
});

(async function init() {
  try {
    await loadPages();
    if (pageIds.length) await selectPage(pageIds[0]);
  } catch (err) {
    saveStatusEl.textContent = `Init: ${err.message}`;
  }
})();
