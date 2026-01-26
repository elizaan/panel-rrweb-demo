import io
import json
import logging
import urllib.request

import numpy as np
import panel as pn
from bokeh.models import WheelZoomTool, PanTool, ResetTool, BoxZoomTool
from bokeh.plotting import figure
from PIL import Image

# Enhanced WebSocket logging with code explanations
class WebSocketLogFilter(logging.Filter):
    """Add context and explanations to WebSocket log messages"""
    
    # WebSocket close codes (RFC 6455)
    CLOSE_CODES = {
        1000: "Normal Closure - Connection completed successfully",
        1001: "Going Away - Browser tab closed or navigated away",
        1002: "Protocol Error - WebSocket protocol violation",
        1003: "Unsupported Data - Received incompatible data type",
        1005: "No Status Received - No close code provided",
        1006: "Abnormal Closure - Connection lost without close frame",
        1007: "Invalid Data - Received invalid UTF-8 or message payload",
        1008: "Policy Violation - Endpoint policy violated",
        1009: "Message Too Big - Message too large to process",
        1010: "Mandatory Extension - Required extension not negotiated",
        1011: "Internal Error - Unexpected server condition",
        1015: "TLS Handshake Failed - TLS/SSL handshake error",
    }
    
    def filter(self, record):
        # Check the unformatted message first to avoid formatting errors
        original_msg = record.msg if isinstance(record.msg, str) else str(record.msg)
        
        # Enhance connection opened messages
        if "WebSocket connection opened" in original_msg:
            record.msg = "WebSocket connection opened - Client connected to server"
            record.args = ()  # Clear args since we're replacing the message
            return True
        
        # Enhance connection closed messages with code explanations
        if "WebSocket connection closed" in original_msg:
            # Extract code and reason from args if available
            code = None
            reason = None
            
            if record.args and len(record.args) >= 2:
                code = record.args[0]
                reason = record.args[1]
            
            # Build enhanced message
            parts = ["WebSocket connection closed"]
            
            if code is not None and str(code) != 'None':
                try:
                    code_int = int(code) if not isinstance(code, int) else code
                    explanation = self.CLOSE_CODES.get(code_int, f"Unknown code {code_int}")
                    parts.append(f"[Code {code_int}: {explanation}]")
                except (ValueError, TypeError):
                    parts.append(f"[Code {code}]")
            else:
                parts.append("[No close code - likely client refresh/reload]")
            
            if reason and str(reason) != 'None':
                parts.append(f"Reason: {reason}")
            
            record.msg = " ".join(parts)
            record.args = ()  # Clear args since we're replacing the message
            return True
        
        # Enhance ServerConnection messages
        if "ServerConnection created" in original_msg:
            record.msg = "ServerConnection created - New session established"
            record.args = ()  # Clear args since we're replacing the message
            return True
        
        return True

# Apply the filter to Panel/Bokeh loggers
websocket_filter = WebSocketLogFilter()
for logger_name in ['bokeh.server.views.ws', 'tornado.access', 'panel', 'bokeh']:
    logger = logging.getLogger(logger_name)
    logger.addFilter(websocket_filter)

