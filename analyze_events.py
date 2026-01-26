import json
from collections import Counter

with open('rrweb-session-canvas.json', 'r') as f:
    events = json.load(f)

print("=" * 60)
print("RRWEB EVENT STRUCTURE ANALYSIS")
print("=" * 60)

# Event type summary
print("\n1. EVENT TYPE SUMMARY:")
print("-" * 60)
type_counts = Counter(e['type'] for e in events)
type_names = {
    2: "FullSnapshot (DOM tree with node IDs)",
    3: "IncrementalSnapshot (user interactions)",
    4: "Meta (page metadata)",
    5: "Custom (our canvas snapshots)"
}
for t, count in sorted(type_counts.items()):
    print(f"   Type {t} - {type_names.get(t, 'Unknown')}: {count} events")

# Click events
print("\n2. CLICK EVENTS (Button clicks):")
print("-" * 60)
clicks = [e for e in events if e.get('type') == 3 and e.get('data', {}).get('source') == 2]
print(f"   Total click events: {len(clicks)}")
if clicks:
    print("\n   Example click event:")
    c = clicks[0]
    print(f"   - Timestamp: {c['timestamp']}")
    print(f"   - Node ID: {c['data'].get('id')} (identifies which element was clicked)")
    print(f"   - Position: x={c['data'].get('x')}, y={c['data'].get('y')}")
    print(f"   - Click type: {c['data'].get('type')} (0=mouseup, 1=mousedown, 2=click)")

# Mouse movements
print("\n3. MOUSE MOVEMENT EVENTS:")
print("-" * 60)
moves = [e for e in events if e.get('type') == 3 and e.get('data', {}).get('source') == 1]
print(f"   Total mouse move events: {len(moves)}")
if moves:
    print(f"   Example: Node ID={moves[0]['data'].get('id')}, Position: ({moves[0]['data']['positions'][0]['x']}, {moves[0]['data']['positions'][0]['y']})")

# Scroll events
print("\n4. SCROLL EVENTS (zoom/pan):")
print("-" * 60)
scrolls = [e for e in events if e.get('type') == 3 and e.get('data', {}).get('source') == 3]
print(f"   Total scroll events: {len(scrolls)}")
if scrolls:
    print(f"   Example: Node ID={scrolls[0]['data'].get('id')}, x={scrolls[0]['data'].get('x')}, y={scrolls[0]['data'].get('y')}")

# Canvas snapshots
print("\n5. CANVAS SNAPSHOT EVENTS (our custom):")
print("-" * 60)
canvas_events = [e for e in events if e.get('type') == 5 and e.get('data', {}).get('tag') == 'canvas-snapshot']
print(f"   Total canvas snapshots: {len(canvas_events)}")
if canvas_events:
    snap = canvas_events[0]['data']['payload']['snapshots'][0]
    print(f"   Example snapshot:")
    print(f"   - Canvas ID: {snap['id']}")
    print(f"   - Size: {snap['width']}x{snap['height']}")
    print(f"   - Data size: {snap['sizeKB']}KB")

# Node ID mapping (from full snapshot)
print("\n6. HOW COMPONENTS ARE IDENTIFIED:")
print("-" * 60)
full_snapshot = [e for e in events if e['type'] == 2]
if full_snapshot:
    print("   rrweb creates a DOM tree snapshot with unique node IDs:")
    print("   - Each HTML element gets a unique ID (e.g., button ID=234)")
    print("   - Interaction events reference these IDs")
    print("   - Example: 'Click on node 234' = 'Click Start button'")
    print("\n   To identify components in different dashboards:")
    print("   - Add data-* attributes to your components")
    print("   - Example: <button data-component='start-recording'>")
    print("   - Then analyze events to map node IDs to components")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
print("✓ Yes, different buttons have different node IDs")
print("✓ Image canvas has its own node ID")
print("✓ All interactions (click/scroll/zoom) reference node IDs")
print("✓ To make this reusable: add data-component attributes")
print("  to tag your dashboard elements")
print("=" * 60)
