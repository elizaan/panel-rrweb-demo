# Building a Reusable Dashboard Recording Framework

## How rrweb Records User Interactions

### Event Structure

rrweb records 5 types of events:

```json
{
  "type": 2,  // FullSnapshot - Initial DOM tree with node IDs
  "type": 3,  // IncrementalSnapshot - User interactions (clicks, moves, scrolls)
  "type": 4,  // Meta - Page metadata (URL, dimensions)
  "type": 5,  // Custom - Your custom events (we use this for canvas snapshots)
}
```

### How Components Are Tracked

**Key Concept:** rrweb assigns a unique **node ID** to every HTML element in the DOM.

```json
// Example: Full snapshot (Type 2) creates the ID mapping
{
  "type": 2,
  "data": {
    "node": {
      "childNodes": [
        {
          "id": 234,
          "tagName": "button",
          "attributes": {
            "class": "bk-btn bk-btn-success",
            "data-component": "start-recording"  // ← Custom identifier!
          }
        },
        {
          "id": 235,
          "tagName": "button",
          "attributes": {
            "class": "bk-btn bk-btn-danger",
            "data-component": "stop-recording"
          }
        },
        {
          "id": 456,
          "tagName": "canvas",
          "attributes": {
            "class": "bk-layer",
            "data-component": "main-visualization"
          }
        }
      ]
    }
  }
}

// Then, interactions reference these IDs:
{
  "type": 3,
  "data": {
    "source": 2,  // MouseClick
    "type": 2,    // Click event
    "id": 234     // ← "User clicked the element with ID 234 (Start button)"
  }
}

{
  "type": 3,
  "data": {
    "source": 3,  // Scroll/Wheel
    "id": 456,    // ← "User scrolled on element ID 456 (Canvas)"
    "x": 120,
    "y": 50
  }
}
```

### Answer to Your Question

**Q: Do the two buttons have different tags under same type?**
**A:** Yes! Both buttons are type 3 events with source 2 (click), but they have **different node IDs**:
- Start button = node ID 234
- Stop button = node ID 235

The **node ID is the unique identifier** that tells them apart.

**Q: Does the image have another ID?**
**A:** Yes! The canvas element has its own unique node ID (e.g., 456), separate from the buttons.

## Building a Reusable Framework

### Strategy 1: Node ID Mapping (Post-Processing)

After recording, analyze the full snapshot to map node IDs to components:

```python
def analyze_recording(events):
    """Extract component interactions from rrweb events"""
    
    # Step 1: Build node ID → component mapping from full snapshot
    node_map = {}
    full_snapshot = next(e for e in events if e['type'] == 2)
    
    def traverse_nodes(node):
        if 'id' in node and 'attributes' in node:
            attrs = node['attributes']
            # Look for data-component attribute
            if 'data-component' in attrs:
                node_map[node['id']] = {
                    'component': attrs['data-component'],
                    'tag': node.get('tagName'),
                    'class': attrs.get('class', '')
                }
        if 'childNodes' in node:
            for child in node['childNodes']:
                traverse_nodes(child)
    
    traverse_nodes(full_snapshot['data']['node'])
    
    # Step 2: Extract interactions by component
    interactions = []
    for event in events:
        if event['type'] == 3:  # Incremental snapshot (interaction)
            node_id = event['data'].get('id')
            if node_id in node_map:
                source_names = {1: 'MouseMove', 2: 'MouseClick', 3: 'Scroll', 5: 'MouseInteraction'}
                interactions.append({
                    'timestamp': event['timestamp'],
                    'component': node_map[node_id]['component'],
                    'action': source_names.get(event['data']['source'], 'Unknown'),
                    'data': event['data']
                })
    
    return interactions

# Usage:
with open('rrweb-session.json') as f:
    events = json.load(f)

interactions = analyze_recording(events)

# Result:
# [
#   {'timestamp': 1234567890, 'component': 'start-recording', 'action': 'MouseClick', ...},
#   {'timestamp': 1234567891, 'component': 'main-visualization', 'action': 'Scroll', ...},
#   {'timestamp': 1234567892, 'component': 'stop-recording', 'action': 'MouseClick', ...}
# ]
```

