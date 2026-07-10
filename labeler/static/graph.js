/** GT v2 labeler — bbox + terminale (krok 5, prompt 022). */

const BBOX_COLOR = "#f76707";
const BBOX_SEL = "#ffd43b";
const UNASSIGNED_COLOR = "#6c757d";
const TERMINAL_COLOR = "#ffd43b";
const TERMINAL_SEL = "#fa5252";
const TERMINAL_HIT_EXTRA = 14;
const TERMINAL_CREATE_PAD = 36;
const TERMINAL_LABEL_PX = 58;
const TERMINAL_LABEL_SEL_PX = 74;
const BBOX_LABEL_PX = 54;
const BBOX_LABEL_SEL_PX = 68;
const BBOX_STROKE = 5;
const BBOX_STROKE_SEL = 7;
const DRAG_THRESHOLD = 4;

const MODE_BBOX = "bbox";
const MODE_LINE = "line";
const LINE_COLOR = "#40c057";
const LINE_COLOR_SEL = "#94d82d";
/** Grubość linii i rozmiar terminali w px obrazu (skalują się z zoomem jak bbox). */
const LINE_STROKE = 4.5;
const LINE_STROKE_SEL = 6;
const TERMINAL_R = LINE_STROKE;
const TERMINAL_R_SEL = LINE_STROKE_SEL;

let mode = MODE_BBOX;
let lineDraft = null;
let cursorImgPt = null;
let selectedLineIdx = -1;
let selectedLineId = null;

const RECENT_PAGES_KEY = "graphRecentPages";
const LAST_PAGE_KEY = "graphLastPage";
const INVERT_BG_KEY = "graphInvertBg";
const RECENT_PAGES_MAX = 3;
const LAST_TYPE_KEY = "schemagen:last-tag";
const LAST_BBOX_TAG_KEY = "schemagen:last-graph-tag";
const LAST_RAIL_KEY = "schemagen:last-rail";
const LAYOUT_WIDTHS_KEY = "graphLayoutWidths";

let lastUsedType = "";
let lastUsedBboxTag = "";
let lastUsedRail = "";

let invertBg = loadStored(INVERT_BG_KEY) === "1";

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
let clickOnSelectedBBox = false;
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
const lineKindSelect = document.getElementById("line-kind");
const lineRailWrap = document.getElementById("line-rail-wrap");
const lineRailInput = document.getElementById("line-rail-input");
const deleteLineBtn = document.getElementById("delete-line-btn");

function loadStored(key) {
  try {
    return (localStorage.getItem(key) || "").trim();
  } catch {
    return "";
  }
}

