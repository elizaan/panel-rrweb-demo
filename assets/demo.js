(() => {
  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
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
        else if (tries >= maxTries) clearInterval(t);
      } catch (e) {
        clearInterval(t);
        // eslint-disable-next-line no-console
        console.error(e);
      }
    }, everyMs);
  }

  function initRrweb() {
    if (window.__rrweb_demo_inited) return true;

    const statusEl = document.getElementById("rrweb-status");
    const startBtn = document.getElementById("rrweb-start");
    const stopBtn = document.getElementById("rrweb-stop");
    if (!statusEl || !startBtn || !stopBtn) return false; // DOM not ready yet

    const setStatus = (txt) => {
      statusEl.textContent = txt;
    };

    if (!window.rrweb || typeof window.rrweb.record !== "function") {
      setStatus("rrweb loading…");
      return false; // wait for rrweb script
    }

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
      stopFn = window.rrweb.record({
        emit: (event) => events.push(event),
      });
    };

    const stopRecording = () => {
      if (!stopFn) return;
      stopFn();
      stopFn = null;
      setStatus(`stopped (${events.length} events)`);
      downloadEvents();
    };

    // For debugging in devtools console:
    // window.__rrweb_demo.getEvents()
    window.__rrweb_demo = { start: startRecording, stop: stopRecording, getEvents: () => events };

    startBtn.addEventListener("click", startRecording);
    stopBtn.addEventListener("click", stopRecording);

    window.__rrweb_demo_inited = true;
    setTimeout(startRecording, 300); // auto-start
    return true;
  }

  function initPanzoom() {
    if (window.__panzoom_demo_inited) return true;

    const viewer = document.getElementById("demo-viewer");
    if (!viewer) return false;

    const svg = viewer.querySelector("svg");
    if (!svg) return false;

    if (typeof window.Panzoom !== "function") return false; // wait for panzoom script

    svg.style.width = "100%";
    svg.style.height = "100%";
    svg.style.cursor = "grab";
    svg.style.transformOrigin = "0 0";

    const panzoom = window.Panzoom(svg, {
      maxScale: 12,
      minScale: 0.5,
      contain: "outside",
    });

    viewer.addEventListener("wheel", panzoom.zoomWithWheel);
    viewer.addEventListener("dblclick", () => panzoom.reset());
    svg.addEventListener("mousedown", () => {
      svg.style.cursor = "grabbing";
    });
    window.addEventListener("mouseup", () => {
      svg.style.cursor = "grab";
    });

    window.__demo_panzoom = panzoom;
    window.__panzoom_demo_inited = true;
    return true;
  }

  ready(() => {
    // These elements are inserted by Bokeh/Panel; polling makes this robust.
    pollUntil(initRrweb, { everyMs: 150, maxTries: 300 });
    pollUntil(initPanzoom, { everyMs: 150, maxTries: 300 });
  });
})();

