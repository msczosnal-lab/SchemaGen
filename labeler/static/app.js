// Prompt 010: bbox-first + paleta typów
// Canvas bbox — rysowanie, zoom, przypisanie typu po bboxie

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const DEFAULT_CLASS = "element";
const UNASSIGNED_COLOR = "#6c757d";
const BBOX_STROKE = 3.5;
const BBOX_STROKE_SELECTED = 4.5;

let currentPageId = null;
let pageIds = [];
let pagesMeta = [];
let bboxes = [];
let selectedIdx = -1;
let expandedIdx = -1;
let nextSeq = 1;
let focusSearchIdx = null;

let scale = 1;
let originX = 0;
let originY = 0;

let drawing = false;
let drawMoved = false;
let clickSelectCandidate = -1;
let startX = 0;
let startY = 0;
const DRAG_THRESHOLD = 5;

let bgImage = null;
let paletteCache = [];
let paletteCacheQuery = null;
let paletteSearchTimer = null;

// --- Tryb linii (prompt 002) ---
const MODE_BBOX = "bbox";
const MODE_LINE = "line";
let mode = MODE_BBOX;
let lines = [];                 // {id, points:[[x,y],...], role, style, semantic_group, color_ref}
let activeLine = null;          // rysowana linia: {points:[...]}
let selectedLineIdx = -1;
let cursorImgPt = null;         // podgląd "gumki" do następnego punktu
let eyedropperArmed = false;
let semanticGroups = [];        // [{name, stroke, fill, style, roles, description}]
const DEFAULT_LINE_ROLE = "wire";
const LINE_STROKE = 3;
const LINE_POINT_R = 4;

const LINE_ROLE_COLORS = {
  wire: "#111111",
  bus: "#c026d3",
  device_stroke: "#0066CC",
  frame: "#00AA44",
  dash: "#888888",
  crossing: "#d97706",
  leader: "#6b7280",
  other: "#6b7280",
};

function lineStrokeColor(line) {
  const grp = semanticGroups.find((g) => g.name === line.semantic_group);
  if (grp && grp.stroke) return grp.stroke;
  return LINE_ROLE_COLORS[line.role] || "#111111";
}

const editorHint = document.getElementById("editor-hint");
const pagePrevBtn = document.getElementById("page-prev");
const pageNextBtn = document.getElementById("page-next");
const pagePositionEl = document.getElementById("page-position");
const saveBtn = document.getElementById("save-btn");
const saveAllBtn = document.getElementById("save-all-btn");
const saveStatusEl = document.getElementById("save-status");

const DRAFT_PREFIX = "schemagen:draft:";
const LAST_TAG_KEY = "schemagen:last-tag";
const pageCache = new Map();
const dirtyPages = new Set();
let lastUsedTag = "";

function draftKey(pageId) {
  return `${DRAFT_PREFIX}${pageId}`;
}

function loadLastUsedTag() {
  try {
    return (localStorage.getItem(LAST_TAG_KEY) || "").trim();
  } catch {
    return "";
  }
}

function rememberLastTag(tag) {
  const t = (tag || "").trim();
  if (!t) return;
  lastUsedTag = t;
  try {
    localStorage.setItem(LAST_TAG_KEY, t);
  } catch {
    /* ignore */
  }
}

function suggestedTag(b) {
  return (b.tag || "").trim() || lastUsedTag;
}