# Configure logging format for better readability
logging.basicConfig(
    format='%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# Load Panel + rrweb + rrweb-player from CDN
pn.extension(
  js_files={
    "rrweb": "https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js",
    "rrwebPlayer": "https://cdn.jsdelivr.net/npm/rrweb-player@latest/dist/index.js",
  },
  css_files=[
    "https://cdn.jsdelivr.net/npm/rrweb@latest/dist/style.css",
    "https://cdn.jsdelivr.net/npm/rrweb-player@latest/dist/style.css",
  ],
)

# Configure Tornado to allow large WebSocket messages (for large rrweb JSON files)
# This must be done at server startup. Start the server with:
# panel serve app.py --show --autoreload --websocket-max-message-size=209715200
# (209715200 bytes = 200MB)
print("[rrweb-demo] For large JSON files (>50MB), start server with: panel serve app.py --websocket-max-message-size=209715200")


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

file_input = pn.widgets.FileInput(name="Load saved rrweb JSON", accept=".json")

events_json = pn.widgets.TextAreaInput(
    name="Recorded events (JSON)",
    placeholder="Click Start recording, interact (zoom/pan), then Stop.",
    height=180,
    sizing_mode="stretch_width",
)

status = pn.pane.Markdown("**Status:** idle", sizing_mode="stretch_width")

# Hidden HTML pane to inject JSON data (used as fallback if execute_script not available)
json_injector = pn.pane.HTML("", width=0, height=0, sizing_mode="fixed")

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

    const RRWEB_URL = "https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js";
    const RRWEB_CSS = "https://cdn.jsdelivr.net/npm/rrweb@latest/dist/style.css";

    function ensureCss(href) {
      if ([...document.styleSheets].some(s => (s.href || "").includes(href))) return;
      if (document.querySelector(`link[rel="stylesheet"][href="${href}"]`)) return;
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    }

    function ensureScript(src, checkFn) {
      return new Promise((resolve, reject) => {
        try {
          if (checkFn()) return resolve(true);
          if (document.querySelector(`script[src="${src}"]`)) {
            // already requested; wait a bit
            const t0 = Date.now();
            const tick = () => {
              if (checkFn()) return resolve(true);
              if (Date.now() - t0 > 8000) return reject(new Error("Timed out loading " + src));
              setTimeout(tick, 100);
            };
            return tick();
          }
          const s = document.createElement("script");
          s.src = src;
          s.async = true;
          s.onload = () => resolve(true);
          s.onerror = () => reject(new Error("Failed to load " + src));
          document.head.appendChild(s);
        } catch (e) {
          reject(e);
        }
      });
    }

    async function startRecording() {
      window.__rrweb_state = window.__rrweb_state || { stopFn: null, events: [], canvasInterval: null };

      if (window.__rrweb_state.stopFn) {
        status.object = "**Status:** already recording";
        return;
      }

      window.__rrweb_state.events = [];
      window.__rrweb_state.stopFn = rrweb.record({
        emit(event) {
          window.__rrweb_state.events.push(event);
        },
        recordCanvas: true,
      });

      // Explicit canvas bitmap capture for Bokeh layers
      let canvasSnapshotCount = 0;
      let totalDataSize = 0;
      window.__rrweb_state.canvasInterval = setInterval(() => {
        try {
          const canvases = document.querySelectorAll('canvas.bk-layer');
          if (!canvases || canvases.length === 0) return;
          
          const snapshots = [];
          canvases.forEach((canvas, idx) => {
            try {
              // Try to capture canvas bitmap with lower quality to reduce size
              const dataURL = canvas.toDataURL('image/jpeg', 0.6); // JPEG at 60% quality
              const sizeKB = Math.round(dataURL.length / 1024);
              totalDataSize += dataURL.length;
              
              snapshots.push({
                index: idx,
                width: canvas.width,
                height: canvas.height,
                dataURL: dataURL,
                sizeKB: sizeKB,
                id: canvas.getAttribute('data-canvas-id') || `bokeh-canvas-${idx}`
              });
            } catch (e) {
              console.warn(`[rrweb-demo] Canvas ${idx} tainted or failed:`, e.message);
            }
          });
          
          if (snapshots.length > 0) {
            // Push custom event (type 5) with canvas snapshots
            window.__rrweb_state.events.push({
              type: 5, // Custom event
              data: {
                tag: 'canvas-snapshot',
                payload: {
                  snapshots: snapshots,
                  timestamp: Date.now()
                }
              },
              timestamp: Date.now()
            });
            canvasSnapshotCount++;
            const totalSizeKB = Math.round(snapshots.reduce((sum, s) => sum + s.sizeKB, 0));
            console.log(`[rrweb-demo] Snapshot ${canvasSnapshotCount}: ${snapshots.length} canvases, ${totalSizeKB}KB (total: ${Math.round(totalDataSize/1024)}KB)`);
          }
        } catch (e) {
          console.error('[rrweb-demo] Canvas capture error:', e);
        }
      }, 1000); // Capture every 1 second (reduced from 200ms)

      status.object = "**Status:** 🔴 recording... (zoom/pan now)";
      start_btn.name = "Recording…";
      start_btn.button_type = "warning";

      stop_btn.disabled = false;
      replay_btn.disabled = true;
      clear_btn.disabled = true;

      console.log("[rrweb-demo] Recording started with canvas capture");
    }

    (async () => {
      try {
        ensureCss(RRWEB_CSS);
        if (!window.rrweb || typeof rrweb.record !== "function") {
          status.object = "**Status:** loading rrweb…";
          await ensureScript(RRWEB_URL, () => window.rrweb && typeof rrweb.record === "function");
        }
        if (!window.rrweb || typeof rrweb.record !== "function") {
          status.object = "**Status:** rrweb not loaded (check Console/Network)";
          alert("rrweb not loaded. Check Network + Console.");
          return;
        }
        await startRecording();
      } catch (e) {
        console.error("[rrweb-demo] Failed to load/start rrweb", e);
        status.object = "**Status:** failed to load rrweb (see Console)";
        alert("Failed to load rrweb. Check Network + Console.");
      }
    })();
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
    },
    code="""
    console.log("[rrweb-demo] Stop clicked");

    if (!window.__rrweb_state || !window.__rrweb_state.stopFn) {
      status.object = "**Status:** not recording";
      return;
    }

    window.__rrweb_state.stopFn();
    window.__rrweb_state.stopFn = null;
    
    // Stop canvas capture interval
    if (window.__rrweb_state.canvasInterval) {
      clearInterval(window.__rrweb_state.canvasInterval);
      window.__rrweb_state.canvasInterval = null;
      console.log('[rrweb-demo] Canvas capture interval cleared');
    }

    const events = window.__rrweb_state.events || [];
    const json = JSON.stringify(events);
    const sizeKB = Math.round(json.length / 1024);
    const sizeMB = (sizeKB / 1024).toFixed(2);

    // Show summary only (don't send full JSON via WebSocket - would exceed message limit!)
    const summary = `Recorded: ${events.length} events, ${sizeMB}MB\n(JSON kept in browser memory, downloaded to file)`;
    events_json.value = summary;

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

    status.object = `**Status:** stopped (${events.length} events, ${sizeMB}MB) ✅`;
    start_btn.name = "Start recording";
    start_btn.button_type = "success";

    stop_btn.disabled = true;
    replay_btn.disabled = (events.length === 0);
    clear_btn.disabled = (events.length === 0);

    console.log("[rrweb-demo] Stopped. Events:", events.length);
    """
)