### Strategy 2: Tag Components in Dashboard Code

Modify your dashboard to add `data-component` attributes:

```python
import panel as pn

# Add custom attributes to Panel widgets
start_btn = pn.widgets.Button(
    name="Start recording",
    button_type="success"
)
# Add data-component attribute via JS
start_btn.js_on_click(code="""
    // Set identifier on first click
    event.target.setAttribute('data-component', 'start-recording');
""")

# Or use CSS classes as identifiers
start_btn.css_classes = ['recording-start-btn']
stop_btn.css_classes = ['recording-stop-btn']
```

For Bokeh plots:

```python
from bokeh.plotting import figure

p = figure(title="Visualization")
# Add custom attribute via JS callback
p.js_on_event('wheel', CustomJS(code="""
    const canvas = document.querySelector('canvas.bk-layer');
    if (canvas) canvas.setAttribute('data-component', 'main-plot');
"""))
```

### Strategy 3: Custom Event Injection

Instead of relying only on rrweb's DOM tracking, inject your own semantic events:

```javascript
// In your dashboard, add explicit event tracking
function trackComponentInteraction(componentName, action, metadata) {
    if (window.__rrweb_state) {
        window.__rrweb_state.events.push({
            type: 5,  // Custom event
            data: {
                tag: 'component-interaction',
                payload: {
                    component: componentName,
                    action: action,
                    metadata: metadata,
                    timestamp: Date.now()
                }
            },
            timestamp: Date.now()
        });
    }
}

// Use it:
startButton.addEventListener('click', () => {
    trackComponentInteraction('start-recording', 'click', {button: 'start'});
    // ... your recording logic
});

document.querySelector('.bk-layer').addEventListener('wheel', (e) => {
    trackComponentInteraction('main-visualization', 'zoom', {
        deltaY: e.deltaY,
        x: e.clientX,
        y: e.clientY
    });
});
```

## Complete Framework Architecture

```
┌─────────────────────────────────────────────────────┐
│           Your Dashboard Application                │
│  (Any Panel/Bokeh/Streamlit/Plotly dashboard)      │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ 1. Inject recording code
                   ├──────────────────────────┐
                   │                          │
         ┌─────────▼────────┐      ┌─────────▼────────────┐
         │  rrweb recorder  │      │  Component Tagger    │
         │  (DOM tracking)  │      │  (data-component)    │
         └─────────┬────────┘      └─────────┬────────────┘
                   │                          │
                   │ 2. Record events         │
                   │                          │
         ┌─────────▼──────────────────────────▼────────┐
         │        Browser Memory Storage               │
         │   window.__rrweb_state.events = [...]      │
         └─────────┬───────────────────────────────────┘
                   │
                   │ 3. Save to JSON
                   │
         ┌─────────▼───────────┐
         │  rrweb-session.json │
         │                     │
         │  - Type 2: DOM tree │
         │  - Type 3: Clicks   │
         │  - Type 3: Scrolls  │
         │  - Type 5: Custom   │
         └─────────┬───────────┘
                   │
                   │ 4. Analysis
                   │
         ┌─────────▼────────────────┐
         │  Component Analyzer      │
         │  - Map node IDs          │
         │  - Extract interactions  │
         │  - Generate timeline     │
         └─────────┬────────────────┘
                   │
                   │ 5. Insights
                   │
         ┌─────────▼────────────────┐
         │  Analytics Dashboard     │
         │  - Which components used?│
         │  - How many interactions?│
         │  - User flow patterns?   │
         └──────────────────────────┘
```

## Framework Implementation

### 1. Core Recorder Module (`dashboard_recorder.py`)

