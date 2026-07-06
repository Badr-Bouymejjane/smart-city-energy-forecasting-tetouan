import os
import shutil
import re
from pathlib import Path

workspace_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan")
nexus_dir = workspace_dir / "nexus_tetouan"
flask_dir = workspace_dir / "flask_app"
templates_dir = flask_dir / "templates"
static_dir = flask_dir / "static"

# Create directories
templates_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

# File mappings
file_mappings = {
    "targeted_intervention_citizen_response_panel": "index.html",
    "environmental_correlation_analysis": "analytics.html",
    "xgboost_vs._random_forest_comparison": "models.html",
    "historical_data_explorer": "data.html",
    "command_center_settings": "settings.html"
}

# The navigation links to replace
# We use regex to find the labels and replace their hrefs
nav_replacements = {
    r'(<span[^>]*>Dashboard</span>)': '/',
    r'(<span[^>]*>Model Comparison</span>)': '/models',
    r'(<span[^>]*>Historical Data</span>)': '/data',
    r'(<span[^>]*>Correlations.*?</span>)': '/analytics',
    r'(<span[^>]*>Settings</span>)': '/settings',
}

def fix_links(html_content):
    # This is a bit tricky because the href="#" is on the <a> tag wrapping the span.
    # It's better to replace all `<a class="... flex items-center ... href="#"` dynamically.
    # Let's just find the `href="#"` closest to the specific spans, or hardcode the replacements
    # since we know the HTML structure.
    
    # Dashboard
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>dashboard</span>\s*<span[^>]*>Dashboard</span>)', r'href="/"', html_content)
    # Model Comparison
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>compare_arrows</span>\s*<span[^>]*>Model Comparison</span>)', r'href="/models"', html_content)
    # Historical Data
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>history</span>\s*<span[^>]*>Historical Data</span>)', r'href="/data"', html_content)
    # Analytics / Correlations (Wait, some files might call it different things. Let's look for icon 'analytics' or 'monitoring')
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>analytics</span>\s*<span[^>]*>Correlations& Analytics</span>)', r'href="/analytics"', html_content)
    # Some might just say "Correlations"
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>analytics</span>\s*<span[^>]*>Correlations</span>)', r'href="/analytics"', html_content)
    # Settings
    html_content = re.sub(r'href="[^"]*"(?=>\s*<span[^>]*>settings</span>\s*<span[^>]*>Settings</span>)', r'href="/settings"', html_content)

    return html_content

for stitch_folder, template_name in file_mappings.items():
    source_html = nexus_dir / stitch_folder / "code.html"
    dest_html = templates_dir / template_name
    
    if source_html.exists():
        content = source_html.read_text(encoding='utf-8')
        content = fix_links(content)
        dest_html.write_text(content, encoding='utf-8')
        print(f"Copied and fixed {stitch_folder} -> {template_name}")
    else:
        print(f"Warning: Could not find {source_html}")

# Write app.py
app_py_content = """from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/models")
def models():
    return render_template("models.html")

@app.route("/data")
def data():
    return render_template("data.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
"""

(flask_dir / "app.py").write_text(app_py_content, encoding='utf-8')

# Write requirements.txt
req_content = """flask>=3.0.0
pandas>=2.1.3
xgboost>=2.0.0
scikit-learn>=1.3.2
"""
(flask_dir / "requirements.txt").write_text(req_content, encoding='utf-8')

print("Flask app scaffolded successfully!")
