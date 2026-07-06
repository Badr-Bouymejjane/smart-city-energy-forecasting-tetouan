import os
import re
from pathlib import Path

templates_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates")

file_to_href = {
    "index.html": "/",
    "models.html": "/models",
    "xgboost_details.html": "/models/xgboost",
    "data.html": "/data",
    "correlations.html": "/correlations",
    "analytics.html": "/correlations",
    "citizen.html": "/citizen"
}

sidebar_template = """<aside class="hidden md:flex flex-col h-screen w-64 fixed left-0 top-0 bg-surface-container-low dark:bg-surface-dim border-r border-outline-variant dark:border-outline p-md z-50">
<div class="flex items-center gap-sm mb-xl px-sm">
<div>
<h1 class="font-headline-md text-headline-md font-bold text-primary">Nexus Tetouan</h1>
<p class="font-label-sm text-label-sm text-on-surface-variant">Energy Management</p>
</div>
</div>
<nav class="flex-1 flex flex-col gap-xs">
<a class="LINK_CLASSES" href="/" data-href="/">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' ICON_FILL;">dashboard</span>
<span class="font-label-md text-label-md">Dashboard</span>
</a>
<a class="LINK_CLASSES" href="/models" data-href="/models">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' ICON_FILL;">compare_arrows</span>
<span class="font-label-md text-label-md">Model Comparison</span>
</a>

<a class="LINK_CLASSES" href="/data" data-href="/data">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' ICON_FILL;">history</span>
<span class="font-label-md text-label-md">Historical Data</span>
</a>
<a class="LINK_CLASSES" href="/correlations" data-href="/correlations">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' ICON_FILL;">ssid_chart</span>
<span class="font-label-md text-label-md">Correlations</span>
</a>
<a class="LINK_CLASSES" href="/citizen" data-href="/citizen">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' ICON_FILL;">nature_people</span>
<span class="font-label-md text-label-md">Citizen Hub</span>
</a>
</nav>
<button class="w-full bg-surface-container-high text-primary font-label-md text-label-md py-sm rounded-lg mt-auto hover:bg-surface-container-highest transition-colors flex items-center justify-center gap-sm">
<span class="material-symbols-outlined text-sm">download</span>
Export Report
</button>
</aside>"""

active_cls = "flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all"
inactive_cls = "flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all"

for filename, active_href in file_to_href.items():
    filepath = templates_dir / filename
    if not filepath.exists():
        continue
    
    content = filepath.read_text(encoding="utf-8")
    
    # Identify the sidebar bounds:
    # It might be <aside> or <nav> and end with </aside> or </nav>
    # In index.html, it's <aside ... </aside>
    # In models.html, it's <nav class="hidden md:flex h-screen w-64 ... </nav>
    
    # We will use regex to find it. The sidebar is the FIRST block that has w-64 and h-screen and hidden md:flex
    # Actually, simpler: replace <aside>...</aside> OR <nav>...</nav> that contains Nexus Tetouan
    
    # Find start: <aside or <nav class="hidden md:flex h-screen w-64
    match = re.search(r'<(?:aside|nav)[^>]*w-64[^>]*>', content)
    if not match:
        print(f"Skipping {filename}, no sidebar found.")
        continue
        
    start_idx = match.start()
    
    # Find matching closing tag
    tag_name = "aside" if "<aside" in match.group(0) else "nav"
    end_idx = content.find(f'</{tag_name}>', start_idx) + len(f'</{tag_name}>')
    
    # Now build the customized sidebar for this page
    custom_sb = sidebar_template
    # We split by 'data-href="' and replace correctly
    parts = custom_sb.split('data-href="')
    for i in range(1, len(parts)):
        href = parts[i].split('"')[0]
        if href == active_href:
            parts[i] = parts[i].replace('LINK_CLASSES', active_cls).replace('ICON_FILL', '1')
        else:
            parts[i] = parts[i].replace('LINK_CLASSES', inactive_cls).replace('ICON_FILL', '0')
    
    custom_sb = 'data-href="'.join(parts)
    # Remove the data-href tags for clean HTML
    custom_sb = re.sub(r' data-href="[^"]+"', '', custom_sb)
    
    # In models.html and data.html, since we make the sidebar `fixed left-0 top-0`, the main content needs `md:ml-64`.
    # Let's ensure the main content wrapper has `md:ml-64`
    # In index.html: <div class="flex-1 md:ml-64 flex flex-col min-h-screen">
    # In models.html: <div class="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-background">
    new_content = content[:start_idx] + custom_sb + content[end_idx:]
    
    # Inject md:ml-64 to the flex-1 container immediately following the sidebar if it's missing
    # We look for `<div class="flex-1`
    flex_match = re.search(r'<div class="flex-1[^>]*>', new_content[start_idx:])
    if flex_match:
        flex_str = flex_match.group(0)
        if 'md:ml-64' not in flex_str:
            new_flex_str = flex_str.replace('flex-1', 'flex-1 md:ml-64')
            new_content = new_content[:start_idx + flex_match.start()] + new_flex_str + new_content[start_idx + flex_match.end():]
            
    filepath.write_text(new_content, encoding="utf-8")
    print(f"Standardized sidebar for {filename}")

print("Done standardizing all sidebars!")