```python
import panel as pn
import json

class DashboardRecorder:
    """Reusable rrweb recorder for any Panel dashboard"""
    
    def __init__(self):
        self.events_json = pn.widgets.TextAreaInput(
            name="Recorded events",
            height=180,
            sizing_mode="stretch_width"
        )
        self.status = pn.pane.Markdown("**Status:** idle")
        
        # Buttons
        self.start_btn = pn.widgets.Button(
            name="Start recording",
            button_type="success"
        )
        self.stop_btn = pn.widgets.Button(
            name="Stop + download",
            button_type="danger",
            disabled=True
        )
        self.replay_btn = pn.widgets.Button(
            name="Replay",
            button_type="primary",
            disabled=True
        )
        
        # Attach JS handlers
        self._setup_js_handlers()
    
    def _setup_js_handlers(self):
        """Setup JS recording logic"""
        # ... (your current JS code from app.py)
        pass
    
    def tag_component(self, widget, component_name):
        """Add data-component attribute to a Panel widget"""
        widget.js_on_click(code=f"""
            event.target.setAttribute('data-component', '{component_name}');
        """)
    
    def controls(self):
        """Return recording controls"""
        return pn.Row(
            self.start_btn,
            self.stop_btn,
            self.replay_btn,
            sizing_mode="stretch_width"
        )
```

### 2. Component Analyzer (`analyze_recording.py`)

```python
import json
from collections import defaultdict

class RecordingAnalyzer:
    """Analyze rrweb recordings to extract component interactions"""
    
    def __init__(self, events):
        self.events = events
        self.node_map = self._build_node_map()
    
    def _build_node_map(self):
        """Map node IDs to component info"""
        node_map = {}
        full_snapshot = next((e for e in self.events if e['type'] == 2), None)
        if not full_snapshot:
            return node_map
        
        def traverse(node):
            if isinstance(node, dict):
                if 'id' in node:
                    node_map[node['id']] = {
                        'tag': node.get('tagName'),
                        'classes': node.get('attributes', {}).get('class', ''),
                        'component': node.get('attributes', {}).get('data-component'),
                        'name': node.get('attributes', {}).get('name')
                    }
                if 'childNodes' in node:
                    for child in node['childNodes']:
                        traverse(child)
        
        traverse(full_snapshot['data']['node'])
        return node_map
    
    def get_component_interactions(self):
        """Extract all component interactions"""
        interactions = []
        
        for event in self.events:
            if event['type'] == 3:  # Incremental snapshot
                node_id = event['data'].get('id')
                if node_id and node_id in self.node_map:
                    comp_info = self.node_map[node_id]
                    source = event['data'].get('source')
                    
                    action_names = {
                        1: 'mouse_move',
                        2: 'mouse_click',
                        3: 'scroll',
                        5: 'mouse_interaction'
                    }
                    
                    interactions.append({
                        'timestamp': event['timestamp'],
                        'component': comp_info.get('component') or comp_info.get('name') or f"node_{node_id}",
                        'action': action_names.get(source, 'unknown'),
                        'data': event['data']
                    })
        
        return interactions
    
    def get_component_summary(self):
        """Get usage summary by component"""
        interactions = self.get_component_interactions()
        summary = defaultdict(lambda: {'clicks': 0, 'scrolls': 0, 'moves': 0})
        
        for interaction in interactions:
            comp = interaction['component']
            action = interaction['action']
            
            if action == 'mouse_click':
                summary[comp]['clicks'] += 1
            elif action == 'scroll':
                summary[comp]['scrolls'] += 1
            elif action == 'mouse_move':
                summary[comp]['moves'] += 1
        
        return dict(summary)

# Usage:
with open('rrweb-session.json') as f:
    events = json.load(f)

analyzer = RecordingAnalyzer(events)
summary = analyzer.get_component_summary()

print("Component Usage Summary:")
for component, stats in summary.items():
    print(f"  {component}:")
    print(f"    Clicks: {stats['clicks']}")
    print(f"    Scrolls: {stats['scrolls']}")
```

### 3. Usage in Any Dashboard

```python
import panel as pn
from dashboard_recorder import DashboardRecorder

# Your dashboard
recorder = DashboardRecorder()

# Tag your components
my_button = pn.widgets.Button(name="Action Button")
recorder.tag_component(my_button, 'action-button')

my_plot = pn.pane.Bokeh(figure(...))
# Canvas tagging happens automatically via our canvas capture

# Layout
dashboard = pn.template.FastListTemplate(
    title="My Dashboard",
    main=[
        recorder.controls(),  # Recording controls
        recorder.status,      # Status display
        my_button,            # Your components
        my_plot,
        recorder.events_json  # Event display
    ]
).servable()
```

