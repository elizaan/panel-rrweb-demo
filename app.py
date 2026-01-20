import io
import urllib.request

import numpy as np
import panel as pn
from bokeh.models import WheelZoomTool, PanTool, ResetTool, BoxZoomTool
from bokeh.plotting import figure
from PIL import Image

# Load Panel and rrweb from CDN
pn.extension(
    js_files={"rrweb": "https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"},
    css_files=["https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.css"],
)


IMAGE_URL = "https://assets.holoviz.org/panel/tutorials/wind_turbine.png"

# --- Load image from URL ---
with urllib.request.urlopen(IMAGE_URL) as resp:
    data = resp.read()

img = Image.open(io.BytesIO(data)).convert("RGBA")
arr = np.asarray(img)
h, w = arr.shape[:2]

rgba = np.flipud(arr).view(dtype=np.uint32).reshape((h, w))

# --- Bokeh figure ---
wheel_zoom = WheelZoomTool()
pan = PanTool()
box_zoom = BoxZoomTool()
reset = ResetTool()

p = figure(
    title="Panel + Bokeh Image Viewer",
    x_range=(0, w),
    y_range=(0, h),
    width=900,
    height=650,
    match_aspect=True,
    toolbar_location="above",
    tools="",
)
p.image_rgba(image=[rgba], x=0, y=0, dw=w, dh=h)
p.add_tools(wheel_zoom, pan, box_zoom, reset)
p.toolbar.active_scroll = wheel_zoom
p.toolbar.active_drag = pan
p.xaxis.visible = False
p.yaxis.visible = False
p.grid.visible = False

plot = pn.pane.Bokeh(p, sizing_mode="stretch_both")

# --- UI widgets ---
start_btn = pn.widgets.Button(name="Start recording", button_type="success")
stop_btn = pn.widgets.Button(name="Stop + download JSON", button_type="danger", disabled=True)
replay_btn = pn.widgets.Button(name="Replay", button_type="primary", disabled=True)
clear_btn = pn.widgets.Button(name="Clear", button_type="default", disabled=True)

events_json = pn.widgets.TextAreaInput(
    name="Recorded events (JSON)",
    placeholder="Click Start recording, interact (zoom/pan), then Stop.",
    height=180,
    sizing_mode="stretch_width",
)

status = pn.pane.Markdown("**Status:** idle", sizing_mode="stretch_width")

replay_container = pn.pane.HTML(
    """
    <div data-rrweb-replay="1"
         style="height:420px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
      <div style="padding:10px; opacity:0.7;">No replay yet.</div>
    </div>
    """,
    sizing_mode="stretch_width",
)



# --- JS callbacks (Panel expects JS strings) ---
start_btn.js_on_click(
    args={
        "stop_btn": stop_btn,
        "replay_btn": replay_btn,
        "clear_btn": clear_btn,
        "start_btn": start_btn,
        "status": status,
    },
    code="""
    console.log("[rrweb-demo] Start clicked");

    if (!window.rrweb || typeof rrweb.record !== "function") {
      status.object = "**Status:** rrweb not loaded (check Network/Console)";
      alert("rrweb not loaded. Check Network + Console.");
      return;
    }

    window.__rrweb_state = window.__rrweb_state || { stopFn: null, events: [] };

    if (window.__rrweb_state.stopFn) {
      status.object = "**Status:** already recording";
      return;
    }

    window.__rrweb_state.events = [];
    window.__rrweb_state.stopFn = rrweb.record({
      emit(event) {
        window.__rrweb_state.events.push(event);
      }
    });

    status.object = "**Status:** 🔴 recording... (zoom/pan now)";
    start_btn.name = "Recording…";
    start_btn.button_type = "warning";

    stop_btn.disabled = false;
    replay_btn.disabled = true;
    clear_btn.disabled = true;

    console.log("[rrweb-demo] Recording started");
    """
)