function storeValue(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

function rememberLastType(type) {
  const t = typeStr(type).trim();
  if (!t) return;
  lastUsedType = t;
  storeValue(LAST_TYPE_KEY, t);
  updateTypeTagPlaceholders();
}

function rememberLastBboxTag(tag) {
  const t = (tag || "").trim();
  if (!t) return;
  lastUsedBboxTag = t;
  storeValue(LAST_BBOX_TAG_KEY, t);
  updateTypeTagPlaceholders();
}

function updateTypeTagPlaceholders() {
  symTypeInput.placeholder = lastUsedType
    ? `Ostatni: ${lastUsedType} — Enter aby przypisać`
    : "np. zlaczka, cewka_przekaznika";
  symTagInput.placeholder = lastUsedBboxTag
    ? `Ostatni: ${lastUsedBboxTag} — Enter aby przypisać`
    : "-K1";
}

function assignTypeToSelected(type) {
  const sym = graph.symbols[selectedSymIdx];
  if (!sym) return;
  const t = typeStr(type).trim();
  if (!t) return;
  sym.type = t;
  symTypeInput.value = t;
  applyInputTypeColor(symTypeInput, t);
  rememberLastType(t);
  markDirty();
  renderSymbolList();
  redraw();
}

function assignBboxTagToSelected(tag) {
  const sym = graph.symbols[selectedSymIdx];
  if (!sym) return;
  const t = (tag || "").trim();
  if (!t) return;
  sym.tag = t;
  symTagInput.value = t;
  applyInputTypeColor(symTagInput, t);
  rememberLastBboxTag(t);
  markDirty();
  renderSymbolList();
  redraw();
}

function applyLastDefaultsToSymbol(sym) {
  if (!sym) return;
  if (lastUsedType && !typeStr(sym.type).trim()) sym.type = lastUsedType;
  if (lastUsedBboxTag && !(sym.tag || "").trim()) sym.tag = lastUsedBboxTag;
}

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

function canvasDisplayMetrics() {
  const rect = canvas.getBoundingClientRect();
  const iw = canvas.width || 1;
  const ih = canvas.height || 1;
  const imgAspect = iw / ih;
  const boxAspect = rect.width / Math.max(rect.height, 1);
  let drawW;
  let drawH;
  let offsetX;
  let offsetY;
  if (boxAspect > imgAspect) {
    drawH = rect.height;
    drawW = drawH * imgAspect;
    offsetX = (rect.width - drawW) / 2;
    offsetY = 0;
  } else {
    drawW = rect.width;
    drawH = drawW / imgAspect;
    offsetX = 0;
    offsetY = (rect.height - drawH) / 2;
  }
  return { rect, drawW, drawH, offsetX, offsetY };
}

function clientToCanvas(e) {
  const m = canvasDisplayMetrics();
  const x = e.clientX - m.rect.left - m.offsetX;
  const y = e.clientY - m.rect.top - m.offsetY;
  return {
    cx: (x / m.drawW) * canvas.width,
    cy: (y / m.drawH) * canvas.height,
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

function insideBbox(b, imgPt) {
  return (
    imgPt.x >= b.x &&
    imgPt.x <= b.x + b.width &&
    imgPt.y >= b.y &&
    imgPt.y <= b.y + b.height
  );
}

/** Rozszerzony hit-test przy zaznaczonym bbox — łatwiejsze dodawanie terminala na krawędzi. */
function terminalCreateHit(sym, imgPt) {
  const b = bboxRect(sym);
  const pad = Math.max(16, TERMINAL_CREATE_PAD / (scale || 1));
  return (
    imgPt.x >= b.x - pad &&
    imgPt.x <= b.x + b.width + pad &&
    imgPt.y >= b.y - pad &&
    imgPt.y <= b.y + b.height + pad
  );
}

function typeStr(v) {
  if (typeof v === "string") return v;
  if (v && typeof v === "object") return String(v.id || v.label_pl || "");
  return v ? String(v) : "";
}

function symColorKey(sym) {
  const t = typeStr(sym?.type).trim();
  if (t) return t;
  return (sym?.tag || "").trim();
}

function colorFromKey(key) {
  if (!key || !key.trim()) return UNASSIGNED_COLOR;
  let h = 0;
  const s = key.trim().toLocaleLowerCase("pl");
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  const hue = (h * 137.508) % 360;
  return `hsl(${hue.toFixed(1)}, 72%, 46%)`;
}

function pillColorsFromKey(key) {
  const stroke = colorFromKey(key);
  return {
    fill: "#ffffff",
    stroke: stroke !== UNASSIGNED_COLOR ? stroke : BBOX_COLOR,
    text: "#111111",
  };
}

function applyInputTypeColor(input, key) {
  const k = (key || "").trim();
  input.style.background = "#2a2a2a";
  input.style.color = "#eee";
  if (!k) {
    input.style.removeProperty("border-left");
    return;
  }
  input.style.borderLeft = `4px solid ${colorFromKey(k)}`;
}

function bboxTagLabel(sym) {
  const tag = (sym.tag || "").trim();
  if (tag) return tag;
  const t = typeStr(sym.type);
  if (t) return t;
  return sym.id;
}

function imageToCanvasPt(x, y) {
  return { cx: x * scale + originX, cy: y * scale + originY };
}

/** Etykieta w px ekranu (canvas) — zawsze czytelna niezależnie od zoomu. */
function drawLabelPill(cx, cy, text, { selected = false, fontPx = TERMINAL_LABEL_PX, selFontPx = TERMINAL_LABEL_SEL_PX, variant = "terminal", colorKey = "" } = {}) {
  if (!text) return;
  const fs = selected ? selFontPx : fontPx;
  const pad = selected ? 9 : 7;
  ctx.save();
  ctx.font = `900 ${fs}px Segoe UI, Arial, sans-serif`;
  ctx.textBaseline = "alphabetic";
  const tw = ctx.measureText(text).width;
  const w = tw + pad * 2;
  const h = fs + pad * 2;
  const tx = cx;
  const ty = cy;
  const bx = tx - pad;
  const by = ty - fs - pad * 0.2;
  let textColor = "#111111";
  if (selected) {
    ctx.fillStyle = "#ffd43b";
    ctx.strokeStyle = TERMINAL_SEL;
    ctx.lineWidth = 4;
  } else if (variant === "bbox") {
    const pc = pillColorsFromKey(colorKey);
    ctx.fillStyle = pc.fill;
    ctx.strokeStyle = pc.stroke;
    ctx.lineWidth = 3;
    textColor = pc.text;
  } else if (variant === "line") {
    ctx.fillStyle = selected ? "#d3f9d8" : "#ffffff";
    ctx.strokeStyle = selected ? LINE_COLOR_SEL : LINE_COLOR;
    ctx.lineWidth = 3;
  } else {
    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = "#111111";
    ctx.lineWidth = 3;
  }
  ctx.fillRect(bx, by, w, h);
  ctx.strokeRect(bx, by, w, h);
  ctx.font = `900 ${fs}px Segoe UI, Arial, sans-serif`;
  const outline = selected ? 5 : 4;
  ctx.lineWidth = outline;
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#ffffff";
  ctx.strokeText(text, tx, ty);
  ctx.fillStyle = "#111111";
  ctx.fillText(text, tx, ty);
  ctx.restore();
}

function lineEndpoint(raw, which) {
  if (which === "from") return raw["from"] ?? raw.from_ref ?? raw.fromRef ?? "";
  return raw["to"] ?? raw.to_ref ?? raw.toRef ?? "";
}

function lineFromRef(line) {
  return lineEndpoint(line, "from");
}

function lineToRef(line) {
  return lineEndpoint(line, "to");
}

function graphContentBounds() {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  let n = 0;
  const grow = (x, y) => {
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
    n += 1;
  };
  for (const sym of graph.symbols) {
    const r = bboxRect(sym);
    grow(r.x, r.y);
    grow(r.x + r.width, r.y + r.height);
    for (const t of sym.terminals || []) {
      const a = terminalAbsPos(sym, t);
      grow(a.x, a.y);
    }
  }
  for (const line of graph.lines) {
    for (const pt of lineDisplayPoints(line)) grow(pt[0], pt[1]);
  }
  if (!n) return null;
  const span = Math.max(maxX - minX, maxY - minY, 40);
  const pad = span * 0.08 + 24;
  return {
    minX: minX - pad,
    minY: minY - pad,
    width: maxX - minX + pad * 2,
    height: maxY - minY + pad * 2,
  };
}

function applyDefaultView() {
  if (!graph.symbols.length && !graph.lines.length) {
    scale = 1;
    originX = 0;
    originY = 0;
    return;
  }
  const bounds = graphContentBounds();
  if (!bounds) {
    scale = 1;
    originX = 0;
    originY = 0;
    return;
  }
  const pad = Math.max(40, Math.min(canvas.width, canvas.height) * 0.02);
  const availW = canvas.width - 2 * pad;
  const availH = canvas.height - 2 * pad;
  scale = Math.min(availW / bounds.width, availH / bounds.height);
  scale = Math.min(Math.max(scale, 0.05), 32);
  originX = pad + (availW - bounds.width * scale) / 2 - bounds.minX * scale;
  originY = pad + (availH - bounds.height * scale) / 2 - bounds.minY * scale;
}

function parseTerminalRef(ref) {
  const s = String(ref || "");
  const i = s.lastIndexOf(":");
  if (i <= 0) return null;
  return { symId: s.slice(0, i), termId: s.slice(i + 1) };
}

/** Kolejny numer bbox (1-based) jak w liście symboli — bez luk w sym_N. */
function symbolListNr(sym) {
  const idx = graph.symbols.findIndex((s) => s.id === sym.id);
  return idx >= 0 ? idx + 1 : "?";
}

function formatLineEndpoint(ref) {
  const p = parseTerminalRef(ref);
  if (!p) return ref;
  const sym = graph.symbols.find((s) => s.id === p.symId);
  if (!sym) return ref;
  const nr = symbolListNr(sym);
  const tag = (sym.tag || "").trim();
  const type = typeStr(sym.type);
  const name = tag || type || sym.id;
  return `#${nr} ${name} · T${p.termId}`;
}

function lineNum(id) {
  const m = String(id).match(/^L(\d+)$/);
  return m ? Number(m[1]) : Number.MAX_SAFE_INTEGER;
}

function formatLineLabel(line) {
  const kind = line.kind || "power";
  const rail = (line.rail || "").trim();
  const railPart = kind === "link" && rail ? ` · ${rail}` : "";
  return `${line.id}: ${formatLineEndpoint(lineFromRef(line))} → ${formatLineEndpoint(lineToRef(line))} [${kind}${railPart}]`;
}

function lineIdxById(id) {
  if (!id) return -1;
  return graph.lines.findIndex((l) => l.id === id);
}

function syncSelectedLineIdx() {
  const idx = lineIdxById(selectedLineId);
  if (idx < 0) {
    selectedLineId = null;
    selectedLineIdx = -1;
  } else {
    selectedLineIdx = idx;
  }
  return selectedLineIdx;
}

function selectedLine() {
  const idx = syncSelectedLineIdx();
  return idx >= 0 ? graph.lines[idx] : null;
}

function rememberLastRail(rail) {
  const t = (rail || "").trim();
  if (!t) return;
  lastUsedRail = t;
  storeValue(LAST_RAIL_KEY, t);
}

function currentLineRail() {
  return (lineRailInput?.value || lastUsedRail || "").trim();
}

function isLinkKind(kind) {
  return (kind || "power") === "link";
}

function terminalHitTest(sym, imgPt) {
  const ts = sym.terminals || [];
  if (!ts.length) return -1;
  const tolImg = Math.max(14, (TERMINAL_R + TERMINAL_HIT_EXTRA) / (scale || 1));
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

function findTerminalAt(imgPt) {
  for (let i = graph.symbols.length - 1; i >= 0; i--) {
    const sym = graph.symbols[i];
    const ti = terminalHitTest(sym, imgPt);
    if (ti >= 0) {
      const t = sym.terminals[ti];
      return { symIdx: i, termIdx: ti, ref: `${sym.id}:${t.id}` };
    }
  }
  return null;
}

function terminalPosByRef(ref) {
  const p = parseTerminalRef(ref);
  if (!p) return null;
  const sym = graph.symbols.find((s) => s.id === p.symId);
  if (!sym) return null;
  const t = (sym.terminals || []).find((x) => String(x.id) === p.termId);
  if (!t) return null;
  return terminalAbsPos(sym, t);
}

function nextLineId() {
  const used = new Set(graph.lines.map((l) => l.id));
  let n = 1;
  while (used.has(`L${n}`)) n += 1;
  return `L${n}`;
}

function currentLineKind() {
  return lineKindSelect?.value || "power";
}

function syncLineToolPanel() {
  syncSelectedLineIdx();
  const line = selectedLine();
  const kind = line ? line.kind || "power" : currentLineKind();
  const showLink = isLinkKind(kind);

  if (lineKindSelect) {
    if (line) lineKindSelect.value = kind;
    else if (!lineKindSelect.value) lineKindSelect.value = "power";
  }

  if (lineRailWrap) lineRailWrap.classList.toggle("hidden", !showLink);
  if (lineRailInput) {
    if (line && isLinkKind(line.kind)) {
      lineRailInput.value = line.rail || "";
    } else if (showLink && !lineRailInput.value.trim()) {
      lineRailInput.value = lastUsedRail;
    }
    lineRailInput.placeholder = lastUsedRail ? `Ostatni: ${lastUsedRail}` : "-X1";
  }

  if (deleteLineBtn) deleteLineBtn.classList.toggle("hidden", !line);
}

/** @deprecated użyj syncLineToolPanel */
function syncLineKindSelect() {
  syncLineToolPanel();
}

function lineAnchorPoint() {
  if (!lineDraft) return null;
  if (lineDraft.middles.length) return lineDraft.middles[lineDraft.middles.length - 1];
  return [lineDraft.fromPos.x, lineDraft.fromPos.y];
}

function applyLineOrtho(anchor, raw, orthoOn) {
  if (!anchor || !orthoOn) return raw;
  const dx = Math.abs(raw.x - anchor[0]);
  const dy = Math.abs(raw.y - anchor[1]);
  if (dx >= dy) return { x: raw.x, y: anchor[1] };
  return { x: anchor[0], y: raw.y };
}

function lineSnapPoint(raw, shiftKey) {
  void shiftKey;
  return applyLineOrtho(lineAnchorPoint(), raw, true);
}

function orthoCornerPoint(from, to) {
  const fx = Array.isArray(from) ? from[0] : from.x;
  const fy = Array.isArray(from) ? from[1] : from.y;
  const dx = Math.abs(to.x - fx);
  const dy = Math.abs(to.y - fy);
  if (dx >= dy) return [to.x, fy];
  return [fx, to.y];
}

function orthoRoutePoints(from, to) {
  const corner = orthoCornerPoint(from, to);
  return [
    [from.x, from.y],
    [Math.round(corner[0]), Math.round(corner[1])],
    [to.x, to.y],
  ];
}

function ptEq(a, b, tol = 0.5) {
  return Math.hypot(a[0] - b[0], a[1] - b[1]) <= tol;
}

function orthoLinkPoints(from, to) {
  const fx = from[0];
  const fy = from[1];
  const tx = to[0];
  const ty = to[1];
  if (ptEq(from, to)) return [from];
  if (Math.abs(fx - tx) < 0.5 || Math.abs(fy - ty) < 0.5) {
    return [from, to];
  }
  const corner = orthoCornerPoint({ x: fx, y: fy }, { x: tx, y: ty });
  return [from, [Math.round(corner[0]), Math.round(corner[1])], to];
}

function simplifyOrthoCollinear(pts) {
  if (pts.length < 3) return pts;
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const a = out[out.length - 1];
    const b = pts[i];
    const c = pts[i + 1];
    const collinearH = Math.abs(a[1] - b[1]) < 0.5 && Math.abs(b[1] - c[1]) < 0.5;
    const collinearV = Math.abs(a[0] - b[0]) < 0.5 && Math.abs(b[0] - c[0]) < 0.5;
    if (!collinearH && !collinearV) out.push(b);
  }
  out.push(pts[pts.length - 1]);
  return out;
}

/** Łańcuch waypointów → polyline H/V (tylko kąty 90°). */
function chainOrthoPoints(waypoints) {
  if (!waypoints || waypoints.length < 2) return waypoints ? waypoints.map((p) => [...p]) : [];
  let chain = [];
  for (let i = 0; i < waypoints.length - 1; i++) {
    const seg = orthoLinkPoints(waypoints[i], waypoints[i + 1]);
    if (!chain.length) chain.push([...seg[0]]);
    for (let j = 1; j < seg.length; j++) {
      const p = [...seg[j]];
      const last = chain[chain.length - 1];
      if (!ptEq(last, p)) chain.push(p);
    }
  }
  return simplifyOrthoCollinear(chain);
}

function extractInteriorVertices(line, fromPos, toPos) {
  const v = (line.vertices || []).map((p) => [Number(p[0]), Number(p[1])]);
  if (v.length <= 2) return [];
  const start = [fromPos.x, fromPos.y];
  const end = [toPos.x, toPos.y];
  if (ptEq(v[0], start) && ptEq(v[v.length - 1], end)) {
    return v.slice(1, -1);
  }
  return v;
}

function verticesForOrthoChain(chain) {
  const pts = (chain || []).map((p) => [Math.round(p[0]), Math.round(p[1])]);
  if (pts.length < 2) return [];
  const straight =
    pts.length === 2 &&
    (Math.abs(pts[0][0] - pts[1][0]) < 0.5 || Math.abs(pts[0][1] - pts[1][1]) < 0.5);
  return straight ? [] : pts;
}

function finalizeLineVertices(fromPos, toPos, toTerm, userMiddles) {
  let mids = (userMiddles || []).map((p) => [p[0], p[1]]);
  if (mids.length && toTerm) {
    mids = snapLastMiddleForTerminal(mids, fromPos, toPos, toTerm);
  }
  const chain = chainOrthoPoints([
    [fromPos.x, fromPos.y],
    ...mids,
    [toPos.x, toPos.y],
  ]);
  return verticesForOrthoChain(chain);
}

function orthoNormalizeLineVertices(line) {
  const a = terminalPosByRef(lineFromRef(line));
  const b = terminalPosByRef(lineToRef(line));
  if (!a || !b) return (line.vertices || []).map((v) => [...v]);
  const toHit = resolveTerminalByRef(lineToRef(line));
  const toTerm =
    toHit != null ? graph.symbols[toHit.symIdx]?.terminals?.[toHit.termIdx] : null;
  const interior = extractInteriorVertices(line, a, b);
  return finalizeLineVertices(a, b, toTerm, interior);
}

function verticesEqual(a, b) {
  const va = a || [];
  const vb = b || [];
  if (va.length !== vb.length) return false;
  for (let i = 0; i < va.length; i++) {
    if (Math.abs(va[i][0] - vb[i][0]) > 0.5 || Math.abs(va[i][1] - vb[i][1]) > 0.5) {
      return false;
    }
  }
  return true;
}

function lineDisplayPoints(line) {
  const v = orthoNormalizeLineVertices(line);
  const a = terminalPosByRef(lineFromRef(line));
  const b = terminalPosByRef(lineToRef(line));
  if (!a || !b) return v.length ? v : [];
  if (v.length) return v;
  return [[Math.round(a.x), Math.round(a.y)], [Math.round(b.x), Math.round(b.y)]];
}

function distPointSeg(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  if (len2 < 1e-6) return Math.hypot(px - ax, py - ay);
  let t = ((px - ax) * dx + (py - ay) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function pickLineAt(imgPt) {
  const tol = Math.max(10, (LINE_STROKE_SEL + 8) / (scale || 1));
  let best = -1;
  let bestD = tol;
  graph.lines.forEach((line, i) => {
    const pts = lineDisplayPoints(line);
    for (let j = 0; j < pts.length - 1; j++) {
      const d = distPointSeg(
        imgPt.x,
        imgPt.y,
        pts[j][0],
        pts[j][1],
        pts[j + 1][0],
        pts[j + 1][1]
      );
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    }
  });
  return best;
}

function purgeLinesUsingRef(ref) {
  const before = graph.lines.length;
  graph.lines = graph.lines.filter((l) => lineFromRef(l) !== ref && lineToRef(l) !== ref);
  if (graph.lines.length === before) return false;
  if (selectedLineId && lineIdxById(selectedLineId) < 0) {
    selectedLineId = null;
    selectedLineIdx = -1;
  } else {
    syncSelectedLineIdx();
  }
  renderLineList();
  syncLineToolPanel();
  return true;
}

function purgeLinesForSymbol(symId) {
  const before = graph.lines.length;
  graph.lines = graph.lines.filter((l) => {
    const from = parseTerminalRef(lineFromRef(l));
    const to = parseTerminalRef(lineToRef(l));
    return from?.symId !== symId && to?.symId !== symId;
  });
  if (graph.lines.length === before) return false;
  if (selectedLineId && lineIdxById(selectedLineId) < 0) {
    selectedLineId = null;
    selectedLineIdx = -1;
  } else {
    syncSelectedLineIdx();
  }
  renderLineList();
  syncLineToolPanel();
  return true;
}

function resolveTerminalByRef(ref) {
  const p = parseTerminalRef(ref);
  if (!p) return null;
  const symIdx = graph.symbols.findIndex((s) => s.id === p.symId);
  if (symIdx < 0) return null;
  const termIdx = (graph.symbols[symIdx].terminals || []).findIndex(
    (t) => String(t.id) === p.termId
  );
  if (termIdx < 0) return null;
  return { symIdx, termIdx, ref: `${p.symId}:${p.termId}` };
}

function terminalUsedRef(ref) {
  return graph.lines.some((l) => lineFromRef(l) === ref || lineToRef(l) === ref);
}

function removeTerminalByRef(ref) {
  const hit = resolveTerminalByRef(ref);
  if (!hit) return false;
  graph.symbols[hit.symIdx].terminals.splice(hit.termIdx, 1);
  if (selectedSymIdx === hit.symIdx && selectedTermIdx === hit.termIdx) {
    selectedTermIdx = -1;
  } else if (selectedSymIdx === hit.symIdx && selectedTermIdx > hit.termIdx) {
    selectedTermIdx -= 1;
  }
  return true;
}

/** Usuń terminale niepodpięte do żadnej linii (np. po skasowaniu jedynej linii). */
function purgeOrphanTerminalRefs(refs) {
  let changed = false;
  for (const ref of refs) {
    if (!ref || terminalUsedRef(ref)) continue;
    if (removeTerminalByRef(ref)) changed = true;
  }
  return changed;
}

function selectLineById(id) {
  selectLine(lineIdxById(id));
}

function selectLine(idx) {
  if (idx < 0 || idx >= graph.lines.length) {
    selectedLineId = null;
    selectedLineIdx = -1;
    syncLineToolPanel();
    renderLineList();
    redraw();
    return;
  }
  cancelLineDraft();
  selectedLineIdx = idx;
  selectedLineId = graph.lines[idx].id;
  syncLineToolPanel();
  renderLineList();
  redraw();
}

function terminalEdge(t) {
  const dL = t.x;
  const dR = 1 - t.x;
  const dT = t.y;
  const dB = 1 - t.y;
  const m = Math.min(dL, dR, dT, dB);
  if (m === dL) return "left";
  if (m === dR) return "right";
  if (m === dT) return "top";
  return "bottom";
}

function terminalSlidesY(edge) {
  return edge === "left" || edge === "right";
}

function terminalSlidesX(edge) {
  return edge === "top" || edge === "bottom";
}

function setTerminalAbsPos(sym, term, absX, absY) {
  const b = bboxRect(sym);
  const edge = terminalEdge(term);
  if (edge === "left") {
    term.x = 0;
    term.y = +Math.max(0, Math.min(1, (absY - b.y) / (b.height || 1))).toFixed(4);
  } else if (edge === "right") {
    term.x = 1;
    term.y = +Math.max(0, Math.min(1, (absY - b.y) / (b.height || 1))).toFixed(4);
  } else if (edge === "top") {
    term.y = 0;
    term.x = +Math.max(0, Math.min(1, (absX - b.x) / (b.width || 1))).toFixed(4);
  } else {
    term.y = 1;
    term.x = +Math.max(0, Math.min(1, (absX - b.x) / (b.width || 1))).toFixed(4);
  }
}

/** Bez przegubów: przesuń terminale wzdłuż krawędzi, aby linia była prosta H/V. */
function alignTerminalsStraight(fromHit, toHit) {
  const fromSym = graph.symbols[fromHit.symIdx];
  const toSym = graph.symbols[toHit.symIdx];
  const fromTerm = fromSym.terminals[fromHit.termIdx];
  const toTerm = toSym.terminals[toHit.termIdx];
  const fromPos = terminalAbsPos(fromSym, fromTerm);
  const toPos = terminalAbsPos(toSym, toTerm);
  const fromEdge = terminalEdge(fromTerm);
  const toEdge = terminalEdge(toTerm);

  if (terminalSlidesY(fromEdge) && terminalSlidesY(toEdge)) {
    const targetY = (fromPos.y + toPos.y) / 2;
    setTerminalAbsPos(fromSym, fromTerm, fromPos.x, targetY);
    setTerminalAbsPos(toSym, toTerm, toPos.x, targetY);
    return true;
  }
  if (terminalSlidesX(fromEdge) && terminalSlidesX(toEdge)) {
    const targetX = (fromPos.x + toPos.x) / 2;
    setTerminalAbsPos(fromSym, fromTerm, targetX, fromPos.y);
    setTerminalAbsPos(toSym, toTerm, targetX, toPos.y);
    return true;
  }
  return false;
}

/** Po kliknięciu terminala DO: ostatni przegub → kąt 90° (wejście prostopadle do krawędzi). */
function snapLastMiddleForTerminal(middles, fromPos, toPos, toTerm) {
  if (!middles.length) return [];
  const m = middles.map((p) => [p[0], p[1]]);
  const prev = m.length > 1 ? m[m.length - 2] : [fromPos.x, fromPos.y];
  const edge = terminalEdge(toTerm);
  let last;
  if (terminalSlidesY(edge)) {
    // terminal L/R — ostatni odcinek poziomy
    last = [Math.round(prev[0]), Math.round(toPos.y)];
  } else {
    // terminal T/B — ostatni odcinek pionowy
    last = [Math.round(toPos.x), Math.round(prev[1])];
  }
  if (Math.hypot(last[0] - toPos.x, last[1] - toPos.y) < 1) {
    if (terminalSlidesY(edge)) {
      last[0] = prev[0] === toPos.x ? prev[0] - 24 : prev[0];
    } else {
      last[1] = prev[1] === toPos.y ? prev[1] - 24 : prev[1];
    }
  }
  m[m.length - 1] = last;
  return m;
}

function cancelLineDraft() {
  lineDraft = null;
  cursorImgPt = null;
}

function startLineDraft(hit) {
  if (terminalUsedRef(hit.ref)) {
    saveStatusEl.textContent = `Terminal zajęty: ${formatLineEndpoint(hit.ref)} — każdy terminal max 1 linia`;
    return;
  }
  const sym = graph.symbols[hit.symIdx];
  const pos = terminalAbsPos(sym, sym.terminals[hit.termIdx]);
  lineDraft = { fromRef: hit.ref, fromPos: pos, middles: [] };
  selectedLineId = null;
  selectedLineIdx = -1;
  syncLineToolPanel();
  saveStatusEl.textContent = `Linia OD ${formatLineEndpoint(hit.ref)} — klik terminal DO (Esc / Enter)`;
}

let lineCompleting = false;

function completeLineDraft(hit) {
  if (lineCompleting || !lineDraft || hit.ref === lineDraft.fromRef) return;
  if (terminalUsedRef(hit.ref)) {
    saveStatusEl.textContent = `Terminal zajęty: ${formatLineEndpoint(hit.ref)} — każdy terminal max 1 linia`;
    return;
  }
  if (graph.lines.some((l) => lineFromRef(l) === lineDraft.fromRef && lineToRef(l) === hit.ref)) {
    saveStatusEl.textContent = "Taka linia już istnieje (ten sam OD → DO)";
    return;
  }
  lineCompleting = true;
  try {
    const fromHit = resolveTerminalByRef(lineDraft.fromRef);
    const toSym = graph.symbols[hit.symIdx];
    const toTerm = toSym.terminals[hit.termIdx];
    if (!fromHit) return;

    const fromSym = graph.symbols[fromHit.symIdx];
    const fromTerm = fromSym.terminals[fromHit.termIdx];
    if (!lineDraft.middles.length) {
      alignTerminalsStraight(fromHit, hit);
    }
    const a = terminalAbsPos(fromSym, fromTerm);
    const b = terminalAbsPos(toSym, toTerm);
    const vertices = finalizeLineVertices(a, b, toTerm, lineDraft.middles);

    const kind = currentLineKind();
    const rail = isLinkKind(kind) ? currentLineRail() : "";
    if (rail) rememberLastRail(rail);

    const line = {
      id: nextLineId(),
      from: lineDraft.fromRef,
      to: hit.ref,
      vertices,
      kind,
      rail,
    };
    graph.lines.push(line);
    cancelLineDraft();
    markDirty();
    renderSymbolList();
    renderLineList();
    redraw();
    saveStatusEl.textContent = `Dodano ${formatLineLabel(line)}`;
  } finally {
    lineCompleting = false;
  }
}

function addLineMiddlePoint(imgPt, shiftKey) {
  if (!lineDraft) return;
  const pt = lineSnapPoint(imgPt, shiftKey);
  const anchor = lineAnchorPoint();
  if (anchor && Math.hypot(pt.x - anchor[0], pt.y - anchor[1]) <= 2 / scale) return;
  lineDraft.middles.push([pt.x, pt.y]);
  markDirty();
  redraw();
}

function deleteSelectedLine() {
  const idx = syncSelectedLineIdx();
  if (idx < 0) {
    saveStatusEl.textContent = "Zaznacz linię (lista lub klik na linii)";
    syncLineToolPanel();
    renderLineList();
    redraw();
    return;
  }
  const removed = graph.lines[idx];
  const orphanRefs = [lineFromRef(removed), lineToRef(removed)];
  cancelLineDraft();
  graph.lines.splice(idx, 1);
  selectedLineId = null;
  selectedLineIdx = -1;
  purgeOrphanTerminalRefs(orphanRefs);
  markDirty();
  renderLineList();
  renderSymbolList();
  renderTerminalList();
  renderSymbolEditor();
  syncLineToolPanel();
  redraw();
  saveStatusEl.textContent = removed ? `Usunięto ${removed.id}` : "Usunięto linię";
}

function updateSidebarForMode() {
  document.getElementById("bbox-tool-panel")?.classList.toggle("hidden", mode !== MODE_BBOX);
  document.getElementById("line-tool-panel")?.classList.toggle("hidden", mode !== MODE_LINE);
}

function setMode(next) {
  mode = next;
  drawing = false;
  drawMoved = false;
  draggingTerminal = null;
  if (mode !== MODE_LINE) cancelLineDraft();
  if (mode === MODE_LINE) {
    selectedSymIdx = -1;
    selectedTermIdx = -1;
    renderSymbolEditor();
  } else {
    renderLineList();
  }
  updateSidebarForMode();
  syncLineToolPanel();
  document.getElementById("mode-bbox")?.classList.toggle("active", mode === MODE_BBOX);
  document.getElementById("mode-line")?.classList.toggle("active", mode === MODE_LINE);
  canvas.style.cursor = mode === MODE_LINE ? "crosshair" : "default";
  const hintEl = document.getElementById("hint");
  if (hintEl) {
    hintEl.textContent =
      mode === MODE_LINE
        ? "Linia: klik krawędź bbox (terminal) OD → opcjonalnie załamania → klik krawędź DO · Esc = anuluj"
        : "Bbox: przeciągnij · zaznaczony + klik w środku = terminal · poza = odznacz";
  }
  redraw();
}

function renderLineList() {
  const list = document.getElementById("line-list");
  if (!list) return;
  const countEl = document.getElementById("line-count");
  if (countEl) countEl.textContent = String(graph.lines.length);
  list.innerHTML = "";
  const order = graph.lines.map((line, i) => ({ line, i }));
  order.sort((a, b) => lineNum(a.line.id) - lineNum(b.line.id) || a.i - b.i);
  order.forEach(({ line, i }) => {
    const li = document.createElement("li");
    li.textContent = formatLineLabel(line);
    if (line.id === selectedLineId) li.classList.add("active");
    li.onclick = () => selectLineById(line.id);
    list.appendChild(li);
  });
  syncLineToolPanel();
}

function lineDraftPreviewPoints() {
  if (!lineDraft) return [];
  const waypoints = [
    [lineDraft.fromPos.x, lineDraft.fromPos.y],
    ...lineDraft.middles.map((m) => [m[0], m[1]]),
  ];
  if (cursorImgPt) {
    const pt = lineSnapPoint(cursorImgPt, false);
    waypoints.push([pt.x, pt.y]);
  }
  if (waypoints.length < 2) return waypoints;
  return chainOrthoPoints(waypoints);
}

function drawPolylineImage(points, { color = LINE_COLOR, width = LINE_STROKE, dash = [] } = {}) {
  if (!points || points.length < 2) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i][0], points[i][1]);
  }
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawTerminalDot(x, y, { selected = false } = {}) {
  const r = selected ? TERMINAL_R_SEL : TERMINAL_R;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = selected ? TERMINAL_SEL : TERMINAL_COLOR;
  ctx.fill();
  ctx.lineWidth = Math.max(1, r * 0.35);
  ctx.strokeStyle = "#1a1a1a";
  ctx.stroke();
}

/** Linie + terminale w px obrazu (wewnątrz ctx.scale — zoom jak podkład). */
function drawWiresAndTerminalsImage() {
  const selIdx = syncSelectedLineIdx();
  graph.lines.forEach((line, i) => {
    const pts = lineDisplayPoints(line);
    drawPolylineImage(pts, {
      color: i === selIdx ? LINE_COLOR_SEL : LINE_COLOR,
      width: i === selIdx ? LINE_STROKE_SEL : LINE_STROKE,
    });
  });

  if (mode === MODE_LINE && selIdx >= 0) {
    const line = graph.lines[selIdx];
    const a = terminalPosByRef(lineFromRef(line));
    const b = terminalPosByRef(lineToRef(line));
    if (a) drawTerminalDot(a.x, a.y, { selected: false });
    if (b) drawTerminalDot(b.x, b.y, { selected: false });
  }

  graph.symbols.forEach((sym, i) => {
    const ts = sym.terminals || [];
    if (!ts.length) return;
    const selSym = i === selectedSymIdx;
    ts.forEach((t, ti) => {
      const a = terminalAbsPos(sym, t);
      drawTerminalDot(a.x, a.y, { selected: selSym && ti === selectedTermIdx });
    });
  });

  if (lineDraft) {
    drawPolylineImage(lineDraftPreviewPoints(), {
      color: "#82c91e",
      width: LINE_STROKE,
      dash: [LINE_STROKE * 2, LINE_STROKE * 1.5],
    });
    drawTerminalDot(lineDraft.fromPos.x, lineDraft.fromPos.y, { selected: false });
  }
}

function lineMidpointImage(line) {
  const pts = lineDisplayPoints(line);
  if (!pts.length) return null;
  const idx = Math.floor((pts.length - 1) / 2);
  return { x: pts[idx][0], y: pts[idx][1] };
}

function markDirty() {
  dirty = true;
  saveStatusEl.textContent = "Niezapisane zmiany";
  touchRecentPage(currentPageId);
  renderRecentPages();
}

function normalizeLines(raw) {
  const seenId = new Set();
  const seenPair = new Set();
  const out = [];
  for (const l of raw || []) {
    const from = lineEndpoint(l, "from");
    const to = lineEndpoint(l, "to");
    if (!from || !to) continue;
    const pairKey = `${from}|${to}`;
    if (seenId.has(l.id) || seenPair.has(pairKey)) continue;
    seenId.add(l.id);
    seenPair.add(pairKey);
    out.push({
      id: l.id,
      from,
      to,
      vertices: (l.vertices || []).map((v) => [...v]),
      kind: l.kind || "power",
      rail: (l.rail || "").trim(),
    });
  }
  return out;
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
    lines: normalizeLines(data.lines),
  };
  let orthoFixed = false;
  graph.lines = graph.lines.map((ln) => {
    const verts = orthoNormalizeLineVertices(ln);
    if (!verticesEqual(ln.vertices, verts)) orthoFixed = true;
    return { ...ln, vertices: verts };
  });
  symSeq = graph.symbols.reduce((m, s) => {
    const match = String(s.id).match(/^sym_(\d+)$/);
    return match ? Math.max(m, Number(match[1]) + 1) : m;
  }, 0);
  dirty = orthoFixed;
  selectedLineId = null;
  selectedLineIdx = -1;
  syncLineToolPanel();
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
    lines: graph.lines.map((l) => ({
      id: l.id,
      from: lineFromRef(l),
      to: lineToRef(l),
      vertices: orthoNormalizeLineVertices(l),
      kind: l.kind || "power",
      rail: (l.rail || "").trim() || undefined,
    })),
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
    selectedLineId = null;
    selectedLineIdx = -1;
    cancelLineDraft();
    renderSymbolList();
    renderSymbolEditor();
    renderLineList();
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

function updateInvertBgButton() {
  const btn = document.getElementById("invert-bg-btn");
  if (!btn) return;
  btn.classList.toggle("active", invertBg);
  btn.setAttribute("aria-pressed", invertBg ? "true" : "false");
  document.body.classList.toggle("invert-bg", invertBg);
}

function setInvertBg(on) {
  invertBg = !!on;
  storeValue(INVERT_BG_KEY, invertBg ? "1" : "0");
  updateInvertBgButton();
  redraw();
}

function toggleInvertBg() {
  setInvertBg(!invertBg);
}

function drawBgImage() {
  if (!bgImage) return;
  if (invertBg) {
    ctx.filter = "invert(1)";
    ctx.drawImage(bgImage, 0, 0);
    ctx.filter = "none";
  } else {
    ctx.drawImage(bgImage, 0, 0);
  }
}

function redraw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.filter = "none";
  ctx.setLineDash([]);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(originX, originY);
  ctx.scale(scale, scale);
  drawBgImage();

  graph.symbols.forEach((sym, i) => {
    const r = bboxRect(sym);
    const sel = i === selectedSymIdx;
    const col = colorFromKey(symColorKey(sym));
    ctx.strokeStyle = sel ? BBOX_SEL : col !== UNASSIGNED_COLOR ? col : BBOX_COLOR;
    ctx.lineWidth = sel ? BBOX_STROKE_SEL : BBOX_STROKE;
    ctx.strokeRect(r.x, r.y, r.width, r.height);
  });

  drawWiresAndTerminalsImage();

  ctx.restore();

  if (mode === MODE_BBOX) {
    graph.symbols.forEach((sym, i) => {
      const r = bboxRect(sym);
      const cx = (r.x + r.width / 2) * scale + originX;
      const cy = r.y * scale + originY - 10;
      drawLabelPill(cx, cy, bboxTagLabel(sym), {
        selected: i === selectedSymIdx,
        fontPx: BBOX_LABEL_PX,
        selFontPx: BBOX_LABEL_SEL_PX,
        variant: "bbox",
        colorKey: symColorKey(sym),
      });
    });
  }

  graph.symbols.forEach((sym, i) => {
    const selSym = i === selectedSymIdx;
    const symNr = symbolListNr(sym);
    (sym.terminals || []).forEach((t, ti) => {
      const a = terminalAbsPos(sym, t);
      const selTerm = selSym && ti === selectedTermIdx;
      const dotR = selTerm ? TERMINAL_R_SEL : TERMINAL_R;
      const p = imageToCanvasPt(a.x, a.y);
      drawLabelPill(p.cx + dotR * scale + 10, p.cy + 6, `${symNr}:${t.id}`, {
        selected: selTerm,
        fontPx: TERMINAL_LABEL_PX,
        selFontPx: TERMINAL_LABEL_SEL_PX,
        variant: "terminal",
      });
    });
  });

  if (mode === MODE_LINE) {
    const selIdx = syncSelectedLineIdx();
    graph.lines.forEach((line, i) => {
      const mid = lineMidpointImage(line);
      if (!mid) return;
      const p = imageToCanvasPt(mid.x, mid.y);
      const rail = isLinkKind(line.kind) && (line.rail || "").trim();
      const label = rail ? `${line.id} ${rail}` : line.id;
      drawLabelPill(p.cx, p.cy - 14, label, {
        selected: i === selIdx,
        fontPx: 26,
        selFontPx: 32,
        variant: "line",
      });
    });
  }
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
    const col = colorFromKey(symColorKey(sym));
    li.style.borderLeftColor = col !== UNASSIGNED_COLOR ? col : BBOX_COLOR;
    li.style.removeProperty("background");
    li.style.color = "#eee";
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
  applyInputTypeColor(symTypeInput, typeStr(sym.type));
  applyInputTypeColor(symTagInput, sym.tag);
  updateTypeTagPlaceholders();
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
  const sym = graph.symbols[selectedSymIdx];
  const symId = sym?.id;
  graph.symbols.splice(selectedSymIdx, 1);
  selectedSymIdx = -1;
  selectedTermIdx = -1;
  if (symId) purgeLinesForSymbol(symId);
  markDirty();
  renderSymbolList();
  renderSymbolEditor();
  renderLineList();
  redraw();
}

function deleteSelectedTerminal() {
  const sym = graph.symbols[selectedSymIdx];
  if (!sym || selectedTermIdx < 0) return;
  const term = sym.terminals[selectedTermIdx];
  const ref = term ? `${sym.id}:${term.id}` : "";
  sym.terminals.splice(selectedTermIdx, 1);
  selectedTermIdx = -1;
  if (ref) purgeLinesUsingRef(ref);
  markDirty();
  renderTerminalList();
  renderLineList();
  redraw();
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
      const c = colorFromKey(slug);
      btn.style.background = "";
      btn.style.color = "#eee";
      if (c !== UNASSIGNED_COLOR) {
        btn.style.borderLeft = `4px solid ${c}`;
      } else {
        btn.style.removeProperty("border-left");
      }
      btn.onclick = () => {
        assignTypeToSelected(slug);
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
  if (!sym) return null;
  const b = bboxRect(sym);
  sym.terminals = sym.terminals || [];
  const rel = snapTerminalRel(b, imgPt);
  const term = { id: nextTerminalId(sym), x: rel.x, y: rel.y, name: "" };
  sym.terminals.push(term);
  markDirty();
  renderTerminalList();
  renderSymbolList();
  redraw();
  return {
    symIdx,
    termIdx: sym.terminals.length - 1,
    ref: `${sym.id}:${term.id}`,
  };
}

/** Tryb linia: istniejący terminal albo nowy na najbliższej krawędzi bboxa. */
function findOrCreateTerminalAt(imgPt) {
  const hit = findTerminalAt(imgPt);
  if (hit) return hit;

  for (let i = graph.symbols.length - 1; i >= 0; i--) {
    const sym = graph.symbols[i];
    if (!terminalCreateHit(sym, imgPt)) continue;
    return addTerminalAt(i, imgPt);
  }
  return null;
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

function pickInitialPageId() {
  const last = loadStored(LAST_PAGE_KEY);
  if (last && pageIds.includes(last)) return last;
  for (const id of recentPageIds()) {
    if (pageIds.includes(id)) return id;
  }
  return pageIds[0];
}

async function selectPage(pageId) {
  if (!pageId) return;
  if (currentPageId && dirty) {
    const ok = window.confirm(`Zapisać zmiany na ${currentPageId} przed przejściem?`);
    if (ok) await saveGraph();
  }

  currentPageId = pageId;
  storeValue(LAST_PAGE_KEY, pageId);
  selectedSymIdx = -1;
  selectedTermIdx = -1;
  selectedLineId = null;
  selectedLineIdx = -1;
  cancelLineDraft();

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
    const data = await fetchJson(`/api/graph/${pageId}?t=${Date.now()}`);
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
  renderLineList();
  renderPageList();
  renderRecentPages();
  updatePageNav();
  applyDefaultView();
  redraw();
  requestAnimationFrame(() => {
    applyDefaultView();
    redraw();
  });
  const idx = currentPageIndex();
  const nSym = graph.symbols.length;
  const nLin = graph.lines.length;
  if (!nSym && !nLin) {
    saveStatusEl.textContent = "Pusty graf — Import draft lub rysuj bbox";
  } else {
    saveStatusEl.textContent = `Wczytano: ${nSym} sym., ${nLin} linii`;
  }
  setMode(mode);
}

function isTypingField(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  const imgPt = imgPointFromEvent(e);

  if (mode === MODE_LINE) {
    const termHit = findOrCreateTerminalAt(imgPt);
    if (termHit) {
      if (!lineDraft) startLineDraft(termHit);
      else completeLineDraft(termHit);
    } else if (lineDraft) {
      addLineMiddlePoint(imgPt, e.shiftKey);
    } else {
      const li = pickLineAt(imgPt);
      if (li >= 0) selectLine(li);
      else {
        selectedLineIdx = -1;
        renderLineList();
        syncLineKindSelect();
        saveStatusEl.textContent =
          "Kliknij linię (zaznacz) lub krawędź bboxa (terminal OD/DO)";
      }
    }
    redraw();
    return;
  }

  for (let i = graph.symbols.length - 1; i >= 0; i--) {
    const hit = terminalHitTest(graph.symbols[i], imgPt);
    if (hit >= 0) {
      selectSymbol(i);
      draggingTerminal = { symIdx: i, termIdx: hit };
      selectedTermIdx = hit;
      terminalDragMoved = false;
      renderTerminalList();
      return;
    }
  }

  clickSelectCandidate = symbolHitTest(imgPt);
  clickOnSelectedBBox =
    selectedSymIdx >= 0 && terminalCreateHit(graph.symbols[selectedSymIdx], imgPt);
  drawing = true;
  drawMoved = false;
  startX = imgPt.x;
  startY = imgPt.y;
});

canvas.addEventListener("mousemove", (e) => {
  if (mode === MODE_LINE) {
    if (lineDraft) {
      cursorImgPt = lineSnapPoint(imgPointFromEvent(e), e.shiftKey);
      redraw();
    }
    return;
  }
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
  ctx.lineWidth = BBOX_STROKE / scale;
  ctx.setLineDash([6 / scale, 3 / scale]);
  ctx.strokeRect(startX, startY, imgPt.x - startX, imgPt.y - startY);
  ctx.setLineDash([]);
  ctx.restore();
});

canvas.addEventListener("mouseup", (e) => {
  if (mode === MODE_LINE) return;
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
    if (clickOnSelectedBBox && selectedSymIdx >= 0) {
      const sym = graph.symbols[selectedSymIdx];
      if (sym && terminalCreateHit(sym, imgPt)) {
        addTerminalAt(selectedSymIdx, imgPt);
        return;
      }
    }
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
  applyLastDefaultsToSymbol(sym);
  markDirty();
  renderSymbolList();
  renderSymbolEditor();
  symTypeInput.focus();
  symTypeInput.select();
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
  if (e.key === "i" || e.key === "I") {
    e.preventDefault();
    toggleInvertBg();
    return;
  }
  if (e.key === "Escape") {
    if (lineDraft) {
      cancelLineDraft();
      saveStatusEl.textContent = "Anulowano rysowanie linii";
      redraw();
      return;
    }
    if (selectedLineIdx >= 0) {
      selectedLineIdx = -1;
      renderLineList();
      redraw();
      return;
    }
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
    if (mode === MODE_LINE && lineDraft) {
      e.preventDefault();
      if (lineDraft.middles?.length) {
        lineDraft.middles.pop();
        markDirty();
      } else {
        cancelLineDraft();
      }
      redraw();
      return;
    }
    if (selectedLineIdx >= 0 && graph.lines[selectedLineIdx]) {
      e.preventDefault();
      deleteSelectedLine();
      return;
    }
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
    applyInputTypeColor(symTypeInput, sym.type);
    markDirty();
    renderSymbolList();
    redraw();
  }
});

symTypeInput.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const value = symTypeInput.value.trim() || lastUsedType;
  if (value) assignTypeToSelected(value);
});

symTypeInput.addEventListener("blur", () => {
  const sym = graph.symbols[selectedSymIdx];
  const value = symTypeInput.value.trim();
  if (sym && value) rememberLastType(value);
});

symTagInput.addEventListener("input", () => {
  const sym = graph.symbols[selectedSymIdx];
  if (sym) {
    sym.tag = symTagInput.value.trim();
    applyInputTypeColor(symTagInput, sym.tag);
    markDirty();
    renderSymbolList();
    redraw();
  }
});

symTagInput.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const value = symTagInput.value.trim() || lastUsedBboxTag;
  if (value) assignBboxTagToSelected(value);
});