## Critical Limitation: WebSocket Size Constraints

### Why Recent Recordings Replay But Large Uploaded Files Don't

**The Problem:**

You may notice that:
- ✅ **Recent recording works**: Record → Stop → Replay works perfectly
- ❌ **Large uploaded file fails**: Upload 50MB+ JSON → Replay fails silently

**Root Cause:**

There are **two different data paths** with different size limits:

#### Path 1: Recording (Works for any size)
```
Browser JS                Browser Memory              File Download
┌─────────┐              ┌──────────────┐           ┌────────────┐
│ rrweb   │──capture──→  │ window.      │──export──→│ JSON file  │
│ records │              │ __rrweb_     │           │ (any size) │
│ events  │              │ state.events │           │            │
└─────────┘              └──────────────┘           └────────────┘
                               ↓
                          Replay (✅ Works)
```

Events never leave browser memory, so size is unlimited (up to browser memory limits ~100MB+).

#### Path 2: File Upload (Fails for large files)
```
File Upload              Python Backend             WebSocket             Browser Memory
┌────────────┐          ┌───────────────┐         ┌──────────┐         ┌──────────────┐
│ User       │─upload──→│ Panel reads   │─script─→│ 10MB     │──X──→  │ window.      │
│ selects    │          │ file, calls   │         │ LIMIT!   │        │ __rrweb_     │
│ 50MB JSON  │          │ execute_script│         │          │        │ state.events │
└────────────┘          └───────────────┘         └──────────┘         └──────────────┘
                                                        ↑
                                            BOTTLENECK: Panel/Bokeh WebSocket
                                            has ~10MB message size limit!
```

**The Issue:**
```python
# In _load_rrweb_json():
json_safe = json.dumps(parsed)  # Could be 50MB+
pn.state.execute_script(f"""
    window.__rrweb_state.events = {json_safe};  # ← This goes through WebSocket!
""")
```

The `execute_script()` command must send the entire JSON through Panel's WebSocket connection, which has a **~10MB message size limit**. For large files (>10MB), the command fails silently.

### Solution Options

#### Option 1: Client-Side File Reading (Best for large files)

Instead of uploading through Panel, read the file directly in JavaScript:

```python
# Modified file_input handler
file_input = pn.widgets.FileInput(name="Load JSON (client-side)", accept=".json")

file_input.js_on_change('value', code="""
async function loadFile() {
    if (!value || value.length === 0) return;
    
    // Read file as text (client-side, no WebSocket involved!)
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const events = JSON.parse(e.target.result);
            window.__rrweb_state = window.__rrweb_state || {};
            window.__rrweb_state.events = events;
            
            const sizeKB = Math.round(e.target.result.length / 1024);
            const sizeMB = (sizeKB / 1024).toFixed(2);
            console.log(`[rrweb-demo] Loaded ${events.length} events (${sizeMB}MB) client-side`);
            
            // Enable replay button
            // Note: Can't directly modify Panel widget, so use DOM manipulation
            document.querySelector('[name="Replay"]').disabled = false;
        } catch (err) {
            console.error('[rrweb-demo] Failed to parse JSON:', err);
        }
    };
    reader.readAsText(value[0]);
}
loadFile();
""")
```

**Pros:**
- ✅ No size limit (works with 100MB+ files)
- ✅ No WebSocket overhead
- ✅ Faster for large files

**Cons:**
- ❌ Can't update Panel widgets directly from JS (need workarounds)

#### Option 2: Chunked Upload (Medium files)

Split large JSON into chunks and send via multiple WebSocket messages:

