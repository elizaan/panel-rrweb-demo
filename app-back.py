import io
import urllib.request

import numpy as np
import panel as pn
from bokeh.models import WheelZoomTool, PanTool, ResetTool, BoxZoomTool
from bokeh.plotting import figure
from PIL import Image

pn.extension()

IMAGE_URL = "https://assets.holoviz.org/panel/tutorials/wind_turbine.png"

# --- Load image from URL ---
with urllib.request.urlopen(IMAGE_URL) as resp:
    data = resp.read()

img = Image.open(io.BytesIO(data)).convert("RGBA")
arr = np.asarray(img)
h, w = arr.shape[:2]

# Pack RGBA into uint32 for Bokeh image_rgba
rgba = np.flipud(arr).view(dtype=np.uint32).reshape((h, w))

# --- Create tools (keep references so we can set them active) ---
wheel_zoom = WheelZoomTool()
pan = PanTool()
box_zoom = BoxZoomTool()
reset = ResetTool()

# --- Create Bokeh figure (tools="" prevents Bokeh defaults) ---
p = figure(
    title="Panel + Bokeh Image Viewer",
    x_range=(0, w),
    y_range=(0, h),
    width=900,
    height=650,
    match_aspect=True,
    toolbar_location="above",
    tools="",  # important: start with no default tools
)

# Add image
p.image_rgba(image=[rgba], x=0, y=0, dw=w, dh=h)

# Add tools
p.add_tools(wheel_zoom, pan, box_zoom, reset)

# Set active tools
p.toolbar.active_scroll = wheel_zoom
p.toolbar.active_drag = pan

# Clean look
p.xaxis.visible = False
p.yaxis.visible = False
p.grid.visible = False

pn.template.FastListTemplate(
    title="Panel + Bokeh Image Viewer",
    main=[pn.pane.Bokeh(p, sizing_mode="stretch_both")],
).servable()
