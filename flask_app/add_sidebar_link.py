import os
import re
from pathlib import Path

templates_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates")

new_link = """
<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/models/xgboost">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 0;">query_stats</span>
<span class="font-label-md text-label-md">XGBoost Details</span>
</a>"""

for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        filepath = templates_dir / filename
        content = filepath.read_text(encoding="utf-8")
        
        # Check if already has XGBoost Details in sidebar
        if "XGBoost Details" in content:
            continue
            
        # The Model Comparison link usually ends with:
        # <span class="font-label-md text-label-md">Model Comparison</span>
        # </a>
        
        # We find the </a> after Model Comparison
        # Regex to find Model Comparison span and its closing </a>
        pattern = r'(<span[^>]*>Model Comparison</span>\s*</a>)'
        
        # To make it active if we are in xgboost_details.html
        if filename == "xgboost_details.html":
            active_link = new_link.replace('text-on-surface-variant', 'text-primary font-bold bg-surface-container-highest').replace('hover:text-primary', '').replace('FILL\' 0', 'FILL\' 1')
            content = re.sub(pattern, r'\1' + active_link, content)
        else:
            content = re.sub(pattern, r'\1' + new_link, content)
            
        filepath.write_text(content, encoding="utf-8")
        print(f"Updated {filename}")
