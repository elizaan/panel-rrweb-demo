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
        # Runs after load; initializes rrweb + pan/zoom (served by panel under /assets)
        "demo": "/assets/demo.js",
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
    """,
    margin=(0, 0, 10, 0),
)


svg_text = DEMO_SVG_PATH.read_text(encoding="utf-8")
if svg_text.lstrip().startswith("<?xml"):
    svg_text = "\n".join(svg_text.splitlines()[1:])
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