stop_btn.js_on_click(
    args={
        "events_json": events_json,
        "stop_btn": stop_btn,
        "replay_btn": replay_btn,
        "clear_btn": clear_btn,
        "start_btn": start_btn,
        "status": status,
        "replay_container": replay_container,
    },
    code="""
    console.log("[rrweb-demo] Stop clicked");

    if (!window.__rrweb_state || !window.__rrweb_state.stopFn) {
      status.object = "**Status:** not recording";
      return;
    }

    window.__rrweb_state.stopFn();
    window.__rrweb_state.stopFn = null;

    const events = window.__rrweb_state.events || [];
    const json = JSON.stringify(events);

    events_json.value = json;

    // download JSON
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rrweb-session.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    status.object = `**Status:** stopped (events: ${events.length}) ✅`;
    start_btn.name = "Start recording";
    start_btn.button_type = "success";

    stop_btn.disabled = true;
    replay_btn.disabled = (events.length === 0);
    clear_btn.disabled = (events.length === 0);

    replay_container.object = `
        <div data-rrweb-replay="1"
            style="height:420px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="padding:10px; opacity:0.7;">Ready to replay. Click "Replay".</div>
        </div>
    `;


    console.log("[rrweb-demo] Stopped. Events:", events.length);
    """
)


replay_btn.js_on_click(
    args={"events_json": events_json, "status": status, "replay_container": replay_container},
    code="""
    console.log("[rrweb-demo] Replay clicked");

    if (!window.rrweb || typeof rrweb.Replayer !== "function") {
      status.object = "**Status:** rrweb replayer not available (check Console/Network)";
      console.error("[rrweb-demo] rrweb or Replayer missing", window.rrweb);
      return;
    }

    let events = [];
    try {
      events = JSON.parse(events_json.value || "[]");
    } catch (e) {
      status.object = "**Status:** JSON parse error";
      console.error(e);
      return;
    }

    if (!events.length) {
      status.object = "**Status:** no events to replay";
      return;
    }

    // Replace the container with a fresh empty root
    replay_container.object = `
      <div data-rrweb-replay="1"
           style="height:420px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
        <div data-rrweb-root="1" style="height:100%;"></div>
      </div>
    `;

    // Wait for Panel to render the updated HTML, then locate within the document
    setTimeout(() => {
      const outer = document.querySelector('[data-rrweb-replay="1"]');
      const root = outer ? outer.querySelector('[data-rrweb-root="1"]') : null;

      console.log("[rrweb-demo] replay outer:", outer);
      console.log("[rrweb-demo] replay root:", root);

      if (!root) {
        status.object = "**Status:** replay root not found (check Console)";
        return;
      }

      status.object = `**Status:** replaying (events: ${events.length}) ▶️`;

      // Stop any previous replayer
      if (window.__rrweb_replayer) {
        try { window.__rrweb_replayer.pause(); } catch(e) {}
        window.__rrweb_replayer = null;
      }

      const replayer = new rrweb.Replayer(events, { root });
      window.__rrweb_replayer = replayer;
      replayer.play();
    }, 200);
    """
)



clear_btn.js_on_click(
    args={"events_json": events_json, "replay_btn": replay_btn, "clear_btn": clear_btn, "status": status, "replay_container": replay_container},
    code="""
    events_json.value = "";
    replay_btn.disabled = true;
    clear_btn.disabled = true;

    if (window.__rrweb_state) {
      window.__rrweb_state.events = [];
      window.__rrweb_state.stopFn = null;
    }

    status.object = "**Status:** cleared";
    replay_container.object = `
      <div style="height:420px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
        <div style="padding:10px; opacity:0.7;">No replay yet.</div>
      </div>
    `;
    """
)


controls = pn.Row(start_btn, stop_btn, replay_btn, clear_btn, sizing_mode="stretch_width")

pn.template.FastListTemplate(
    title="Panel + Bokeh + rrweb (minimal demo)",
    main=[
        controls,
        status,
        replay_container,
        plot,
        events_json,
    ],
).servable()

