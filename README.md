# Simple Panel + rrweb demo

Very small first demo that shows:

- A **Panel** dashboard with an “image” (an inline SVG) that supports **pan + zoom**
- Two buttons: **Yes** / **No**
- **rrweb** recording of user interactions, with a **Stop & Download** button that saves a recording JSON file

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Standard run (default WebSocket limit ~10MB)
panel serve app.py --show --autoreload 

# For large JSON files: increase WebSocket message size limit to 200MB
panel serve app.py --show --autoreload --websocket-max-message-size=209715200
```

**Note:** The `--websocket-max-message-size` flag accepts bytes. Common values:
- 50MB = `52428800`
- 100MB = `104857600`
- 200MB = `209715200` (recommended for large recordings)
- 500MB = `524288000`
- 1GB = `1073741824`

Adjust based on your largest expected recording file size.

## Use the demo

- The page will auto-start rrweb recording after load
- Interact with the app (click Yes/No, pan/zoom the “image”)
- Click **Stop & download (.json)** to save the recorded rrweb events

## Notes

- rrweb is loaded from a CDN (`unpkg`) and runs fully in the browser for this first demo.
- Pan/zoom is provided by the lightweight `@panzoom/panzoom` library (also via CDN).
