(() => {
  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function waitForElement(selector, callback, opts) {
    opts = opts || {};
    const maxWait = opts.maxWait || 30000; // 30 seconds
    const checkInterval = opts.checkInterval || 200; // Check every 200ms
    const startTime = Date.now();

    console.log(`Waiting for element: ${selector}`);

    const check = () => {
      const element = document.querySelector(selector);
      if (element) {
        console.log(`Element found: ${selector}`);
        callback(element);
        return true;
      }
      
      if (Date.now() - startTime > maxWait) {
        console.warn(`Timeout waiting for element: ${selector}`);
        return true;
      }
      
      return false;
    };

    // Check immediately
    if (check()) return;

    // Then poll regularly
    const intervalId = setInterval(() => {
      if (check()) {
        clearInterval(intervalId);
      }
    }, checkInterval);
  }

  function pollUntil(fn, opts) {
    opts = opts || {};
    const everyMs = opts.everyMs || 100;
    const maxTries = opts.maxTries || 250; // ~25s
    let tries = 0;
    const t = setInterval(() => {
      tries++;
      try {
        if (fn()) clearInterval(t);
        else if (tries >= maxTries) {
          console.warn("pollUntil: Max tries reached");
          clearInterval(t);
        }
      } catch (e) {
        clearInterval(t);
        // eslint-disable-next-line no-console
        console.error(e);
      }
    }, everyMs);
  }

  function initRrweb() {
    if (window.__rrweb_demo_inited) return true;

    const statusEl = document.querySelector(".rrweb-status");
    const startBtn = document.querySelector(".rrweb-start");
    const stopBtn = document.querySelector(".rrweb-stop");
    if (!statusEl || !startBtn || !stopBtn) {
      return false; // DOM not ready yet
    }

    const setStatus = (txt) => {
      statusEl.textContent = txt;
    };

    if (!window.rrweb || typeof window.rrweb.record !== "function") {
      console.log("rrweb: library not loaded yet, waiting...");
      setStatus("rrweb loading…");
      return false; // wait for rrweb script
    }

    console.log("rrweb: Initializing...");

    let stopFn = null;
    let events = [];

    const nowIso = () => new Date().toISOString().replace(/[:.]/g, "-");

    const downloadEvents = () => {
      const payload = {
        created_at: new Date().toISOString(),
        user_agent: navigator.userAgent,
        url: location.href,
        rrweb_events: events,
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rrweb-recording-${nowIso()}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 250);
    };

    const startRecording = () => {
      if (stopFn) return;
      events = [];
      setStatus("recording…");
      console.log("rrweb: Recording started");
      stopFn = window.rrweb.record({
        emit: (event) => {
          events.push(event);
          if (events.length % 50 === 0) {
            console.log(`rrweb: ${events.length} events captured`);
          }
        },
      });
    };

    const stopRecording = () => {
      if (!stopFn) return;
      stopFn();
      stopFn = null;
      setStatus(`stopped (${events.length} events)`);
      console.log(`rrweb: Recording stopped. Total events: ${events.length}`);
      downloadEvents();
    };

    // For debugging in devtools console:
    // window.__rrweb_demo.getEvents()
    window.__rrweb_demo = { start: startRecording, stop: stopRecording, getEvents: () => events };

    startBtn.addEventListener("click", startRecording);
    stopBtn.addEventListener("click", stopRecording);

    window.__rrweb_demo_inited = true;
    console.log("rrweb: Initialization complete. Auto-starting in 300ms...");
    setTimeout(startRecording, 300); // auto-start
    return true;
  }

  function initPanzoom() {
    if (window.__panzoom_demo_inited) return true;

    const viewer = document.querySelector(".demo-viewer");
    if (!viewer) {
      return false;
    }

    const svg = viewer.querySelector("svg");
    if (!svg) {
      console.log("panzoom: SVG element not found in viewer, waiting...");
      return false;
    }

    if (typeof window.Panzoom !== "function") {
      console.log("panzoom: library not loaded yet, waiting...");
      return false; // wait for panzoom script
    }

    console.log("panzoom: Initializing...");

    svg.style.width = "100%";
    svg.style.height = "100%";
    svg.style.cursor = "grab";
    svg.style.transformOrigin = "0 0";

    const panzoom = window.Panzoom(svg, {
      maxScale: 12,
      minScale: 0.5,
      contain: "outside",
      startScale: 1,
      startX: 0,
      startY: 0,
    });

    // Wheel zoom with preventDefault to stop page scroll
    viewer.addEventListener("wheel", (e) => {
      e.preventDefault();
      panzoom.zoomWithWheel(e);
    }, { passive: false });
    
    viewer.addEventListener("dblclick", () => {
      console.log("panzoom: Reset view");
      panzoom.reset();
    });
    svg.addEventListener("mousedown", () => {
      svg.style.cursor = "grabbing";
    });
    window.addEventListener("mouseup", () => {
      svg.style.cursor = "grab";
    });

    // Update zoom indicator
    const zoomIndicator = document.querySelector(".zoom-indicator");
    if (zoomIndicator) {
      panzoom.on("zoom", (e) => {
        const scale = e.detail.scale || 1;
        zoomIndicator.textContent = `${Math.round(scale * 100)}%`;
      });
      panzoom.on("pan", () => {
        console.log("panzoom: Panning...");
      });
    }

    window.__demo_panzoom = panzoom;
    window.__panzoom_demo_inited = true;
    console.log("panzoom: Initialization complete");
    return true;
  }

  ready(() => {
    // Give Panel/Bokeh time to render
    setTimeout(() => {
      // Wait for rrweb controls to appear, then initialize
      waitForElement(".rrweb-status", () => {
        pollUntil(initRrweb, { everyMs: 100, maxTries: 150 });
      }, { checkInterval: 200 });

      // Wait for viewer element to appear, then initialize panzoom
      waitForElement(".demo-viewer", () => {
        pollUntil(initPanzoom, { everyMs: 100, maxTries: 150 });
      }, { checkInterval: 200 });
    }, 800);
  });
})();

