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

panel serve app.py --show --autoreload
```

## Use the demo

- The page will auto-start rrweb recording after load
- Interact with the app (click Yes/No, pan/zoom the “image”)
- Click **Stop & download (.json)** to save the recorded rrweb events

## Notes

- rrweb is loaded from a CDN (`unpkg`) and runs fully in the browser for this first demo.
- Pan/zoom is provided by the lightweight `@panzoom/panzoom` library (also via CDN).