function capturePageState() {
  return {
    bboxes: JSON.parse(JSON.stringify(bboxes)),
    lines: JSON.parse(JSON.stringify(lines)),
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
  lines = state?.lines ? JSON.parse(JSON.stringify(state.lines)) : [];
  sortBboxesNewestFirst();
  ensureSeqNumbers();
  if (state?.nextSeq && state.nextSeq > nextSeq) {
    nextSeq = state.nextSeq;
  }
}

function countUnassigned() {
  return bboxes.filter((b) => !(b.tag || "").trim()).length;
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
  const unassigned = countUnassigned();
  const dirty = currentPageId && dirtyPages.has(currentPageId);
  saveBtn.textContent = dirty ? `Zapisz strone (${n})*` : `Zapisz strone (${n})`;
  saveBtn.classList.toggle("dirty", !!dirty);
  const dirtyCount = dirtyPages.size;
  let extra = "";
  if (unassigned > 0) {
    extra = ` | ${unassigned} nieprzypisanych`;
  }
  if (dirtyCount > 0) {
    saveStatusEl.textContent = `Niezapisane: ${dirtyCount} str.${extra}`;
  } else if (unassigned > 0) {
    saveStatusEl.textContent = `${unassigned} bbox bez typu — przypisz po prawej`;
  } else if (pageCache.size > 0) {
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
        parent_id: b.parent_id || "",
        depth: b.depth || 0,
        rel_bbox: b.rel_bbox || [],
      })),
      lines: (state.lines || []).map((l) => ({
        id: l.id,
        points: l.points,
        role: l.role || DEFAULT_LINE_ROLE,
        style: l.style || "solid",
        semantic_group: l.semantic_group || "",
        color_ref: l.color_ref || "",
      })),
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
      const ua = res.unassigned_count ?? countUnassigned();
      saveStatusEl.textContent = `Zapisano ${pageId}: ${res.bbox_count ?? state.bboxes.length} bbox` +
        (ua ? ` (${ua} nieprzypisanych)` : "");
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

function isAssigned(b) {
  return !!(b.tag || "").trim();
}

function colorFromTag(tag) {
  if (!tag || !tag.trim()) return UNASSIGNED_COLOR;
  let h = 0;
  const s = tag.trim().toLocaleLowerCase("pl");
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  const hue = (h * 137.508) % 360;
  return `hsl(${hue.toFixed(1)}, 72%, 46%)`;
}

function contrastTextForTag(tag) {
  const color = colorFromTag(tag);
  const m = color.match(/hsl\([\d.]+,\s*[\d.]+%\s*,\s*([\d.]+)%\)/);
  if (!m) return "#fff";
  return parseFloat(m[1]) > 52 ? "#141414" : "#fff";
}

function applyTagUi(el, tag, { variant = "fill" } = {}) {
  const t = (tag || "").trim();
  if (!t) {
    el.style.removeProperty("background");
    el.style.removeProperty("color");
    el.style.removeProperty("border");
    el.style.removeProperty("--tag-color");
    return;
  }
  const color = colorFromTag(t);
  el.style.setProperty("--tag-color", color);
  if (variant === "fill" || variant === "preview") {
    el.style.background = color;
    el.style.color = contrastTextForTag(t);
    el.style.border = variant === "preview" ? "none" : `1px solid ${color}`;
    if (variant === "preview") {
      el.style.padding = "6px 8px";
      el.style.borderRadius = "4px";
    }
  } else if (variant === "border") {
    el.style.background = "";
    el.style.color = contrastTextForTag(t);
    el.style.borderColor = color;
    el.style.borderWidth = "2px";
    el.style.borderStyle = "solid";
  }
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
  const tag = (b.tag || "").trim();
  if (tag) return `#${b.seq || "?"} · ${tag}`;
  return `#${b.seq || "?"} · (?)`;
}

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

function listDisplayIndices() {
  return bboxes
    .map((_, i) => i)
    .sort((a, b) => (bboxes[b].seq || 0) - (bboxes[a].seq || 0));
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
  const assigned = isAssigned(b);
  const color = colorFromTag(b.tag);
  ctx.strokeStyle = color;
  ctx.lineWidth = BBOX_STROKE / scale;
  if (!assigned) {
    ctx.setLineDash([8 / scale, 4 / scale]);
  }
  ctx.strokeRect(b.x, b.y, b.width, b.height);
  ctx.setLineDash([]);

  if (i === selectedIdx) {
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = BBOX_STROKE_SELECTED / scale;
    ctx.setLineDash([6 / scale, 3 / scale]);
    ctx.strokeRect(b.x, b.y, b.width, b.height);
    ctx.setLineDash([]);
    if (b.parent_id) {
      const parent = bboxes.find((x) => x.id === b.parent_id);
      if (parent) {
        ctx.strokeStyle = "#ffd24a";
        ctx.lineWidth = 2.5 / scale;
        ctx.setLineDash([10 / scale, 5 / scale]);
        ctx.strokeRect(parent.x, parent.y, parent.width, parent.height);
        ctx.setLineDash([]);
      }
    }
  }

  drawBboxNumber(b, color);
}

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  if (bgImage) ctx.drawImage(bgImage, 0, 0);
  for (let i = bboxes.length - 1; i >= 0; i--) {
    drawBboxOnCanvas(bboxes[i], i);
  }
  for (let i = 0; i < lines.length; i++) {
    drawLineOnCanvas(lines[i], i);
  }
  drawActiveLine();
  ctx.restore();
}

