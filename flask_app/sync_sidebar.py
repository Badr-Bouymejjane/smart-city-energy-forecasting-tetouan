import os
import re
from pathlib import Path

templates_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates")

# Map of template filename to the href that should be active
file_to_href = {
    "index.html": "/",
    "models.html": "/models",
    "xgboost_details.html": "/models/xgboost",
    "data.html": "/data",
    "correlations.html": "/correlations",
    "analytics.html": "/correlations", # Fallback if analytics.html is still used
    "settings.html": "/settings"
}

active_classes = "flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all"
inactive_classes = "flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all"

# Read the sidebar from index.html (the source of truth)
index_content = (templates_dir / "index.html").read_text(encoding="utf-8")
sidebar_start = index_content.find('<aside')
sidebar_end = index_content.find('</aside>') + len('</aside>')
base_sidebar = index_content[sidebar_start:sidebar_end]

# Make all links inactive in the base_sidebar
# 1. Replace active classes with inactive classes
base_sidebar = base_sidebar.replace(active_classes, inactive_classes)
# 2. Replace FILL 1 with FILL 0
base_sidebar = base_sidebar.replace("'FILL' 1", "'FILL' 0")

for filename, active_href in file_to_href.items():
    filepath = templates_dir / filename
    if not filepath.exists():
        continue
        
    content = filepath.read_text(encoding="utf-8")
    
    # Extract the current sidebar bounds
    current_sidebar_start = content.find('<aside')
    current_sidebar_end = content.find('</aside>') + len('</aside>')
    
    if current_sidebar_start == -1 or current_sidebar_end == -1:
        print(f"No sidebar found in {filename}")
        continue
        
    # Customize the base sidebar for this file
    custom_sidebar = base_sidebar
    
    # Find the link with the active_href and make it active
    # We need to find: <a class="[inactive_classes]" href="[active_href]">
    # and change to: <a class="[active_classes]" href="[active_href]">
    target_a_tag_start = f'href="{active_href}"'
    
    # Use regex to find the specific <a> block for this href and make it active
    # This is a bit tricky, let's just do it string manipulation way
    # Split the sidebar by `<a class="`
    parts = custom_sidebar.split('<a class="')
    for i in range(1, len(parts)):
        if f'href="{active_href}"' in parts[i][:500]: # Look ahead to ensure it's the right link
            # Replace classes
            parts[i] = parts[i].replace(inactive_classes.replace("flex items-center ", ""), active_classes.replace("flex items-center ", ""), 1)
            # Find the first span and replace FILL 0 with FILL 1
            span_idx = parts[i].find('<span')
            if span_idx != -1:
                end_span_idx = parts[i].find('>', span_idx)
                parts[i] = parts[i][:span_idx] + parts[i][span_idx:end_span_idx].replace("'FILL' 0", "'FILL' 1") + parts[i][end_span_idx:]
    
    custom_sidebar = '<a class="'.join(parts)
    
    # Replace the sidebar in the file
    new_content = content[:current_sidebar_start] + custom_sidebar + content[current_sidebar_end:]
    filepath.write_text(new_content, encoding="utf-8")
    print(f"Updated sidebar active state for {filename}")

print("Done syncing sidebars!")
