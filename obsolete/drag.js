// Optimiertes Dragging für .chart-controls
// Features: Pointer API (Maus/Touch/Stift), robust gegen transformierte Eltern,
// Begrenzung auf Viewport, Persistenz (localStorage), keyboard support, comments.

// test:
console.log("drag.js wurde geladen!");

// Wait-for-panel helper (versucht sofort und bei DOMContentLoaded)
function waitForPanel() {
  const panel = document.querySelector(".chart-controls");
  if (panel) {
    console.log("Panel gefunden – starte erweitertes Drag-System");
    if (typeof window.__startAdvancedDragSystem === "function") {
      window.__startAdvancedDragSystem(panel);
    } else {
      console.warn("Advanced Drag System nicht verfügbar.");
    }
    return;
  }
  // Wenn noch nicht da, erneut versuchen
  console.log("Panel noch nicht da...");
  setTimeout(waitForPanel, 200);
}

document.addEventListener("DOMContentLoaded", waitForPanel);
waitForPanel(); // sofortiger Versuch, falls Script nach DOMContentLoaded geladen wurde

// Großes IIFE, jetzt als startbare Funktion exportiert
(function () {
  "use strict";

  // Exportierte Startfunktion — wird mit dem bereits vorhandenen panel aufgerufen
  window.__startAdvancedDragSystem = function(panel) {
    console.log("Advanced Drag System gestartet für:", panel);

    const STORAGE_KEY = "chartControlsPosition_v1";

    // Ensure panel is positioned absolutely so left/top wirken
    const cs = getComputedStyle(panel);
    if (cs.position !== "absolute" && cs.position !== "fixed") {
      panel.style.position = "absolute";
    }

    // Load saved position if present
    const saved = loadPosition();
    if (saved) {
      applyPosition(panel, saved.left, saved.top);
    } else {
      // Ensure panel has numeric left/top if not set
      if (!panel.style.left) panel.style.left = (panel.getBoundingClientRect().left + window.scrollX) + "px";
      if (!panel.style.top) panel.style.top = (panel.getBoundingClientRect().top + window.scrollY) + "px";
    }

    // State for dragging
    let dragging = false;
    let startX = 0, startY = 0, startLeft = 0, startTop = 0;
    let activePointerId = null;

    // Start drag: record start positions
    function startDrag(clientX, clientY, pointerId) {
      dragging = true;
      activePointerId = pointerId == null ? null : pointerId;
      const rect = panel.getBoundingClientRect();
      startX = clientX;
      startY = clientY;
      startLeft = rect.left + window.scrollX;
      startTop = rect.top + window.scrollY;
      document.body.style.userSelect = "none";
      panel.style.cursor = "grabbing";
      panel.classList.add("dragging");
    }

    // Move drag: compute new left/top and clamp to viewport
    function moveDrag(clientX, clientY) {
      if (!dragging) return;
      const dx = clientX - startX;
      const dy = clientY - startY;
      const newLeft = startLeft + dx;
      const newTop = startTop + dy;

      const clamped = clampToViewport(panel, newLeft, newTop);
      applyPosition(panel, clamped.left, clamped.top);
    }

    // End drag: persist and cleanup
    function endDrag(pointerId) {
      if (pointerId != null && activePointerId != null && pointerId !== activePointerId) return;
      dragging = false;
      activePointerId = null;
      document.body.style.userSelect = "";
      panel.style.cursor = "grab";
      panel.classList.remove("dragging");
      savePosition(panel);
    }

    // Pointer event handlers
    panel.addEventListener("pointerdown", (e) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      startDrag(e.clientX, e.clientY, e.pointerId);
      try { panel.setPointerCapture(e.pointerId); } catch (err) {}
      e.preventDefault();
    });

    document.addEventListener("pointermove", (e) => {
      moveDrag(e.clientX, e.clientY);
    }, { passive: true });

    document.addEventListener("pointerup", (e) => {
      endDrag(e.pointerId);
      try { panel.releasePointerCapture(e.pointerId); } catch (err) {}
    });

    document.addEventListener("pointercancel", (e) => {
      endDrag(e.pointerId);
    });

    // Keyboard accessibility: move with arrow keys, save with Enter/Escape
    panel.setAttribute("tabindex", panel.getAttribute("tabindex") || "0");
    panel.style.cursor = "grab";
    panel.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 20 : 8;
      let changed = false;
      let left = parseFloat(getComputedStyle(panel).left) || 0;
      let top = parseFloat(getComputedStyle(panel).top) || 0;

      switch (e.key) {
        case "ArrowLeft": left -= step; changed = true; break;
        case "ArrowRight": left += step; changed = true; break;
        case "ArrowUp": top -= step; changed = true; break;
        case "ArrowDown": top += step; changed = true; break;
        case "Home": left = 0; top = 0; changed = true; break;
        case "End": left = window.innerWidth - panel.offsetWidth; top = window.innerHeight - panel.offsetHeight; changed = true; break;
        case "Enter": savePosition(panel); break;
        case "Escape":
          const s = loadPosition();
          if (s) applyPosition(panel, s.left, s.top);
          break;
        default: break;
      }

      if (changed) {
        const clamped = clampToViewport(panel, left, top);
        applyPosition(panel, clamped.left, clamped.top);
        e.preventDefault();
      }
    });

    // Double click to reset to saved or default position
    panel.addEventListener("dblclick", () => {
      const s = loadPosition();
      if (s) applyPosition(panel, s.left, s.top);
      else applyPosition(panel, 20, 20);
    });

    // Helper: apply left/top to element
    function applyPosition(el, left, top) {
      el.style.left = Math.round(left) + "px";
      el.style.top = Math.round(top) + "px";
    }

    // Helper: clamp coordinates so panel stays fully in viewport
    function clampToViewport(el, left, top) {
      const w = el.offsetWidth;
      const h = el.offsetHeight;
      const minLeft = 0;
      const minTop = 0;
      const maxLeft = Math.max(0, window.innerWidth - w);
      const maxTop = Math.max(0, window.innerHeight - h);
      return {
        left: Math.min(Math.max(minLeft, left), maxLeft),
        top: Math.min(Math.max(minTop, top), maxTop)
      };
    }

    // Persistence: save and load position
    function savePosition(el) {
      try {
        const left = parseFloat(getComputedStyle(el).left) || 0;
        const top = parseFloat(getComputedStyle(el).top) || 0;
        const payload = { left: Math.round(left), top: Math.round(top), ts: Date.now() };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      } catch (err) {
        console.warn("Speichern der Position fehlgeschlagen:", err);
      }
    }

    function loadPosition() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const obj = JSON.parse(raw);
        if (typeof obj.left === "number" && typeof obj.top === "number") {
          const clamped = clampToViewport(panel, obj.left, obj.top);
          return { left: clamped.left, top: clamped.top };
        }
      } catch (err) {
        console.warn("Laden der Position fehlgeschlagen:", err);
      }
      return null;
    }

    // Expose a small API on the element for debugging
    panel.__dragApi = {
      save: () => savePosition(panel),
      load: () => {
        const s = loadPosition();
        if (s) applyPosition(panel, s.left, s.top);
        return s;
      },
      reset: () => {
        localStorage.removeItem(STORAGE_KEY);
        applyPosition(panel, 20, 20);
      }
    };

    // Optional: keep panel inside viewport on window resize
    window.addEventListener("resize", () => {
      const left = parseFloat(getComputedStyle(panel).left) || 0;
      const top = parseFloat(getComputedStyle(panel).top) || 0;
      const clamped = clampToViewport(panel, left, top);
      applyPosition(panel, clamped.left, clamped.top);
      savePosition(panel);
    });

    // Ende der startbaren Funktion
  }; // window.__startAdvancedDragSystem
})(); // IIFE Ende