function applyLineDash(line) {
  if (line.style === "dashed" || line.role === "dash") {
    ctx.setLineDash([10 / scale, 6 / scale]);
  } else if (line.style === "dotted") {
    ctx.setLineDash([2 / scale, 4 / scale]);
  } else {
    ctx.setLineDash([]);
  }
}

function drawLineOnCanvas(line, i) {
  const pts = line.points || [];
  if (pts.length < 1) return;
  const color = lineStrokeColor(line);
  ctx.strokeStyle = color;
  ctx.lineWidth = (i === selectedLineIdx ? LINE_STROKE + 1.5 : LINE_STROKE) / scale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  applyLineDash(line);
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1]);
  ctx.stroke();
  ctx.setLineDash([]);
  // wezly
  for (const p of pts) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p[0], p[1], LINE_POINT_R / scale, 0, Math.PI * 2);
    ctx.fill();
  }
  if (i === selectedLineIdx) {
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 1.5 / scale;
    for (const p of pts) {
      ctx.beginPath();
      ctx.arc(p[0], p[1], (LINE_POINT_R + 1.5) / scale, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
}

function drawActiveLine() {
  if (!activeLine || !activeLine.points.length) return;
  const pts = activeLine.points;
  ctx.strokeStyle = LINE_ROLE_COLORS[currentLineRole()] || "#111";
  ctx.lineWidth = LINE_STROKE / scale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1]);
  if (cursorImgPt) ctx.lineTo(cursorImgPt.x, cursorImgPt.y);
  ctx.stroke();
  for (const p of pts) {
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#111";
    ctx.lineWidth = 1.5 / scale;
    ctx.beginPath();
    ctx.arc(p[0], p[1], LINE_POINT_R / scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }
}

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
  await fetchJson("/api/element-catalog");
}

async function recordTagUsage(label) {
  const tag = (label || "").trim();
  if (!tag) return;
  try {
    await fetchJson("/api/tag-usage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ labels: [tag] }),
    });
    paletteCache = [];
    paletteCacheQuery = null;
    if (expandedIdx >= 0) renderAnnotationList();
  } catch (err) {
    console.warn("tag-usage:", err);
  }
}

async function fetchSymbolPalette(q = "") {
  const data = await fetchJson(`/api/symbol-palette?q=${encodeURIComponent(q)}&limit=60`);
  return data.symbols || [];
}

async function ensurePaletteCache(q = "") {
  if (paletteCache.length && paletteCacheQuery === q) return paletteCache;
  paletteCache = await fetchSymbolPalette(q);
  paletteCacheQuery = q;
  return paletteCache;
}

function assignTag(idx, tag) {
  if (idx < 0 || idx >= bboxes.length) return;
  const trimmed = (tag || "").trim();
  const prev = (bboxes[idx].tag || "").trim();
  bboxes[idx].tag = trimmed;
  markPageDirty();
  recomputeHierarchy();
  redraw();
  renderAnnotationList();
  updateSaveStatus();
  if (trimmed) {
    rememberLastTag(trimmed);
    if (trimmed !== prev) recordTagUsage(trimmed);
  }
}

