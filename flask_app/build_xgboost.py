import os
from pathlib import Path

app_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app")
templates_dir = app_dir / "templates"
source_html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\nexus_tetouan\xgboost_performance_deep_dive\code.html")
index_html_path = templates_dir / "index.html"

# Read source and index
source_html = source_html_path.read_text(encoding="utf-8")
index_html = index_html_path.read_text(encoding="utf-8")

# Extract the header and sidebar from index.html
sidebar_start = index_html.find('<!-- SideNavBar -->')
main_content_start = index_html.find('<!-- Main Content Canvas -->')
index_sidebar = index_html[sidebar_start:main_content_start]

# Modify sidebar: make Model Comparison active
index_sidebar = index_sidebar.replace(
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all" href="/">',
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/">'
).replace("'FILL' 1;", "'FILL' 0;", 1)

index_sidebar = index_sidebar.replace(
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/models">',
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all" href="/models">'
).replace("'FILL' 0;", "'FILL' 1;")

# Extract main content
main_start = source_html.find('<main')
main_end = source_html.find('</main>') + len('</main>')
main_content = source_html[main_start:main_end]

# Extract TopAppBar
header_start = source_html.find('<header')
header_end = source_html.find('</header>') + len('</header>')
header_content = source_html[header_start:header_end]

# Combine
new_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XGBoost Performance - Nexus Tetouan</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    {index_html[index_html.find('<script id="tailwind-config">'):index_html.find('</script>', index_html.find('<script id="tailwind-config">'))+len('</script>')]}
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .ambient-shadow {{
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-background text-on-surface font-body-md min-h-screen flex">
{index_sidebar}
<div class="flex-1 md:ml-64 flex flex-col min-h-screen">
{header_content.replace('docked full-width top-0 sticky z-40', 'sticky top-0 z-40')}
<div class="p-lg max-w-container-max mx-auto w-full space-y-lg">
{main_content[main_content.find('<!-- Header Section -->'):]}
</div>
</div>
</body>
</html>
"""

# Replace Metrics
new_html = new_html.replace('>1.24<', '>{{ mae }}<')
new_html = new_html.replace('>1.85<', '>{{ rmse }}<')
new_html = new_html.replace('>2.1<', '>{{ mape }}<')

# Replace SVGs with canvases
residual_svg_start = new_html.find('<!-- Scatter Plot Mockup via SVG -->')
residual_svg_end = new_html.find('</div>\n</div>\n</div>\n<!-- Section 4:')
canvas_residual = """<!-- Chart.js Residuals Container -->
<div class="flex-1 w-full relative min-h-[200px] bg-surface-bright rounded-lg border border-surface-variant p-4">
    <canvas id="residualChart"></canvas>
"""
new_html = new_html[:residual_svg_start] + canvas_residual + new_html[residual_svg_end:]

forecast_svg_start = new_html.find('<!-- Line Chart Mockup via SVG -->')
forecast_svg_end = new_html.find('</div>\n</div>\n</main>')
canvas_forecast = """<!-- Chart.js Forecast Container -->
<div class="w-full h-72 relative mt-4">
    <canvas id="forecastChart"></canvas>
"""
new_html = new_html[:forecast_svg_start] + canvas_forecast + new_html[forecast_svg_end:]

# Inject JS logic
js_logic = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const rawData = {{ chart_data|safe }};
        
        // 1. Residuals Scatter Plot
        const resCtx = document.getElementById('residualChart').getContext('2d');
        const resData = rawData.residuals.map(r => ({ x: r.pred, y: r.res }));
        
        new Chart(resCtx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Residuals',
                    data: resData,
                    backgroundColor: 'rgba(0, 80, 203, 0.4)',
                    borderColor: '#0050cb',
                    borderWidth: 1,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        title: { display: true, text: 'Predicted Value (MW)' },
                        grid: { color: '#e0e3e5' }
                    },
                    y: {
                        title: { display: true, text: 'Residual (MW)' },
                        grid: { color: '#e0e3e5' },
                        suggestedMin: -5,
                        suggestedMax: 5
                    }
                }
            }
        });

        // 2. 24-Hour Forecast Breakdown
        const labels = rawData.labels.map(ts => {
            const date = new Date(ts);
            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });
        
        const fcCtx = document.getElementById('forecastChart').getContext('2d');
        new Chart(fcCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual Load (MW)',
                        data: rawData.actual,
                        borderColor: '#727687',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'XGBoost Predicted (MW)',
                        data: rawData.prediction,
                        borderColor: '#0050cb',
                        backgroundColor: 'rgba(0, 80, 203, 0.1)',
                        fill: true,
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        grid: { color: '#e0e3e5' },
                        suggestedMin: 20,
                        suggestedMax: 40
                    }
                }
            }
        });
    });
</script>
"""
new_html = new_html.replace('</body>', js_logic + '</body>')

# Handle the URL linking in models.html
models_html_path = templates_dir / "models.html"
models_html = models_html_path.read_text(encoding="utf-8")
# Find the XGBoost 'View Full Details' button/link and update it
models_html = models_html.replace('<button class="text-primary font-label-md text-label-md hover:underline">View Full Details</button>', '<a href="/models/xgboost" class="text-primary font-label-md text-label-md hover:underline">View Full Details</a>')

models_html_path.write_text(models_html, encoding="utf-8")
(templates_dir / "xgboost_details.html").write_text(new_html, encoding="utf-8")
print("xgboost_details.html created and models.html linked!")
