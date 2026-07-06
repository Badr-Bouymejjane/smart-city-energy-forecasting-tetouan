import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\models.html")
html = html_path.read_text(encoding="utf-8")

# Replace metrics
html = html.replace('>52,416<', '>{{ total_obs }}<')
html = html.replace('>8,760<', '>{{ hourly_aggs }}<')
html = html.replace('>01/01/2017<', '>{{ start_date }}<')
html = html.replace('>12/31/2022<', '>{{ end_date }}<')

# Replace Forecast text
html = html.replace('Alert: Peak Load Expected', '{{ xgb_alert }}')
html = html.replace('38.5 MW', '{{ xgb_forecast }} MW')

html = html.replace('Normal: Load Expected', '{{ rf_alert }}')
html = html.replace('34.2 MW', '{{ rf_forecast }} MW')

# Add ID to New Analysis Button
html = html.replace('<button class="w-full bg-primary text-on-primary font-label-md text-label-md py-sm px-md', '<button id="newAnalysisBtn" class="w-full bg-primary text-on-primary font-label-md text-label-md py-sm px-md')

# Inject Javascript for the New Analysis button
js_injection = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const btn = document.getElementById("newAnalysisBtn");
        if (btn) {
            btn.addEventListener("click", function() {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">sync</span> Initializing Pipeline...`;
                btn.classList.add("opacity-80");
                
                setTimeout(() => {
                    btn.innerHTML = `<span class="material-symbols-outlined text-[18px]">model_training</span> Training XGBoost...`;
                    
                    setTimeout(() => {
                        btn.innerHTML = `<span class="material-symbols-outlined text-[18px]">check_circle</span> Analysis Complete`;
                        btn.classList.remove("bg-primary");
                        btn.classList.add("bg-secondary");
                        
                        setTimeout(() => {
                            btn.innerHTML = originalHtml;
                            btn.classList.remove("bg-secondary", "opacity-80");
                            btn.classList.add("bg-primary");
                        }, 3000);
                        
                    }, 2000);
                }, 1500);
            });
        }
    });
</script>
</body>
"""

if "Initializing Pipeline" not in html:
    html = html.replace("</body>\n</html>", js_injection + "\n</html>")

html_path.write_text(html, encoding="utf-8")
print("Successfully injected dynamic variables and New Analysis JS into models.html")
