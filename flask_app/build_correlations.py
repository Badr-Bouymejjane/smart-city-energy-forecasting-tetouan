import os
from pathlib import Path

app_dir = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app")
templates_dir = app_dir / "templates"
source_html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\nexus_tetouan\environmental_correlation_analysis\code.html")
index_html_path = templates_dir / "index.html"

# Read source and index
source_html = source_html_path.read_text(encoding="utf-8")
index_html = index_html_path.read_text(encoding="utf-8")

# 1. Create correlations.html by taking the head/body of code.html, but substituting the sidebar

# Extract the header and sidebar from index.html to use as our base
sidebar_start = index_html.find('<!-- SideNavBar -->')
main_content_start = index_html.find('<!-- Main Content Canvas -->')
index_sidebar = index_html[sidebar_start:main_content_start]

# We need to add "Correlations" to the index_sidebar before inserting it
new_link = """
<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/correlations">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 0;">ssid_chart</span>
<span class="font-label-md text-label-md">Correlations</span>
</a>
"""

# Modify the sidebar to make Correlations active and Dashboard inactive (when we paste it into correlations.html)
correlations_sidebar = index_sidebar.replace(
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all" href="/">',
    '<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/">'
)
correlations_sidebar = correlations_sidebar.replace('</nav>', new_link.replace('text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all', 'text-primary dark:text-primary-fixed font-bold bg-surface-container-highest dark:bg-surface-container-high transition-all').replace("'FILL' 0;", "'FILL' 1;") + '</nav>')


# Now extract the main content from code.html
main_start = source_html.find('<main class="')
main_end = source_html.find('</main>') + len('</main>')
main_content = source_html[main_start:main_end]

# Extract the top navbar from code.html
header_start = source_html.find('<header')
header_end = source_html.find('</header>') + len('</header>')
header_content = source_html[header_start:header_end]

# Combine
new_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environmental Correlation - Nexus Tetouan</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    {index_html[index_html.find('<script id="tailwind-config">'):index_html.find('</script>', index_html.find('<script id="tailwind-config">'))+len('</script>')]}
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .shadow-L1 {{ box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03); }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-background text-on-background font-body-md min-h-screen flex">
{correlations_sidebar}
<div class="flex-1 md:ml-64 flex flex-col min-h-screen">
{header_content.replace('md:w-[calc(100%-16rem)]', 'w-full')}
<div class="pt-[88px] px-md w-full">
{main_content}
</div>
</div>
</body>
</html>
"""

# Replace the static numbers with Jinja variables
new_html = new_html.replace('>24°C<', '>{{ avg_temp }}°C<')
new_html = new_html.replace('>65%<', '>{{ avg_hum }}%<')
new_html = new_html.replace('>12 km/h<', '>{{ avg_wind }} km/h<')

# Replace the SVG chart with a canvas
svg_start = new_html.find('<!-- Faux Chart Container -->')
svg_end = new_html.find('</div>\n<!-- Footer Insight -->')
canvas_html = """<!-- Chart Container -->
<div class="relative w-full h-80 bg-white border border-outline-variant/20 rounded-lg p-md">
    <canvas id="envChart"></canvas>
</div>
"""
new_html = new_html[:svg_start] + canvas_html + new_html[svg_end:]

# Inject Chart.js logic
js_logic = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const rawData = {{ chart_data|safe }};
        
        const labels = rawData.labels.map(ts => {
            const date = new Date(ts);
            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });
        
        const ctx = document.getElementById('envChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Energy Load (MW)',
                        data: rawData.load,
                        borderColor: '#006e2a',
                        borderDash: [5, 5],
                        yAxisID: 'y1',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: 'Temperature (°C)',
                        data: rawData.temp,
                        borderColor: '#FACC15',
                        yAxisID: 'y',
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0
                    },
                    {
                        label: 'Humidity (%)',
                        data: rawData.hum,
                        borderColor: '#3B82F6',
                        yAxisID: 'y',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: 'Wind (km/h)',
                        data: rawData.wind,
                        borderColor: '#14B8A6',
                        yAxisID: 'y',
                        tension: 0.4,
                        borderWidth: 2,
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
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Weather (°C, %, km/h)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Energy Load (MW)' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    });
</script>
"""
new_html = new_html.replace('</body>', js_logic + '</body>')

(templates_dir / "correlations.html").write_text(new_html, encoding="utf-8")
print("correlations.html created successfully.")

# 2. Update sidebars in existing HTML files (index.html, models.html, data.html, settings.html)
files_to_update = ["index.html", "models.html", "data.html", "settings.html"]

for fname in files_to_update:
    fpath = templates_dir / fname
    if not fpath.exists(): continue
    
    html_content = fpath.read_text(encoding="utf-8")
    
    # We want to insert the Correlations link right after Historical Data
    insert_point = html_content.find('<span class="font-label-md text-label-md">Historical Data</span>\n</a>')
    if insert_point != -1:
        insert_point += len('<span class="font-label-md text-label-md">Historical Data</span>\n</a>')
        
        # Determine if it's the `settings.html` sidebar (which has different styling) or the standard one
        if fname == "settings.html":
            link_to_insert = """\n<a class="flex items-center px-md py-sm rounded-lg hover:bg-surface-container-low dark:hover:bg-surface-container-highest transition-colors text-tertiary dark:text-tertiary-fixed-dim active:scale-95 duration-150" href="/correlations">
<span class="material-symbols-outlined mr-md">ssid_chart</span>
<span class="font-label-md text-label-md">Correlations</span>
</a>"""
        else:
            link_to_insert = """\n<a class="flex items-center gap-md px-md py-sm rounded-lg mb-xs text-on-surface-variant dark:text-outline-variant hover:text-primary dark:hover:text-primary-fixed-dim hover:bg-surface-container-high transition-all" href="/correlations">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 0;">ssid_chart</span>
<span class="font-label-md text-label-md">Correlations</span>
</a>"""

        if "/correlations" not in html_content:
            html_content = html_content[:insert_point] + link_to_insert + html_content[insert_point:]
            fpath.write_text(html_content, encoding="utf-8")
            print(f"Updated sidebar in {fname}")