replay_btn.js_on_click(
    args={"events_json": events_json, "status": status},
    code="""
    console.log("[rrweb-demo] Replay clicked");
    console.log("[rrweb-demo] window.rrwebPlayer available?", typeof window.rrwebPlayer);

    const RRWEB_PLAYER_URL = "https://cdn.jsdelivr.net/npm/rrweb-player@latest/dist/index.js";
    const RRWEB_PLAYER_CSS = "https://cdn.jsdelivr.net/npm/rrweb-player@latest/dist/style.css";

    function ensureCss(href) {
      if ([...document.styleSheets].some(s => (s.href || "").includes(href))) return;
      if (document.querySelector(`link[rel="stylesheet"][href="${href}"]`)) return;
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
      console.log("[rrweb-demo] Added CSS:", href);
    }

    function ensureScript(src, checkFn) {
      return new Promise((resolve, reject) => {
        try {
          if (checkFn()) {
            console.log("[rrweb-demo] Script already loaded:", src);
            return resolve(true);
          }
          if (document.querySelector(`script[src="${src}"]`)) {
            console.log("[rrweb-demo] Script tag exists, waiting for load:", src);
            const t0 = Date.now();
            const tick = () => {
              if (checkFn()) {
                console.log("[rrweb-demo] Script now available:", src);
                return resolve(true);
              }
              if (Date.now() - t0 > 8000) {
                console.error("[rrweb-demo] Timeout loading:", src);
                return reject(new Error("Timed out loading " + src));
              }
              setTimeout(tick, 100);
            };
            return tick();
          }
          console.log("[rrweb-demo] Loading script:", src);
          const s = document.createElement("script");
          s.src = src;
          s.async = true;
          s.onload = () => {
            console.log("[rrweb-demo] Script loaded successfully:", src);
            resolve(true);
          };
          s.onerror = () => {
            console.error("[rrweb-demo] Failed to load script:", src);
            reject(new Error("Failed to load " + src));
          };
          document.head.appendChild(s);
        } catch (e) {
          console.error("[rrweb-demo] Error in ensureScript:", e);
          reject(e);
        }
      });
    }

    async function doReplay() {
      console.log("[rrweb-demo] doReplay started");
      
      if (typeof window.rrwebPlayer !== "function") {
        status.object = "**Status:** loading rrweb-player…";
        console.log("[rrweb-demo] rrwebPlayer not found, loading from CDN");
        ensureCss(RRWEB_PLAYER_CSS);
        await ensureScript(RRWEB_PLAYER_URL, () => typeof window.rrwebPlayer === "function");
        console.log("[rrweb-demo] After ensureScript, rrwebPlayer type:", typeof window.rrwebPlayer);
      }

      if (typeof window.rrwebPlayer !== "function") {
        status.object = "**Status:** rrweb-player not loaded (check Console/Network)";
        console.error("[rrweb-demo] rrwebPlayer still missing after load attempt", window.rrwebPlayer);
        console.error("[rrweb-demo] window keys:", Object.keys(window).filter(k => k.toLowerCase().includes('rrweb')));
        return;
      }

      let events = [];
      try {
        // Try browser memory first (if we just recorded)
        if (window.__rrweb_state && window.__rrweb_state.events && window.__rrweb_state.events.length > 0) {
          events = window.__rrweb_state.events;
          console.log("[rrweb-demo] Using events from browser memory:", events.length);
        } else {
          // Try parsing from widget (for uploaded files)
          events = JSON.parse(events_json.value || "[]");
          console.log("[rrweb-demo] Parsed events from widget:", events.length);
        }
      } catch (e) {
        status.object = "**Status:** no events available (upload JSON file or record first)";
        console.error("[rrweb-demo] No events available:", e);
        return;
      }

      if (!events.length) {
        status.object = "**Status:** no events to replay";
        console.warn("[rrweb-demo] No events to replay");
        return;
      }

      status.object = `**Status:** mounting player (events: ${events.length})…`;
      console.log("[rrweb-demo] Setting up replay container");
      
      // Create or find container at the document body level (bypass Panel isolation)
      let root = document.getElementById("rrweb-replay-root");
      
      if (!root) {
        console.log("[rrweb-demo] Creating replay root at document.body level");
        
        // Create a fixed-position overlay container
        const overlay = document.createElement('div');
        overlay.id = 'rrweb-overlay';
        overlay.style.cssText = `
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 90vw;
          max-width: 1200px;
          height: 80vh;
          background: white;
          border: 2px solid #333;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.3);
          z-index: 10000;
          display: flex;
          flex-direction: column;
        `;
        
        const header = document.createElement('div');
        header.style.cssText = 'padding: 10px; background: #f0f0f0; border-bottom: 1px solid #ccc; display: flex; justify-content: space-between; align-items: center;';
        header.innerHTML = '<strong>rrweb Replay</strong><button id="close-replay" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;">Close</button>';
        
        root = document.createElement('div');
        root.id = 'rrweb-replay-root';
        root.style.cssText = 'flex: 1; overflow: hidden; background: white;';
        
        overlay.appendChild(header);
        overlay.appendChild(root);
        document.body.appendChild(overlay);
        
        document.getElementById('close-replay').onclick = () => {
          document.body.removeChild(overlay);
          status.object = "**Status:** replay closed";
        };
        
        console.log("[rrweb-demo] Created overlay replay container");
      } else {
        console.log("[rrweb-demo] Reusing existing replay root");
      }

      root.innerHTML = "";
      root.style.background = "#fff";

      if (window.__rrweb_player) {
        console.log("[rrweb-demo] Destroying existing player");
        try {
          const rep = window.__rrweb_player.getReplayer ? window.__rrweb_player.getReplayer() : null;
          if (rep && rep.destroy) rep.destroy();
        } catch (e) {
          console.warn("[rrweb-demo] Error destroying old player:", e);
        }
        window.__rrweb_player = null;
      }

      status.object = `**Status:** replaying (events: ${events.length}) ▶️`;
      console.log("[rrweb-demo] Creating new rrwebPlayer with config:", {
        events: events.length,
        width: root.clientWidth || 1000,
        height: root.clientHeight || 600
      });
      
      // Count canvas snapshot events
      const canvasEvents = events.filter(e => e.type === 5 && e.data && e.data.tag === 'canvas-snapshot');
      console.log(`[rrweb-demo] Found ${canvasEvents.length} canvas snapshot events`);
      
      try {
        window.__rrweb_player = new rrwebPlayer({
          target: root,
          props: {
            events,
            autoPlay: true,
            showController: true,
            width: root.clientWidth || 1000,
            height: root.clientHeight || 600,
            UNSAFE_replayCanvas: true,
          },
        });
        console.log("[rrweb-demo] Player created successfully", window.__rrweb_player);
        
        // Hook into replayer to restore canvas snapshots
        try {
          const replayer = window.__rrweb_player.getReplayer();
          if (replayer) {
            let lastCanvasRestore = 0;
            replayer.on('event-cast', (event) => {
              if (event.type === 5 && event.data && event.data.tag === 'canvas-snapshot') {
                const snapshots = event.data.payload.snapshots || [];
                const iframe = root.querySelector('iframe');
                if (!iframe) return;
                
                const replayDoc = iframe.contentDocument || iframe.contentWindow.document;
                if (!replayDoc) return;
                
                snapshots.forEach(snapshot => {
                  const canvases = replayDoc.querySelectorAll('canvas.bk-layer');
                  if (canvases[snapshot.index]) {
                    const canvas = canvases[snapshot.index];
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                      const img = new Image();
                      img.onload = () => {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0);
                        lastCanvasRestore++;
                        if (lastCanvasRestore % 10 === 0) {
                          console.log(`[rrweb-demo] Restored ${lastCanvasRestore} canvas snapshots`);
                        }
                      };
                      img.src = snapshot.dataURL;
                    }
                  }
                });
              }
            });
            console.log('[rrweb-demo] Canvas restoration hook installed');
          }
        } catch (hookErr) {
          console.warn('[rrweb-demo] Could not install canvas restoration hook:', hookErr);
        }
      } catch (e) {
        console.error("[rrweb-demo] Failed to mount rrwebPlayer", e);
        console.error("[rrweb-demo] Error stack:", e.stack);
        status.object = "**Status:** replay failed to mount (see Console)";
        try {
          root.innerHTML = `<div style="padding:10px; color:#b00020; font-family:monospace; white-space:pre-wrap;">${String(e && (e.stack || e.message || e))}</div>`;
        } catch (_) {}
      }
    }

    (async () => {
      try {
        await doReplay();
        console.log("[rrweb-demo] Replay sequence completed");
      } catch (e) {
        console.error("[rrweb-demo] Replay failed at top level", e);
        console.error("[rrweb-demo] Error stack:", e.stack);
        status.object = "**Status:** replay failed (see Console)";
      }
    })();
    """
)