function renderPaletteButtons(container, symbols, idx, onPick) {
  container.innerHTML = "";
  if (!symbols.length) {
    const empty = document.createElement("span");
    empty.className = "muted";
    empty.textContent = "Brak wynikow";
    container.appendChild(empty);
    return;
  }
  symbols.forEach((sym) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "palette-btn" + (sym.custom ? " custom" : "");
    const count = sym.usage_count || 0;
    const label = sym.label_pl || sym.id;
    btn.textContent = count > 0 ? `${label} (${count})` : label;
    applyTagUi(btn, label, { variant: "fill" });
    btn.title = [
      sym.tag_prefix ? `Prefiks: ${sym.tag_prefix}` : sym.id,
      sym.custom ? "Wolne haslo / wyjatek" : "",
      count > 0 ? `Uzyc: ${count}` : "",
    ].filter(Boolean).join(" · ");
    btn.addEventListener("mousedown", (e) => e.preventDefault());
    btn.addEventListener("click", () => onPick(label));
    container.appendChild(btn);
  });
}

function buildTypePicker(body, idx) {
  body.innerHTML = "";
  const b = bboxes[idx];
  const displayTag = suggestedTag(b);

  const preview = document.createElement("div");
  preview.className = "tag-preview " + (isAssigned(b) ? "assigned" : "unassigned");
  if (isAssigned(b)) {
    preview.textContent = `Typ: ${b.tag}`;
    applyTagUi(preview, b.tag, { variant: "preview" });
  } else if (lastUsedTag) {
    preview.textContent = `Ostatni typ: ${lastUsedTag}`;
    applyTagUi(preview, lastUsedTag, { variant: "preview" });
  } else {
    preview.textContent = "Nieprzypisany — wyszukaj lub wpisz haslo ponizej";
  }
  body.appendChild(preview);

  const typeInput = document.createElement("input");
  typeInput.type = "text";
  typeInput.className = "type-search";
  typeInput.placeholder = lastUsedTag
    ? `Ostatni: ${lastUsedTag} — Enter aby przypisac`
    : "Szukaj typ lub wpisz wyjatek (np. stycznik)…";
  typeInput.value = displayTag;
  typeInput.dataset.idx = String(idx);
  applyTagUi(typeInput, displayTag, { variant: "fill" });
  body.appendChild(typeInput);

  const resultsSection = document.createElement("div");
  resultsSection.className = "palette-section";
  const resultsTitle = document.createElement("h4");
  resultsTitle.className = "palette-section-title";
  resultsTitle.textContent = "Typy (najczesciej uzywane na gorze)";
  resultsSection.appendChild(resultsTitle);
  const resultsList = document.createElement("div");
  resultsList.className = "palette-list";
  resultsSection.appendChild(resultsList);
  body.appendChild(resultsSection);

  function pickLabel(label) {
    typeInput.value = label;
    assignTag(idx, label);
  }

  function commitInput() {
    const value = typeInput.value.trim();
    if (value !== (bboxes[idx].tag || "").trim()) {
      assignTag(idx, value);
    }
  }

  async function refreshResults(q) {
    const symbols = await ensurePaletteCache(q);
    resultsTitle.textContent = q.trim()
      ? "Wyniki wyszukiwania"
      : "Typy (najczesciej uzywane na gorze)";
    renderPaletteButtons(resultsList, symbols, idx, pickLabel);
  }

  typeInput.addEventListener("input", () => {
    clearTimeout(paletteSearchTimer);
    const q = typeInput.value.trim();
    applyTagUi(typeInput, q, { variant: "fill" });
    paletteSearchTimer = setTimeout(() => refreshResults(q), 200);
  });
  typeInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const first = resultsList.querySelector(".palette-btn");
      if (first) {
        first.click();
      } else {
        commitInput();
      }
    }
  });
  typeInput.addEventListener("blur", () => {
    if (typeInput.value.trim() !== (bboxes[idx].tag || "").trim()) {
      commitInput();
    }
  });

  refreshResults(typeInput.value.trim());

  if (focusSearchIdx === idx) {
    requestAnimationFrame(() => {
      typeInput.focus();
      typeInput.select();
      focusSearchIdx = null;
    });
  }
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
  focusSearchIdx = null;
  selectedLineIdx = -1;
  activeLine = null;
  cursorImgPt = null;

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
  let serverLines = [];
  try {
    const ann = await fetchJson(`/api/annotations/${pageId}`);
    serverBboxes = ann.bboxes || [];
    serverLines = ann.lines || [];
  } catch {
    serverBboxes = [];
    serverLines = [];
  }

  const cached = pageCache.get(pageId) || loadLocalDraft(pageId);
  if (cached?.bboxes?.length >= serverBboxes.length) {
    applyPageState(cached);
    if (cached.bboxes.length > serverBboxes.length) {
      dirtyPages.add(pageId);
    }
  } else {
    bboxes = serverBboxes;
    lines = serverLines;
    sortBboxesNewestFirst();
    ensureSeqNumbers();
    persistPageDraft(pageId);
  }

  recomputeHierarchy();
  redraw();
  renderAnnotationList();
  renderLineList();
  renderPageList();
  updatePageNav();
  updateSaveStatus();
  const idx = currentPageIndex();
  const pos = idx >= 0 ? `${idx + 1}/${pageIds.length}` : "?";
  document.getElementById("hint").textContent =
    `Strona ${pos}: ${pageId} — narysuj bbox, przypisz typ | Ctrl+S | / = szukaj`;
}