symTagInput.addEventListener("blur", () => {
  const sym = graph.symbols[selectedSymIdx];
  const value = symTagInput.value.trim();
  if (sym && value) rememberLastBboxTag(value);
});

document.getElementById("save-btn").addEventListener("click", saveGraph);

if (lineKindSelect) {
  lineKindSelect.addEventListener("change", () => {
    if (selectedLineIdx < 0 || !graph.lines[selectedLineIdx]) return;
    graph.lines[selectedLineIdx].kind = currentLineKind();
    markDirty();
    renderLineList();
  });
}
document.getElementById("prefill-btn").addEventListener("click", runPrefill);
document.getElementById("delete-symbol-btn").addEventListener("click", deleteSelectedSymbol);
document.getElementById("delete-line-btn")?.addEventListener("click", deleteSelectedLine);
document.getElementById("mode-bbox")?.addEventListener("click", () => setMode(MODE_BBOX));
document.getElementById("mode-line")?.addEventListener("click", () => setMode(MODE_LINE));
document.getElementById("invert-bg-btn")?.addEventListener("click", toggleInvertBg);
pagePrevBtn.addEventListener("click", () => {
  const idx = currentPageIndex();
  if (idx > 0) selectPage(pageIds[idx - 1]);
});
pageNextBtn.addEventListener("click", () => {
  const idx = currentPageIndex();
  if (idx >= 0 && idx < pageIds.length - 1) selectPage(pageIds[idx + 1]);
});

