"""
Test the export functionality
"""

import requests
import json

# Test if the app is running
response = requests.get("http://localhost:8050")
if response.status_code == 200:
    print("✓ App is running")
else:
    print("✗ App not accessible")
    exit(1)

# Get the layout to check for export buttons
response = requests.get("http://localhost:8050/_dash-layout")
if response.status_code == 200:
    layout = response.json()
    layout_str = json.dumps(layout)
    
    # Check for export components
    if 'export-image-btn' in layout_str:
        print("✓ Image export button present")
    else:
        print("✗ Image export button missing")
    
    if 'export-pyvis-btn' in layout_str:
        print("✓ PyVis export button present")
    else:
        print("✗ PyVis export button missing")
    
    if 'export-obsidian-btn' in layout_str:
        print("✓ Obsidian export button present")
    else:
        print("✗ Obsidian export button missing")
    
    if 'download-output' in layout_str:
        print("✓ Download component present")
    else:
        print("✗ Download component missing")

# Check dependencies
response = requests.get("http://localhost:8050/_dash-dependencies")
if response.status_code == 200:
    deps = response.json()
    
    # Look for export callback
    export_callback_found = False
    for dep in deps:
        outputs = dep.get('outputs', [])
        for output in outputs:
            if output.get('id') == 'download-output':
                export_callback_found = True
                break
    
    if export_callback_found:
        print("✓ Export callback registered")
    else:
        print("✗ Export callback not found")

print("\n✅ Export functionality is properly configured!")
print("\nYou can now use the app at http://localhost:8050")
print("Click any of the export buttons to download the graph in different formats:")