function toggleAccordion(i) {
  if (expandedIdx === i) {
    expandedIdx = -1;
    focusSearchIdx = null;
  } else {
    expandedIdx = i;
    selectedIdx = i;
    focusSearchIdx = i;
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
    empty.textContent = "Brak elementow — narysuj bbox na schemacie.";
    empty.style.background = "transparent";
    empty.style.border = "none";
    empty.style.cursor = "default";
    list.appendChild(empty);
    return;
  }
  listDisplayIndices().forEach((i) => {
    const b = bboxes[i];
    const isExpanded = i === expandedIdx;
    const row = document.createElement("li");
    row.className = "annotation-accordion";
    if (!isAssigned(b)) row.classList.add("unassigned");
    if (i === selectedIdx) row.classList.add("active");
    if (isExpanded) row.classList.add("expanded");
    if (b.depth) row.style.marginLeft = `${b.depth * 16}px`;

    const summary = document.createElement("div");
    summary.className = "accordion-summary";

    const line = document.createElement("button");
    line.type = "button";
    line.className = "summary-line";
    const pseq = parentSeqOf(b);
    line.textContent = pseq ? `${listLabel(b)}  ↳ w #${pseq}` : listLabel(b);
    line.title = isExpanded ? "Zwin" : (isAssigned(b) ? b.tag : "Przypisz typ");
    if (isAssigned(b)) {
      applyTagUi(line, b.tag, { variant: "fill" });
    }
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
      buildTypePicker(body, i);
      row.appendChild(body);
    }

    list.appendChild(row);
  });
}

function removeBboxAt(idx) {
  if (idx < 0 || idx >= bboxes.length) return;
  bboxes.splice(idx, 1);
  recomputeHierarchy();
  selectedIdx = -1;
  expandedIdx = -1;
  focusSearchIdx = null;
  markPageDirty();
  renderAnnotationList();
  redraw();
  updateSaveStatus();
}

function selectBbox(idx) {
  selectedIdx = idx;
  renderAnnotationList();
  redraw();
}

// ===== Linie (prompt 002) =====

const roleSelect = () => document.getElementById("line-role");
const groupSelect = () => document.getElementById("line-group");

function currentLineRole() {
  const el = roleSelect();
  return el ? el.value : DEFAULT_LINE_ROLE;
}

function currentLineGroup() {
  const el = groupSelect();
  return el ? el.value : "";
}

function roleDefaultStyle(role) {
  return role === "dash" ? "dashed" : "solid";
}

async function loadSemanticGroups() {
  try {
    const data = await fetchJson("/api/semantic-groups");
    semanticGroups = data.groups || [];
  } catch (err) {
    console.warn("semantic-groups:", err);
    semanticGroups = [];
  }
  const sel = groupSelect();
  if (sel) {
    sel.innerHTML = '<option value="">—</option>';
    semanticGroups.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = g.name;
      opt.textContent = g.description ? `${g.name} — ${g.description}` : g.name;
      sel.appendChild(opt);
    });
  }
}