function readLayoutVar(layout, name, fallback) {
  const raw = getComputedStyle(layout).getPropertyValue(name).trim();
  const n = parseFloat(raw);
  return Number.isFinite(n) ? n : fallback;
}

function saveLayoutWidths(layout) {
  try {
    localStorage.setItem(
      LAYOUT_WIDTHS_KEY,
      JSON.stringify({
        left: readLayoutVar(layout, "--left-w", 280),
        right: readLayoutVar(layout, "--right-w", 320),
      })
    );
  } catch {
    /* ignore */
  }
}

function initPanelResize() {
  const layout = document.getElementById("graph-layout");
  const leftHandle = document.getElementById("resize-left");
  const rightHandle = document.getElementById("resize-right");
  if (!layout || !leftHandle || !rightHandle) return;

  try {
    const saved = JSON.parse(localStorage.getItem(LAYOUT_WIDTHS_KEY) || "{}");
    if (saved.left) layout.style.setProperty("--left-w", `${saved.left}px`);
    if (saved.right) layout.style.setProperty("--right-w", `${saved.right}px`);
  } catch {
    /* ignore */
  }

  function bindHandle(handle, side) {
    handle.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      handle.classList.add("dragging");
      document.body.style.cursor = "col-resize";
      const startX = e.clientX;
      const startLeft = readLayoutVar(layout, "--left-w", 280);
      const startRight = readLayoutVar(layout, "--right-w", 320);

      function onMove(ev) {
        const dx = ev.clientX - startX;
        if (side === "left") {
          const w = Math.min(520, Math.max(200, Math.round(startLeft + dx)));
          layout.style.setProperty("--left-w", `${w}px`);
        } else {
          const w = Math.min(560, Math.max(240, Math.round(startRight - dx)));
          layout.style.setProperty("--right-w", `${w}px`);
        }
      }

      function onUp() {
        handle.classList.remove("dragging");
        document.body.style.removeProperty("cursor");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        saveLayoutWidths(layout);
      }

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }

  bindHandle(leftHandle, "left");
  bindHandle(rightHandle, "right");
}

(async function init() {
  lastUsedType = loadStored(LAST_TYPE_KEY);
  lastUsedBboxTag = loadStored(LAST_BBOX_TAG_KEY);
  updateTypeTagPlaceholders();
  updateInvertBgButton();
  try {
    localStorage.removeItem("graphViewportByPage");
  } catch {
    /* ignore */
  }
  initPanelResize();
  try {
    await loadPages();
    if (pageIds.length) await selectPage(pickInitialPageId());
  } catch (err) {
    saveStatusEl.textContent = `Init: ${err.message}`;
  }
})();
