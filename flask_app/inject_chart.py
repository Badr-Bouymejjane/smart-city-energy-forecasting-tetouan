import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\models.html")
html = html_path.read_text(encoding="utf-8")

# Inject Chart.js CDN into head if not exists
if "chart.js" not in html:
    html = html.replace("</head>", '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>')

# Define the replacement for the Chart Placeholder Area
chart_replacement = """
<!-- Chart Area -->
<div class="p-lg w-full h-[400px] relative bg-surface-bright flex items-center justify-center overflow-hidden">
    <canvas id="forecastChart" class="w-full h-full"></canvas>
</div>
"""

# Regex to find the Chart Placeholder Area and replace it
# The placeholder starts with: <!-- Chart Placeholder Area -->
# and ends right before </section>
pattern = re.compile(r'<!-- Chart Placeholder Area -->.*?</div>\s*</section>', re.DOTALL)
html = pattern.sub(chart_replacement + "\n</section>", html)

# Inject the initialization script just before </body>
script_injection = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const chartData = {{ chart_data|safe }};
        
        // Format the labels (datetime strings) to shorter time
        const labels = chartData.labels.map(ts => {
            const date = new Date(ts);
            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });
        
        const ctx = document.getElementById('forecastChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual Load',
                        data: chartData.actual,
                        borderColor: '#727687', // outline color
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    },
                    {
                        label: 'XGBoost',
                        data: chartData.xgboost,
                        borderColor: '#0050cb', // primary color
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    },
                    {
                        label: 'Random Forest',
                        data: chartData.random_forest,
                        borderColor: '#8b5cf6', // purple color
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
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
                    legend: {
                        display: false // We use the custom HTML legend above the chart
                    },
                    tooltip: {
                        backgroundColor: '#2d3133',
                        titleFont: { family: 'Inter', size: 14 },
                        bodyFont: { family: 'Inter', size: 14 },
                        padding: 12
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxTicksLimit: 8,
                            font: { family: 'Inter', size: 12 },
                            color: '#424656'
                        }
                    },
                    y: {
                        grid: { color: '#e0e3e5' },
                        border: { dash: [4, 4] },
                        ticks: {
                            font: { family: 'Inter', size: 12 },
                            color: '#424656',
                            callback: function(value) { return value + ' MW'; }
                        }
                    }
                }
            }
        });
    });
</script>
</body>
"""

if "id=\"forecastChart\"" not in html or "new Chart(ctx" not in html:
    html = html.replace("</body>", script_injection)

html_path.write_text(html, encoding="utf-8")
print("Successfully injected Chart.js into models.html")