function setMode(next) {
  mode = next;
  if (mode !== MODE_LINE) {
    activeLine = null;
    cursorImgPt = null;
    eyedropperArmed = false;
  }
  const bboxBtn = document.getElementById("mode-bbox");
  const lineBtn = document.getElementById("mode-line");
  const toolbar = document.getElementById("line-toolbar");
  if (bboxBtn) bboxBtn.classList.toggle("active", mode === MODE_BBOX);
  if (lineBtn) lineBtn.classList.toggle("active", mode === MODE_LINE);
  if (toolbar) toolbar.classList.toggle("hidden", mode !== MODE_LINE);
  canvas.style.cursor = mode === MODE_LINE ? "crosshair" : "default";
  document.getElementById("hint").textContent =
    mode === MODE_LINE
      ? "Linia: klik = punkt, Enter/dblklik = zakończ, Esc = anuluj | Del = usuń | pipeta = kolor"
      : "Bbox → typ → Zapisz | Ctrl+S | / = szukaj typu | B/L = tryb";
  redraw();
}

function finishActiveLine() {
  if (!activeLine || activeLine.points.length < 2) {
    activeLine = null;
    cursorImgPt = null;
    redraw();
    return;
  }
  const role = currentLineRole();
  const group = currentLineGroup();
  const grp = semanticGroups.find((g) => g.name === group);
  const line = {
    id: `line_${Date.now()}`,
    points: activeLine.points.map((p) => [Math.round(p[0]), Math.round(p[1])]),
    role,
    style: roleDefaultStyle(role),
    semantic_group: group,
    color_ref: grp && grp.stroke ? grp.stroke : "",
  };
  lines.push(line);
  activeLine = null;
  cursorImgPt = null;
  selectedLineIdx = lines.length - 1;
  markPageDirty();
  redraw();
  renderLineList();
  updateSaveStatus();
}

function cancelActiveLine() {
  activeLine = null;
  cursorImgPt = null;
  redraw();
}

function removeLineAt(idx) {
  if (idx < 0 || idx >= lines.length) return;
  lines.splice(idx, 1);
  selectedLineIdx = -1;
  markPageDirty();
  redraw();
  renderLineList();
  updateSaveStatus();
}

function selectLine(idx) {
  selectedLineIdx = idx;
  renderLineList();
  redraw();
}

function updateLineField(idx, field, value) {
  if (idx < 0 || idx >= lines.length) return;
  lines[idx][field] = value;
  if (field === "role") lines[idx].style = roleDefaultStyle(value);
  if (field === "semantic_group") {
    const grp = semanticGroups.find((g) => g.name === value);
    lines[idx].color_ref = grp && grp.stroke ? grp.stroke : "";
  }
  markPageDirty();
  redraw();
  renderLineList();
}

function pointSegDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  let t = len2 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
  t = Math.max(0, Math.min(1, t));
  const cx = ax + t * dx;
  const cy = ay + t * dy;
  return Math.hypot(px - cx, py - cy);
}

function hitTestLine(pt) {
  const tol = 6 / scale;
  for (let i = 0; i < lines.length; i++) {
    const pts = lines[i].points || [];
    for (let k = 0; k + 1 < pts.length; k++) {
      if (pointSegDist(pt.x, pt.y, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]) <= tol) {
        return i;
      }
    }
  }
  return -1;
}

function canvasPixelHex(imgX, imgY) {
  if (!bgImage) return null;
  const x = Math.round(imgX);
  const y = Math.round(imgY);
  if (x < 0 || y < 0 || x >= bgImage.naturalWidth || y >= bgImage.naturalHeight) return null;
  const off = document.createElement("canvas");
  off.width = 1;
  off.height = 1;
  const octx = off.getContext("2d", { willReadFrequently: true });
  octx.drawImage(bgImage, x, y, 1, 1, 0, 0, 1, 1);
  const d = octx.getImageData(0, 0, 1, 1).data;
  const hex = "#" + [d[0], d[1], d[2]].map((v) => v.toString(16).padStart(2, "0")).join("");
  return hex;
}

