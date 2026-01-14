import panel as pn
from pathlib import Path

pn.extension()

# Load SVG
svg_path = Path(__file__).parent / "assets" / "demo.svg"
svg_content = svg_path.read_text()

# Create HTML with inline SVG and pure CSS/JS zoom
# Panel strips IDs, so use querySelector for SVG directly
html_content = f"""
<div style="width: 100%; height: 600px; overflow: auto; border: 2px solid red;">
    <div style="transform-origin: 0 0; transition: transform 0.1s;">
        {svg_content}
    </div>
</div>

<div style="margin-top: 20px;">
    <button onclick="zoomIn()">Zoom In (+)</button>
    <button onclick="zoomOut()">Zoom Out (-)</button>
    <button onclick="resetZoom()">Reset</button>
    <span style="margin-left: 10px; font-weight: bold;">Zoom: <span data-zoom-display>100%</span></span>
</div>

<script>
(function() {{
    let scale = 1;
    let svg = null;
    let container = null;
    let zoomDisplay = null;
    
    function findElements() {{
        svg = document.querySelector('svg');
        zoomDisplay = document.querySelector('[data-zoom-display]');
        
        if (svg) {{
            container = svg.parentElement;
            console.log('✅ Found SVG:', svg);
            console.log('✅ Container:', container);
            return true;
        }}
        return false;
    }}
    
    function updateZoom() {{
        if (!container) return;
        container.style.transform = 'scale(' + scale + ')';
        if (zoomDisplay) {{
            zoomDisplay.textContent = Math.round(scale * 100) + '%';
        }}
    }}
    
    window.zoomIn = function() {{
        if (!svg) {{
            console.log('Waiting for SVG to load...');
            return;
        }}
        scale *= 1.2;
        updateZoom();
        console.log('Zoomed in to', scale);
    }};
    
    window.zoomOut = function() {{
        if (!svg) {{
            console.log('Waiting for SVG to load...');
            return;
        }}
        scale /= 1.2;
        updateZoom();
        console.log('Zoomed out to', scale);
    }};
    
    window.resetZoom = function() {{
        if (!svg) return;
        scale = 1;
        updateZoom();
        console.log('Reset zoom');
    }};
    
    function setupZoom() {{
        // Mousewheel zoom on the outer container
        container.parentElement.addEventListener('wheel', function(e) {{
            e.preventDefault();
            if (e.deltaY < 0) {{
                scale *= 1.1;
            }} else {{
                scale /= 1.1;
            }}
            updateZoom();
            console.log('🎡 Mouse wheel zoom:', scale);
        }});
        
        console.log('✅✅✅ Zoom controls ready! Use buttons or mouse wheel over image! ✅✅✅');
    }}
    
    // Poll for SVG element
    let attempts = 0;
    const pollInterval = setInterval(function() {{
        attempts++;
        console.log('Looking for SVG... attempt', attempts);
        console.log('  Total elements:', document.querySelectorAll('*').length);
        console.log('  SVGs found:', document.querySelectorAll('svg').length);
        
        if (findElements()) {{
            clearInterval(pollInterval);
            setupZoom();
        }} else if (attempts >= 100) {{
            console.error('❌ SVG not found after 100 attempts');
            console.log('All HTML:', document.body.innerHTML.substring(0, 500));
            clearInterval(pollInterval);
        }}
    }}, 200);
}})();
</script>
"""

app = pn.Column(
    "# Simple Zoom Test",
    "Use the buttons below or **mouse wheel over the image** to zoom:",
    pn.pane.HTML(html_content, height=800)
)

app.servable()
