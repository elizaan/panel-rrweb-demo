from __future__ import annotations

from pathlib import Path

import panel as pn


ASSETS_DIR = Path(__file__).parent / "assets"
DEMO_SVG_PATH = ASSETS_DIR / "demo.svg"

pn.extension(
    sizing_mode="stretch_width",
    js_files={
        # rrweb guide: https://github.com/rrweb-io/rrweb/blob/master/guide.md
        "rrweb": "https://unpkg.com/rrweb@latest/dist/rrweb.min.js",
        # Panzoom: https://github.com/timmywil/panzoom
        "panzoom": "https://unpkg.com/@panzoom/panzoom@4.6.1/dist/panzoom.min.js",
    },
    raw_css=[
        """
        .demo-card {
          border: 1px solid rgba(15, 23, 42, 0.12);
          border-radius: 12px;
          padding: 12px;
          background: white;
        }
        .rrweb-controls button {
          border: 1px solid rgba(15, 23, 42, 0.18);
          border-radius: 10px;
          padding: 8px 10px;
          background: rgba(15, 23, 42, 0.04);
          cursor: pointer;
        }
        .rrweb-controls button:hover { background: rgba(15, 23, 42, 0.07); }
        .rrweb-pill {
          font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
          font-size: 13px;
          border-radius: 999px;
          padding: 4px 10px;
          border: 1px solid rgba(15, 23, 42, 0.14);
          background: rgba(15, 23, 42, 0.04);
          user-select: none;
        }
        """,
    ],
)


title = pn.pane.Markdown(
    "## Simple Panel dashboard (image + Yes/No) + rrweb recording",
    margin=(0, 0, 8, 0),
)


rrweb_controls = pn.pane.HTML(
    """
    <div class="demo-card rrweb-controls" style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
      <strong style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
        rrweb recording
      </strong>
      <button id="rrweb-start" type="button">Start recording</button>
      <button id="rrweb-stop" type="button">Stop &amp; download (.json)</button>
      <span id="rrweb-status" class="rrweb-pill">idle</span>
      <span style="opacity:0.75; font-size:13px; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
        (auto-starts after load)
      </span>
    </div>

    <script>
    (function () {
      function $(id) { return document.getElementById(id); }
      function nowIso() { return new Date().toISOString().replace(/[:.]/g, "-"); }

      function init() {
        var statusEl = $("rrweb-status");
        var startBtn = $("rrweb-start");
        var stopBtn = $("rrweb-stop");
        if (!statusEl || !startBtn || !stopBtn) return;

        var stopFn = null;
        var events = [];

        function setStatus(txt) { statusEl.textContent = txt; }

        function downloadEvents() {
          var payload = {
            created_at: new Date().toISOString(),
            user_agent: navigator.userAgent,
            url: location.href,
            rrweb_events: events
          };
          var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
          var url = URL.createObjectURL(blob);
          var a = document.createElement("a");
          a.href = url;
          a.download = "rrweb-recording-" + nowIso() + ".json";
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(function () { URL.revokeObjectURL(url); }, 250);
        }

        function startRecording() {
          if (!window.rrweb || !window.rrweb.record) {
            setStatus("rrweb not loaded");
            return;
          }
          if (stopFn) return;
          events = [];
          setStatus("recording…");
          stopFn = window.rrweb.record({
            emit: function (event) { events.push(event); }
          });
        }

        function stopRecording() {
          if (!stopFn) return;
          stopFn();
          stopFn = null;
          setStatus("stopped (" + events.length + " events)");
          downloadEvents();
        }

        // Expose for debugging in console
        window.__rrweb_demo = {
          start: startRecording,
          stop: stopRecording,
          getEvents: function () { return events; }
        };

        startBtn.addEventListener("click", startRecording);
        stopBtn.addEventListener("click", stopRecording);

        setTimeout(startRecording, 600);
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
      } else {
        init();
      }
    })();
    </script>
    """,
    margin=(0, 0, 10, 0),
)


svg_text = DEMO_SVG_PATH.read_text(encoding="utf-8")
image_viewer = pn.pane.HTML(
    f"""
    <div class="demo-card">
      <div style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
                  font-weight:600; margin-bottom:8px;">
        Image viewer (pan + zoom)
      </div>
      <div id="demo-viewer"
           style="width:100%; height:520px; overflow:hidden; border-radius:10px;
                  border: 1px solid rgba(15, 23, 42, 0.12); background: rgba(15, 23, 42, 0.02);
                  touch-action:none;">
        {svg_text}
      </div>
      <div style="margin-top:8px; opacity:0.75; font-size:13px;
                  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
        Wheel = zoom, drag = pan, double-click = reset
      </div>
    </div>

    <script>
    (function () {{
      function init() {{
        var viewer = document.getElementById("demo-viewer");
        if (!viewer) return;
        var svg = viewer.querySelector("svg");
        if (!svg || !window.Panzoom) return;

        // Make sure the inline SVG is "transformable"
        svg.style.width = "100%";
        svg.style.height = "100%";
        svg.style.cursor = "grab";
        svg.style.transformOrigin = "0 0";

        var panzoom = window.Panzoom(svg, {{
          maxScale: 12,
          minScale: 0.5,
          contain: "outside"
        }});

        viewer.addEventListener("wheel", panzoom.zoomWithWheel);
        viewer.addEventListener("dblclick", function () {{ panzoom.reset(); }});
        svg.addEventListener("mousedown", function () {{ svg.style.cursor = "grabbing"; }});
        window.addEventListener("mouseup", function () {{ svg.style.cursor = "grab"; }});

        window.__demo_panzoom = panzoom;
      }}

      if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", init);
      }} else {{
        init();
      }}
    }})();
    </script>
    """,
    sizing_mode="stretch_width",
    margin=0,
)


yes_btn = pn.widgets.Button(name="Yes", button_type="success", width=120)
no_btn = pn.widgets.Button(name="No", button_type="danger", width=120)
decision = pn.pane.Markdown("**Decision**: _none yet_", margin=(10, 0, 0, 0))


def _set_decision(value: str) -> None:
    decision.object = f"**Decision**: `{value}`"


yes_btn.on_click(lambda *_: _set_decision("yes"))
no_btn.on_click(lambda *_: _set_decision("no"))

controls = pn.Column(
    pn.pane.Markdown("### Simple Yes/No buttons", margin=(0, 0, 8, 0)),
    pn.Row(yes_btn, no_btn),
    decision,
    pn.layout.Spacer(height=8),
    pn.pane.Markdown(
        """
        **What rrweb records here**

        - Clicking **Yes/No**
        - Panning/zooming the image viewer (mouse events)
        - Any scrolling / typing / focus changes in the page
        """,
        margin=0,
    ),
    css_classes=["demo-card"],
    width=360,
)


app = pn.Column(
    title,
    rrweb_controls,
    pn.Row(image_viewer, controls, sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

app.servable()
