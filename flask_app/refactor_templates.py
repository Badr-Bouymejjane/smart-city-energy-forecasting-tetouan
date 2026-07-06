import os
import re
from pathlib import Path

templates_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates")

def refactor_file(filename, breadcrumb_html):
    filepath = templates_dir / filename
    if not filepath.exists():
        return
        
    content = filepath.read_text(encoding="utf-8")
    
    # We need to extract what's inside <main> or the core content div.
    # Usually, it's after the <header> tag inside the main wrapper.
    # Let's find the closing </header> tag.
    header_end = content.find('</header>')
    if header_end == -1:
        # Fallback: find <aside>, its closing tag, and take what's after
        aside_end = content.find('</aside>')
        if aside_end != -1:
            header_end = aside_end
        else:
            header_end = 0
            
    # The end of the file is usually </body></html>
    body_close = content.rfind('</body>')
    if body_close == -1:
        body_close = len(content)
        
    main_content = content[header_end+9:body_close].strip()
    
    # Remove the closing </div> of the flex-1 container if it's there
    if main_content.endswith('</div>'):
        main_content = main_content[:-6].strip()
        
    # Also extract scripts
    # Find any <script> at the bottom
    scripts = ""
    script_start = main_content.rfind('<script')
    if script_start != -1 and 'Chart.js' not in main_content[script_start:]:
        # if the script is at the very end
        scripts = main_content[script_start:]
        main_content = main_content[:script_start].strip()
        
    new_template = f"""{{% extends "base.html" %}}

{{% block breadcrumb %}}
{breadcrumb_html}
{{% endblock %}}

{{% block content %}}
{main_content}
{{% endblock %}}

{{% block scripts %}}
{scripts}
{{% endblock %}}
"""
    filepath.write_text(new_template, encoding="utf-8")
    print(f"Refactored {filename}")

refactor_file("index.html", '<span class="font-label-md text-label-md">City-Wide Ops</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">Live Dashboard</span>')
refactor_file("models.html", '<span class="font-label-md text-label-md">Nexus Tetouan</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">Model Comparison</span>')
refactor_file("xgboost_details.html", '<span class="font-label-md text-label-md">Model Comparison</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">XGBoost Detailed View</span>')
refactor_file("data.html", '<span class="font-label-md text-label-md">Nexus Tetouan</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">Historical Data</span>')
refactor_file("correlations.html", '<span class="font-label-md text-label-md">Nexus Tetouan</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">Environmental Correlations</span>')
refactor_file("settings.html", '<span class="font-label-md text-label-md">Nexus Tetouan</span><span class="material-symbols-outlined mx-1" style="font-size: 16px;">chevron_right</span><span class="font-label-md text-label-md text-primary">Settings</span>')
