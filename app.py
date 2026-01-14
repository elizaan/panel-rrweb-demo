from __future__ import annotations

import base64
import json
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
        #demo-viewer {
          cursor: grab !important;
        }
        #demo-viewer:active {
          cursor: grabbing !important;
        }
        #demo-viewer svg {
          cursor: grab !important;
        }
        #demo-viewer svg:active {
          cursor: grabbing !important;
        }
        """,
    ],
)


title = pn.pane.Markdown(
    "## Simple Panel dashboard (image + Yes/No) + rrweb recording",
    margin=(0, 0, 8, 0),
)


# Use raw HTML string parameter which Panel should not sanitize
rrweb_controls_html = """
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
"""

rrweb_controls = pn.pane.HTML(
    rrweb_controls_html,
    margin=(0, 0, 10, 0),
    sizing_mode="stretch_width",
)


# Store SVG content
svg_text = DEMO_SVG_PATH.read_text(encoding="utf-8")
if svg_text.lstrip().startswith("<?xml"):
    svg_text = "\n".join(svg_text.splitlines()[1:])

# Use raw HTML directly
image_viewer = pn.pane.HTML(
    f"""
<div class="demo-card">
  <div style="font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
              font-weight:600; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
    <span>Image viewer (pan + zoom)</span>
    <span id="zoom-indicator" style="font-size:12px; color:#64748b; font-weight:400;">100%</span>
  </div>
  <div id="demo-viewer"
       style="width:100%; height:750px; overflow:hidden; border-radius:10px;
              border: 1px solid rgba(15, 23, 42, 0.12); background: rgba(15, 23, 42, 0.02);
              touch-action:none; user-select:none; display:flex; align-items:center; justify-content:center;">
    {svg_text}
  </div>
  <div style="margin-top:8px; opacity:0.75; font-size:13px;
              font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
    🖱️ Wheel = zoom, drag = pan, double-click = reset
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


# Load demo.js content
demo_js_content = (ASSETS_DIR / "demo.js").read_text(encoding="utf-8")

# Wrapper script to wait for Bokeh and assign IDs before demo.js runs
wrapper_script = """
(function() {
  console.log('=== Starting ID assignment ===');
  
  let attempts = 0;
  const maxAttempts = 50;
  
  function assignIds() {
    const allDivs = document.getElementsByTagName('div');
    const allSpans = document.getElementsByTagName('span');
    const allButtons = document.getElementsByTagName('button');
    
    let assigned = 0;
    
    // Find demo-viewer (div with SVG)
    for (let div of allDivs) {
      if (div.querySelector('svg') && !div.id) {
        div.id = 'demo-viewer';
        console.log('✓ Assigned id=demo-viewer');
        assigned++;
        break;
      }
    }
    
    // Find zoom indicator (span with "100%")
    for (let span of allSpans) {
      if (span.textContent.trim() === '100%' && !span.id) {
        span.id = 'zoom-indicator';
        console.log('✓ Assigned id=zoom-indicator');
        assigned++;
        break;
      }
    }
    
    // Find rrweb buttons
    for (let btn of allButtons) {
      const text = btn.textContent.trim();
      if (text === 'Start recording' && !btn.id) {
        btn.id = 'rrweb-start';
        console.log('✓ Assigned id=rrweb-start');
        assigned++;
      } else if (text.includes('Stop') && !btn.id) {
        btn.id = 'rrweb-stop';
        console.log('✓ Assigned id=rrweb-stop');
        assigned++;
      }
    }
    
    // Find status pill
    const pill = document.querySelector('.rrweb-pill');
    if (pill && !pill.id) {
      pill.id = 'rrweb-status';
      console.log('✓ Assigned id=rrweb-status');
      assigned++;
    }
    
    return assigned >= 5;
  }
  
  function checkAndAssign() {
    const svgCount = document.getElementsByTagName('svg').length;
    const btnCount = document.getElementsByTagName('button').length;
    
    if (attempts % 10 === 0) {
      console.log('Check ' + attempts + ' - SVG: ' + svgCount + ' Buttons: ' + btnCount);
    }
    
    if (svgCount > 0 && btnCount >= 2) {
      console.log('✓ Content found! Assigning IDs...');
      if (assignIds()) {
        clearInterval(pollInterval);
        console.log('✓✓✓ All IDs assigned successfully!');
        return true;
      }
    }
    
    attempts++;
    if (attempts >= maxAttempts) {
      console.error('Timeout: Could not find all elements after ' + maxAttempts + ' attempts');
      clearInterval(pollInterval);
      return false;
    }
    
    return false;
  }
  
  const pollInterval = setInterval(checkAndAssign, 100);
})();
"""

# Build script using string concatenation to avoid f-string brace conflicts
demo_script = pn.pane.HTML(
    "<script type=\"text/javascript\">\n" + wrapper_script + "\n" + demo_js_content + "\n</script>",
    sizing_mode="fixed",
    width=0,
    height=0,
)

app = pn.Column(
    title,
    rrweb_controls,
    pn.Row(image_viewer, controls, sizing_mode="stretch_width"),
    demo_script,
    sizing_mode="stretch_width",
)

app.servable()
