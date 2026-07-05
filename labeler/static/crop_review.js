/**
 * Crop viewport + tryby review (terminale, bbox, connection).
 * Wymaga globals z app.js: bgImage, canvas, ctx, bboxes, lines, connections,
 * selectedIdx, mode constants, markPageDirty, fetchJson, saveStatusEl, redraw hook.
 */
(function () {
  const CROP_PAD_FRAC = 0.18;
  const CROP_PAD_MIN = 40;

  let cropRect = null; // {x1,y1,x2,y2} image coords or null
  let reviewQueueIdx = 0;
  let reviewQueue = [];
  let reviewKind = null; // 'terminal' | 'bbox' | 'connection'
  let pageTerminalsDerived = false;
  let terminalCfg = null;

  async function loadTerminalCfg() {
    if (terminalCfg) return terminalCfg;
    try {
      terminalCfg = await fetchJson("/api/terminal-config");
    } catch {
      terminalCfg = { contact_tol_frac: 0.012, contact_tol_min: 12, merge_tol_cap: 15 };
    }
    return terminalCfg;
  }

  function terminalTol() {
    const { w, h } = imgSize();
    const big = Math.max(w, h);
    if (terminalCfg) {
      return Math.max(terminalCfg.contact_tol_min, terminalCfg.contact_tol_frac * big);
    }
    return Math.max(12, 0.012 * big);
  }

  function mergeTol(contactTol) {
    const cap = terminalCfg?.merge_tol_cap ?? 15;
    return Math.min(contactTol, cap);
  }

  function imgSize() {
    return {
      w: bgImage?.naturalWidth || canvas.width,
      h: bgImage?.naturalHeight || canvas.height,
    };
  }

  function bboxCropRect(b, padFrac = CROP_PAD_FRAC) {
    const { w: iw, h: ih } = imgSize();
    const padX = Math.max(CROP_PAD_MIN, b.width * padFrac);
    const padY = Math.max(CROP_PAD_MIN, b.height * padFrac);
    return {
      x1: Math.max(0, b.x - padX),
      y1: Math.max(0, b.y - padY),
      x2: Math.min(iw, b.x + b.width + padX),
      y2: Math.min(ih, b.y + b.height + padY),
    };
  }

  function unionRect(a, b) {
    return {
      x1: Math.min(a.x1, b.x1),
      y1: Math.min(a.y1, b.y1),
      x2: Math.max(a.x2, b.x2),
      y2: Math.max(a.y2, b.y2),
    };
  }

  function setCropRect(rect) {
    cropRect = rect;
    if (!rect || !bgImage) return;
    const sw = Math.max(1, rect.x2 - rect.x1);
    const sh = Math.max(1, rect.y2 - rect.y1);
    canvas.width = Math.round(sw);
    canvas.height = Math.round(sh);
    scale = 1;
    originX = 0;
    originY = 0;
  }

  function clearCropRect() {
    cropRect = null;
    if (bgImage) {
      canvas.width = bgImage.naturalWidth;
      canvas.height = bgImage.naturalHeight;
    }
    scale = 1;
    originX = 0;
    originY = 0;
  }

  function isCropActive() {
    return cropRect != null;
  }

  function withCropCtx(drawFn) {
    if (!cropRect || !bgImage) {
      drawFn(false);
      return;
    }
    const { x1, y1, x2, y2 } = cropRect;
    const sw = x2 - x1;
    const sh = y2 - y1;
    ctx.drawImage(bgImage, x1, y1, sw, sh, 0, 0, canvas.width, canvas.height);
    ctx.save();
    const sx = canvas.width / sw;
    const sy = canvas.height / sh;
    ctx.scale(sx, sy);
    ctx.translate(-x1, -y1);
    drawFn(true);
    ctx.restore();
  }

  function resolveBboxForRef(ref) {
    if (!ref) return null;
    const compId = String(ref).split(":")[0];
    const idx = bboxes.findIndex((b) => b.id === compId);
    return idx >= 0 ? { b: bboxes[idx], idx } : null;
  }

  async function deriveTerminalsForPage() {
    if (!lines.length) {
      saveStatusEl.textContent =
        "Brak linii — zaimportuj draft (Import draft) lub narysuj linie (L) i Zapisz";
      return false;
    }
    await loadTerminalCfg();
    const tol = terminalTol();
    try {
      const res = await fetchJson("/api/derive-terminals-page", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bboxes: bboxes.map((b) => ({
            id: b.id,
            bbox: [b.x, b.y, b.x + b.width, b.y + b.height],
          })),
          lines: lines.map((l) => ({
            points: l.points,
            role: l.role === "bus" ? "wire" : l.role || "wire",
          })),
          tol,
          merge_tol: mergeTol(tol),
        }),
      });
      const results = res.results || {};
      let filled = 0;
      let kept = 0;
      for (const b of bboxes) {
        if (b.terminals && b.terminals.length) {
          kept += 1; // ZACHOWAJ reczne GT — auto tylko uzupelnia puste, nigdy nie kasuje
          continue;
        }
        b.terminals = (results[b.id] || []).map((t) => ({
          id: t.id,
          x: t.x,
          y: t.y,
          name: "",
        }));
        if (b.terminals.length) filled += 1;
      }
      pageTerminalsDerived = true;
      markPageDirty();
      saveStatusEl.textContent =
        `Auto-zaciski: dodano ${filled} bbox, zachowano ${kept} z recznymi (nic nie nadpisano)`;
      return true;
    } catch (err) {
      saveStatusEl.textContent = "Błąd auto-zacisków: " + err.message;
      return false;
    }
  }

  function buildBboxReviewQueue() {
    return bboxes
      .map((b, idx) => ({ kind: "bbox", idx, b }))
      .filter((item) => item.b.id.startsWith("auto_") || item.b.id.startsWith("sym_") || !(item.b.tag || "").trim());
  }

  function buildConnectionReviewQueue() {
    const out = [];
    connections.forEach((conn, ci) => {
      const fromR = resolveBboxForRef(conn.from || conn.from_ref);
      const toR = resolveBboxForRef(conn.to);
      if (!fromR || !toR) return;
      const crop = unionRect(bboxCropRect(fromR.b), bboxCropRect(toR.b));
      out.push({
        kind: "connection",
        connIdx: ci,
        conn,
        fromIdx: fromR.idx,
        toIdx: toR.idx,
        crop,
      });
    });
    return out;
  }

  function showReviewItem(item) {
    if (!item) return;
    if (item.kind === "terminal" || item.kind === "bbox") {
      selectedIdx = item.idx;
      setCropRect(bboxCropRect(item.b || bboxes[item.idx]));
      const b = bboxes[selectedIdx];
      saveStatusEl.textContent = `Review ${reviewQueueIdx + 1}/${reviewQueue.length}: #${b?.seq || ""} ${(b?.tag || "").trim()}`;
    } else if (item.kind === "connection") {
      selectedIdx = item.fromIdx;
      setCropRect(item.crop);
      const c = item.conn;
      saveStatusEl.textContent = `Połączenie ${reviewQueueIdx + 1}/${reviewQueue.length}: ${c.from || c.from_ref} → ${c.to}`;
    }
    if (typeof renderTerminalList === "function") renderTerminalList();
    if (typeof renderAnnotationList === "function") renderAnnotationList();
    if (typeof window.renderReviewBboxType === "function") window.renderReviewBboxType();
    if (typeof window._cropRedraw === "function") window._cropRedraw();
  }

  function startReviewQueue(kind) {
    reviewKind = kind;
    reviewQueueIdx = 0;
    if (kind === "terminal") {
      reviewQueue = bboxes.map((b, idx) => ({ kind: "terminal", idx, b }));
    } else if (kind === "bbox") {
      reviewQueue = buildBboxReviewQueue();
      if (!reviewQueue.length) {
        reviewQueue = bboxes.map((b, idx) => ({ kind: "bbox", idx, b }));
      }
    } else if (kind === "connection") {
      reviewQueue = buildConnectionReviewQueue();
    } else {
      reviewQueue = [];
    }
    if (!reviewQueue.length) {
      saveStatusEl.textContent = "Brak elementów w kolejce review";
      return false;
    }
    showReviewItem(reviewQueue[0]);
    return true;
  }

  function reviewStep(dir) {
    if (!reviewQueue.length) return;
    reviewQueueIdx = (reviewQueueIdx + dir + reviewQueue.length) % reviewQueue.length;
    showReviewItem(reviewQueue[reviewQueueIdx]);
  }

  function drawCropOverlay() {
    withCropCtx((cropped) => {
      if (!cropped) return;
      const item = reviewQueue[reviewQueueIdx];
      if (mode === MODE_TERMINAL || (item && item.kind === "terminal")) {
        const b = bboxes[selectedIdx];
        if (b) {
          drawBboxOnCanvas(b, selectedIdx);
          drawTerminalsForBbox(b, selectedIdx);
        }
      } else if (mode === MODE_REVIEW_BBOX) {
        const b = bboxes[selectedIdx];
        if (b) drawBboxOnCanvas(b, selectedIdx);
      } else if (mode === MODE_CONNECTION) {
        const item = reviewQueue[reviewQueueIdx];
        if (item && item.kind === "connection") {
          drawBboxOnCanvas(bboxes[item.fromIdx], item.fromIdx);
          drawBboxOnCanvas(bboxes[item.toIdx], item.toIdx);
          drawConnectionLinesInCrop(item);
        }
      }
    });
  }

  function drawTerminalsForBbox(b, idx) {
    const ts = b.terminals || [];
    if (!ts.length) return;
    const sel = idx === selectedIdx;
    const r = TERMINAL_R / scale;
    for (const t of ts) {
      const ax = b.x + t.x * b.width;
      const ay = b.y + t.y * b.height;
      ctx.beginPath();
      ctx.arc(ax, ay, r + 2 / scale, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(ax, ay, r, 0, Math.PI * 2);
      ctx.fillStyle = sel ? "#fa5252" : "#f76707";
      ctx.fill();
      ctx.lineWidth = 2 / scale;
      ctx.strokeStyle = "#1a1a1a";
      ctx.stroke();
      const label = (t.name || t.id || "").toString();
      if (label) {
        ctx.font = `bold ${14 / scale}px sans-serif`;
        const tx = ax + (r + 4 / scale);
        const ty = ay - (r + 2 / scale);
        ctx.lineWidth = 3 / scale;
        ctx.strokeStyle = "#ffffff";
        ctx.strokeText(label, tx, ty);
        ctx.fillStyle = "#1a1a1a";
        ctx.fillText(label, tx, ty);
      }
    }
  }

  function drawConnectionLinesInCrop(item) {
    if (!cropRect) return;
    const { x1, y1, x2, y2 } = cropRect;
    ctx.strokeStyle = "#111";
    ctx.lineWidth = 4 / scale;
    ctx.lineCap = "round";
    for (const ln of lines) {
      if (ln.role !== "wire" && ln.role !== "bus") continue;
      const pts = ln.points || [];
      if (pts.length < 2) continue;
      let any = false;
      for (const p of pts) {
        if (p[0] >= x1 && p[0] <= x2 && p[1] >= y1 && p[1] <= y2) {
          any = true;
          break;
        }
      }
      if (!any) continue;
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1]);
      ctx.stroke();
    }
  }

  async function enterTerminalMode() {
    hideLinesReview = true;
    await loadTerminalCfg();
    if (!pageTerminalsDerived) await deriveTerminalsForPage();
    startReviewQueue("terminal");
  }

  async function saveTerminalPattern() {
    const b = bboxes[selectedIdx];
    if (!b || !currentPageId) {
      saveStatusEl.textContent = "Wybierz bbox i stronę (tryb terminale)";
      return;
    }
    if (!(b.terminals || []).length) {
      saveStatusEl.textContent = "Bbox bez terminali — popraw GT przed zapisem wzorca";
      return;
    }
    try {
      const res = await fetchJson("/api/save-terminal-pattern", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          page_id: currentPageId,
          bbox_id: b.id,
        }),
      });
      saveStatusEl.textContent =
        `Wzorzec ${res.class_name}: ${res.sample_count} bbox → ${(res.pattern?.expected || []).length} slotów`;
    } catch (err) {
      saveStatusEl.textContent = "Zapis wzorca: " + err.message;
    }
  }

  function exitCropModes() {
    clearCropRect();
    reviewQueue = [];
    reviewKind = null;
    hideLinesReview = false;
  }

  function acceptReviewItem() {
    if (mode === MODE_REVIEW_BBOX && reviewQueue[reviewQueueIdx]) {
      const b = bboxes[reviewQueue[reviewQueueIdx].idx];
      if (b && b.id.startsWith("auto_")) b.id = b.id.replace(/^auto_/, "ok_");
    }
    markPageDirty();
    reviewStep(1);
  }

  function rejectReviewItem() {
    const item = reviewQueue[reviewQueueIdx];
    if (!item) return;
    if (mode === MODE_REVIEW_BBOX) {
      bboxes.splice(item.idx, 1);
      reviewQueue = buildBboxReviewQueue();
      if (!reviewQueue.length) reviewQueue = bboxes.map((b, idx) => ({ kind: "bbox", idx, b }));
    } else if (mode === MODE_CONNECTION) {
      connections.splice(item.connIdx, 1);
      reviewQueue = buildConnectionReviewQueue();
    }
    markPageDirty();
    if (typeof renderConnectionList === "function") renderConnectionList();
    if (!reviewQueue.length) {
      saveStatusEl.textContent = "Kolejka review pusta";
      return;
    }
    reviewQueueIdx = Math.min(reviewQueueIdx, reviewQueue.length - 1);
    showReviewItem(reviewQueue[reviewQueueIdx]);
  }

  async function importRuntimeDraft() {
    if (!currentPageId) return;
    try {
      const res = await fetchJson(
        `/api/import-runtime-draft/${encodeURIComponent(currentPageId)}?force=true`,
        { method: "POST" }
      );
      await selectPage(currentPageId);
      saveStatusEl.textContent =
        `Draft: ${res.bbox_count} bbox, ${res.line_count} linii, ${res.connection_count} conn`;
    } catch (err) {
      saveStatusEl.textContent = "Import draft: " + err.message;
    }
  }

  function imagePointFromCanvas(cx, cy) {
    // Klik w canvasie -> wsp. obrazu, z uwzglednieniem aktywnego cropu.
    if (!cropRect) return { x: cx, y: cy };
    const sw = cropRect.x2 - cropRect.x1;
    const sh = cropRect.y2 - cropRect.y1;
    return {
      x: cropRect.x1 + (cx * sw) / canvas.width,
      y: cropRect.y1 + (cy * sh) / canvas.height,
    };
  }

  function cropPxPerImage() {
    // ile px canvasu przypada na 1 px obrazu (do progu trafienia w terminal)
    if (!cropRect) return 1;
    const sw = cropRect.x2 - cropRect.x1;
    return sw > 0 ? canvas.width / sw : 1;
  }

  window.CropReview = {
    isCropActive,
    imagePointFromCanvas,
    cropPxPerImage,
    drawCropOverlay,
    enterTerminalMode,
    exitCropModes,
    deriveTerminalsForPage,
    saveTerminalPattern,
    loadTerminalCfg,
    startReviewQueue,
    reviewStep,
    acceptReviewItem,
    rejectReviewItem,
    importRuntimeDraft,
    onPageChange() {
      pageTerminalsDerived = false;
      terminalCfg = null;
      exitCropModes();
    },
  };
})();
