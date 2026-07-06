import os
import re
from pathlib import Path

templates_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates")

# Read index.html to grab the head and standard imports
index_content = (templates_dir / "index.html").read_text(encoding="utf-8")

# Extract the <head> block
head_match = re.search(r'(<head>.*?</head>)', index_content, flags=re.DOTALL)
head_content = head_match.group(1)

# Base template HTML
base_html = f"""<!DOCTYPE html>
<html lang="en">
{head_content}
<body class="bg-background text-on-surface font-body-md antialiased overflow-hidden flex h-screen">

<!-- SideNavBar -->
<aside class="hidden md:flex flex-col h-screen w-64 fixed left-0 top-0 bg-surface-container-low dark:bg-surface-dim border-r border-outline-variant dark:border-outline p-md z-50">
    <div class="flex items-center gap-sm mb-xl px-sm">
        <div>
            <h1 class="font-headline-md text-headline-md font-bold text-primary">Nexus Tetouan</h1>
            <p class="font-label-sm text-label-sm text-on-surface-variant">Energy Management</p>
        </div>
    </div>
    <nav class="flex-1 flex flex-col gap-xs">
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/' else '0' }};">dashboard</span>
            <span class="font-label-md text-label-md">Dashboard</span>
        </a>
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/models' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/models">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/models' else '0' }};">compare_arrows</span>
            <span class="font-label-md text-label-md">Model Comparison</span>
        </a>
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/models/xgboost' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/models/xgboost">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/models/xgboost' else '0' }};">query_stats</span>
            <span class="font-label-md text-label-md">XGBoost Details</span>
        </a>
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/data' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/data">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/data' else '0' }};">history</span>
            <span class="font-label-md text-label-md">Historical Data</span>
        </a>
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/correlations' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/correlations">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/correlations' else '0' }};">ssid_chart</span>
            <span class="font-label-md text-label-md">Correlations</span>
        </a>
        <a class="{{ 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all' if request.path == '/settings' else 'flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all' }}" href="/settings">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {{ '1' if request.path == '/settings' else '0' }};">settings</span>
            <span class="font-label-md text-label-md">Settings</span>
        </a>
    </nav>
    <button class="w-full bg-surface-container-high text-primary font-label-md text-label-md py-sm rounded-lg mt-auto hover:bg-surface-container-highest transition-colors flex items-center justify-center gap-sm">
        <span class="material-symbols-outlined text-sm">download</span>
        Export Report
    </button>
</aside>

<!-- Main Layout Wrapper -->
<div class="flex-1 md:ml-64 flex flex-col min-h-screen min-w-0 bg-background overflow-y-auto">
    
    <!-- Unified Top Header -->
    <header class="w-full h-16 bg-surface-container-lowest shadow-sm flex justify-between items-center px-lg z-10 flex-shrink-0 sticky top-0">
        <div class="flex items-center gap-lg">
            <!-- Mobile Menu Toggle -->
            <button class="md:hidden text-on-surface-variant">
                <span class="material-symbols-outlined">menu</span>
            </button>
            
            <!-- Breadcrumbs Area -->
            <div class="hidden md:flex items-center text-sm text-on-surface-variant">
                {{% block breadcrumb %}}
                <span class="font-label-md text-label-md">Nexus Tetouan</span>
                {{% endblock %}}
            </div>
        </div>
        
        <!-- Right side actions -->
        <div class="flex items-center gap-sm">
            <div class="hidden lg:flex items-center bg-surface-container-low rounded-full px-md py-xs border border-outline-variant/50 focus-within:border-primary transition-colors mr-4">
                <span class="material-symbols-outlined text-on-surface-variant text-[20px]">search</span>
                <input class="bg-transparent border-none focus:ring-0 text-body-sm font-body-sm text-on-surface w-64 placeholder:text-on-surface-variant/70" placeholder="Search operations..." type="text">
            </div>
            
            <button class="p-2 rounded-full text-on-surface-variant hover:text-primary-container hover:bg-surface-container transition-all">
                <span class="material-symbols-outlined">notifications</span>
            </button>
            <button class="p-2 rounded-full text-on-surface-variant hover:text-primary-container hover:bg-surface-container transition-all">
                <span class="material-symbols-outlined">help</span>
            </button>
            <div class="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm ml-2">
                A
            </div>
        </div>
    </header>

    <!-- Page Content -->
    {{% block content %}}
    {{% endblock %}}

</div>
<!-- End Main Layout Wrapper -->

<!-- Scripts -->
{{% block scripts %}}
{{% endblock %}}

</body>
</html>
"""

# Write base.html
(templates_dir / "base.html").write_text(base_html, encoding="utf-8")
print("Created base.html")

# Define how to extract content from each file
files_to_refactor = [
    "index.html", "models.html", "xgboost_details.html", 
    "data.html", "correlations.html", "settings.html", "analytics.html"
]

for filename in files_to_refactor:
    filepath = templates_dir / filename
    if not filepath.exists():
        continue
        
    content = filepath.read_text(encoding="utf-8")
    
    # In each file, the main content is usually inside a <main> tag or inside a div that follows the <header> or <aside>.
    # Instead of fragile regex, we'll manually look for the core content wrapper.
    # In index.html, it's inside `<main class="p-gutter...`
    # In models.html, it's inside `<main class="flex-1 overflow-y-auto p-lg...`
    # In xgboost_details.html, it's `<div class="p-lg max-w-container-max mx-auto w-full space-y-lg">`
    # We will just write a specific extractor for each known file, to be perfectly safe.
    print(f"File {filename} needs manual or specific extraction.")