clear_btn.js_on_click(
    args={"events_json": events_json, "replay_btn": replay_btn, "clear_btn": clear_btn, "status": status},
    code="""
    events_json.value = "No events recorded";
    replay_btn.disabled = true;
    clear_btn.disabled = true;

    if (window.__rrweb_player) {
      try {
        const rep = window.__rrweb_player.getReplayer ? window.__rrweb_player.getReplayer() : null;
        if (rep && rep.destroy) rep.destroy();
      } catch (e) {}
      window.__rrweb_player = null;
    }

    if (window.__rrweb_state) {
      window.__rrweb_state.events = [];
      window.__rrweb_state.stopFn = null;
    }

    status.object = "**Status:** cleared";
    """
)


def _load_rrweb_json(event):
    if not event.new:
        return
    try:
        text = event.new.decode("utf-8")
    except Exception:
        text = ""
    
    # Store uploaded JSON in browser memory for replay (avoid WebSocket size limits)
    if text.strip():
        try:
            parsed = json.loads(text)
            event_count = len(parsed) if isinstance(parsed, list) else None
            
            # Show summary (don't send full JSON via WebSocket - would exceed message limit!)
            sizeKB = round(len(text) / 1024)
            sizeMB = round(sizeKB / 1024, 2)
            summary = f"Uploaded: {event_count} events, {sizeMB}MB\n(JSON stored in browser memory for replay)"
            events_json.value = summary
            
            # Store in browser memory via JS execution
            # Use json.dumps to safely escape the parsed JSON for embedding in JS
            json_safe = json.dumps(parsed)
            
            # Try multiple methods to inject JSON into browser memory
            injection_success = False
            try:
                # Method 1: Use pn.state.execute_script if available (Panel 1.0+)
                if hasattr(pn.state, 'execute_script'):
                    pn.state.execute_script(f"""
                        window.__rrweb_state = window.__rrweb_state || {{}};
                        window.__rrweb_state.events = {json_safe};
                        console.log('[rrweb-demo] Loaded', {event_count}, 'events from file into browser memory via execute_script');
                    """)
                    print(f"[rrweb-demo] Injected {event_count} events into browser memory via execute_script")
                    injection_success = True
                # Method 2: Use HTML pane with inline script as fallback
                else:
                    # Update the hidden HTML injector pane with a script that loads the data
                    json_injector.object = f"""
                        <script>
                        (function() {{
                            window.__rrweb_state = window.__rrweb_state || {{}};
                            window.__rrweb_state.events = {json_safe};
                            console.log('[rrweb-demo] Loaded', {event_count}, 'events from file into browser memory via HTML injector');
                        }})();
                        </script>
                    """
                    print(f"[rrweb-demo] Set HTML injector for {event_count} events (fallback method)")
                    injection_success = True
            except Exception as js_err:
                print(f"[rrweb-demo] Failed to inject JSON into browser memory: {js_err}")
                injection_success = False
            
            if not injection_success:
                # If injection fails, the replay button will try to parse from events_json
                # but this will fail for large files due to WebSocket limits
                status.object = f"**Status:** loaded {event_count} events ({sizeMB}MB) - Warning: may not replay properly for large files"
                return
            
            replay_btn.disabled = False
            clear_btn.disabled = False
            status.object = f"**Status:** loaded {event_count} events ({sizeMB}MB)"
        except Exception as e:
            events_json.value = "Failed to parse uploaded JSON"
            status.object = f"**Status:** file load failed - {str(e)}"
            replay_btn.disabled = True
            clear_btn.disabled = True
    else:
        events_json.value = ""
        status.object = "**Status:** file load failed - empty file"
        replay_btn.disabled = True
        clear_btn.disabled = True


file_input.param.watch(_load_rrweb_json, "value")


controls = pn.Row(start_btn, stop_btn, replay_btn, clear_btn, file_input, sizing_mode="stretch_width")

pn.template.FastListTemplate(
    title="Panel + Bokeh + rrweb (minimal demo)",
    main=[
        json_injector,  # Hidden HTML pane for JS injection (fallback method)
        controls,
        status,
        plot,
        events_json,
    ],
).servable()