async function applyEyedropper(imgX, imgY) {
  const hex = canvasPixelHex(imgX, imgY);
  eyedropperArmed = false;
  canvas.style.cursor = mode === MODE_LINE ? "crosshair" : "default";
  if (!hex) return;
  try {
    const res = await fetchJson(`/api/match-color?hex=${encodeURIComponent(hex)}`);
    const sel = groupSelect();
    if (res.semantic_group && sel) {
      sel.value = res.semantic_group;
      saveStatusEl.textContent = `Pipeta ${hex} → grupa: ${res.semantic_group}`;
    } else {
      saveStatusEl.textContent = `Pipeta ${hex} → brak dopasowania grupy`;
    }
  } catch (err) {
    saveStatusEl.textContent = `Pipeta: blad match-color (${err.message})`;
  }
}

function renderLineList() {
  const list = document.getElementById("line-list");
  if (!list) return;
  list.innerHTML = "";
  if (!lines.length) {
    const empty = document.createElement("li");
    empty.className = "muted";
    empty.textContent = "Brak linii — przełącz na tryb Linia (L).";
    empty.style.background = "transparent";
    empty.style.border = "none";
    list.appendChild(empty);
    return;
  }
  lines.forEach((line, i) => {
    const row = document.createElement("li");
    row.className = "line-row";
    if (i === selectedLineIdx) row.classList.add("active");

    const swatch = document.createElement("span");
    swatch.className = "line-swatch";
    swatch.style.background = lineStrokeColor(line);
    row.appendChild(swatch);

    const label = document.createElement("button");
    label.type = "button";
    label.className = "line-label";
    const grpTxt = line.semantic_group ? ` · ${line.semantic_group}` : "";
    label.textContent = `${i + 1}. ${line.role}${grpTxt} (${line.points.length} pkt)`;
    label.addEventListener("click", () => selectLine(i));
    row.appendChild(label);

    const del = document.createElement("button");
    del.type = "button";
    del.className = "delete-btn";
    del.textContent = "×";
    del.title = "Usun linie";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      removeLineAt(i);
    });
    row.appendChild(del);

    if (i === selectedLineIdx) {
      const editor = document.createElement("div");
      editor.className = "line-editor";

      const roleSel = document.createElement("select");
      ["wire", "bus", "device_stroke", "frame", "dash", "crossing", "leader", "other"].forEach((r) => {
        const o = document.createElement("option");
        o.value = r;
        o.textContent = r;
        if (r === line.role) o.selected = true;
        roleSel.appendChild(o);
      });
      roleSel.addEventListener("change", () => updateLineField(i, "role", roleSel.value));
      editor.appendChild(roleSel);

      const grpSel = document.createElement("select");
      const none = document.createElement("option");
      none.value = "";
      none.textContent = "— grupa —";
      grpSel.appendChild(none);
      semanticGroups.forEach((g) => {
        const o = document.createElement("option");
        o.value = g.name;
        o.textContent = g.name;
        if (g.name === line.semantic_group) o.selected = true;
        grpSel.appendChild(o);
      });
      grpSel.addEventListener("change", () => updateLineField(i, "semantic_group", grpSel.value));
      editor.appendChild(grpSel);

      row.appendChild(editor);
    }

    list.appendChild(row);
  });
}

function isTypingField(el) {
  if (!el) return false;
  return el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable;
}

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  if (mode === MODE_LINE) {
    const { cx, cy } = clientToCanvas(e);
    const pt = canvasToImage(cx, cy);
    if (eyedropperArmed) {
      applyEyedropper(pt.x, pt.y);
      return;
    }
    if (!activeLine) {
      const hit = hitTestLine(pt);
      if (hit >= 0) {
        selectLine(hit);
        return;
      }
      activeLine = { points: [] };
    }
    const last = activeLine.points[activeLine.points.length - 1];
    if (!last || Math.hypot(pt.x - last[0], pt.y - last[1]) > 2 / scale) {
      activeLine.points.push([pt.x, pt.y]);
    }
    cursorImgPt = { x: pt.x, y: pt.y };
    redraw();
    return;
  }
  const { cx, cy } = clientToCanvas(e);
  const pt = canvasToImage(cx, cy);
  clickSelectCandidate = bboxes.findIndex(
    (b) => pt.x >= b.x && pt.x <= b.x + b.width && pt.y >= b.y && pt.y <= b.y + b.height
  );
  drawing = true;
  drawMoved = false;
  startX = pt.x;
  startY = pt.y;
});