```python
def _load_rrweb_json_chunked(event):
    if not event.new:
        return
    
    text = event.new.decode("utf-8")
    parsed = json.loads(text)
    
    # Split into chunks (5MB per chunk to stay under 10MB limit)
    chunk_size = 1000  # events per chunk
    chunks = [parsed[i:i+chunk_size] for i in range(0, len(parsed), chunk_size)]
    
    # Send initialization
    pn.state.execute_script("""
        window.__rrweb_state = window.__rrweb_state || {};
        window.__rrweb_state.events = [];
    """)
    
    # Send each chunk
    for i, chunk in enumerate(chunks):
        json_chunk = json.dumps(chunk)
        pn.state.execute_script(f"""
            window.__rrweb_state.events.push(...{json_chunk});
            console.log('[rrweb-demo] Loaded chunk {i+1}/{len(chunks)}');
        """)
    
    status.object = f"**Status:** loaded {len(parsed)} events in {len(chunks)} chunks"
```

**Pros:**
- ✅ Works with Panel widget updates
- ✅ Handles medium files (up to ~50MB)

**Cons:**
- ❌ Multiple WebSocket round-trips (slower)
- ❌ Still has practical limits

#### Option 3: Server-Side Storage + Reference (Enterprise)

Store large files on server, only send reference to browser:

```python
import uuid

uploaded_sessions = {}  # In-memory or database

def _load_rrweb_json(event):
    text = event.new.decode("utf-8")
    parsed = json.loads(text)
    
    # Store on server
    session_id = str(uuid.uuid4())
    uploaded_sessions[session_id] = parsed
    
    # Send only the reference
    pn.state.execute_script(f"""
        window.__rrweb_session_id = '{session_id}';
        console.log('[rrweb-demo] Session stored on server: {session_id}');
    """)

# Modified replay to fetch from server
def get_session_events(session_id):
    """Endpoint to fetch events by ID"""
    return uploaded_sessions.get(session_id, [])
```

Then fetch via AJAX when replaying.

**Pros:**
- ✅ No size limits
- ✅ Fast upload (small reference)
- ✅ Can use database/blob storage

**Cons:**
- ❌ More complex architecture
- ❌ Requires server-side session management

### Recommended Approach

For a production framework:

1. **Small files (<5MB)**: Use current `execute_script()` approach
2. **Medium files (5-50MB)**: Use **chunked upload** (Option 2)
3. **Large files (>50MB)**: Use **client-side file reading** (Option 1)

Implement auto-detection:

```python
def _load_rrweb_json(event):
    if not event.new:
        return
    
    text = event.new.decode("utf-8")
    size_mb = len(text) / (1024 * 1024)
    
    if size_mb < 5:
        # Small file: direct injection
        parsed = json.loads(text)
        json_safe = json.dumps(parsed)
        pn.state.execute_script(f"""
            window.__rrweb_state = window.__rrweb_state || {{}};
            window.__rrweb_state.events = {json_safe};
        """)
    else:
        # Large file: use client-side loading via FileReader
        pn.state.execute_script("""
            console.warn('[rrweb-demo] File too large for WebSocket, use client-side file input');
            alert('File is large. Please use the browser file reader instead.');
        """)
```

## Summary

**How components are tracked:**
- ✅ Each HTML element gets a unique **node ID** in the rrweb recording
- ✅ Start button, Stop button, Image canvas all have **different node IDs**
- ✅ All interactions (clicks, scrolls, zooms) reference these IDs
- ✅ Type 3 events contain the action (click/scroll) + node ID

**To make it reusable:**
1. Add `data-component` attributes to your dashboard widgets
2. Use the `RecordingAnalyzer` class to map node IDs → component names
3. Extract component-level interaction summaries
4. Works with **any Panel/Bokeh dashboard** - just tag your components!

**WebSocket Size Limits:**
- Recent recordings work because events never leave browser memory
- Uploaded large files fail because `execute_script()` goes through WebSocket (~10MB limit)
- Solution: Use client-side file reading for large files (Option 1 above)

**Next Steps:**
- Implement `DashboardRecorder` as a reusable class with size-aware file loading
- Add automatic component tagging via Panel widget wrapping
- Build analytics dashboard to visualize usage patterns
- Store recordings in database with metadata (user, session, dashboard version)