canvas.addEventListener("mousemove", (e) => {
  if (mode === MODE_LINE) {
    if (!activeLine) return;
    const { cx, cy } = clientToCanvas(e);
    cursorImgPt = canvasToImage(cx, cy);
    redraw();
    return;
  }
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
  ctx.strokeStyle = UNASSIGNED_COLOR;
  ctx.lineWidth = 2 / scale;
  ctx.setLineDash([6 / scale, 3 / scale]);
  ctx.strokeRect(startX, startY, pt.x - startX, pt.y - startY);
  ctx.setLineDash([]);
  ctx.restore();
});

canvas.addEventListener("dblclick", (e) => {
  if (mode !== MODE_LINE) return;
  e.preventDefault();
  finishActiveLine();
});

canvas.addEventListener("mouseup", (e) => {
  if (mode === MODE_LINE) return;
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
      toggleAccordion(clickSelectCandidate);
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

  const id = `${DEFAULT_CLASS}_${Date.now()}`;
  bboxes.unshift({
    id,
    class_name: DEFAULT_CLASS,
    x,
    y,
    width: w,
    height: h,
    tag: "",
    seq: nextSeq++,
    parent_id: "",
    depth: 0,
    rel_bbox: [],
  });
  recomputeHierarchy();
  selectedIdx = 0;
  expandedIdx = 0;
  focusSearchIdx = 0;
  if (lastUsedTag) {
    assignTag(0, lastUsedTag);
  } else {
    markPageDirty();
    redraw();
    renderAnnotationList();
    updateSaveStatus();
  }
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
      savePageToServer(currentPageId);
    }
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    savePageToServer(currentPageId);
    return;
  }
  if (e.key === "b" || e.key === "B") {
    e.preventDefault();
    setMode(MODE_BBOX);
    return;
  }
  if (e.key === "l" || e.key === "L") {
    e.preventDefault();
    setMode(MODE_LINE);
    return;
  }
  if (mode === MODE_LINE && e.key === "Enter") {
    e.preventDefault();
    finishActiveLine();
    return;
  }
  if (e.key === "Escape") {
    if (activeLine) {
      e.preventDefault();
      cancelActiveLine();
      return;
    }
  }
  if ((e.key === "Delete" || e.key === "Backspace") && mode === MODE_LINE && selectedLineIdx >= 0) {
    e.preventDefault();
    removeLineAt(selectedLineIdx);
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
  if (e.key === "/" && expandedIdx >= 0) {
    e.preventDefault();
    focusSearchIdx = expandedIdx;
    renderAnnotationList();
    return;
  }
  if ((e.key === "Delete" || e.key === "Backspace") && selectedIdx >= 0) {
    removeBboxAt(selectedIdx);
  }
});

pagePrevBtn?.addEventListener("click", () => navigatePage(-1));
pageNextBtn?.addEventListener("click", () => navigatePage(1));

document.getElementById("mode-bbox")?.addEventListener("click", () => setMode(MODE_BBOX));
document.getElementById("mode-line")?.addEventListener("click", () => setMode(MODE_LINE));
document.getElementById("eyedropper-btn")?.addEventListener("click", () => {
  if (mode !== MODE_LINE) setMode(MODE_LINE);
  eyedropperArmed = !eyedropperArmed;
  canvas.style.cursor = eyedropperArmed ? "cell" : "crosshair";
  saveStatusEl.textContent = eyedropperArmed
    ? "Pipeta uzbrojona — kliknij piksel obrazu"
    : "Pipeta wyłączona";
});

async function init() {
  lastUsedTag = loadLastUsedTag();
  await loadSemanticGroups();
  setMode(MODE_BBOX);
  await loadPages();
  reportRecoveryHints();
  if (pageIds.length && currentPageId == null) {
    await selectPage(pageIds[0]);
  } else {
    updatePageNav();
  }
  await ensurePaletteCache("");
  renderLineList();
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
