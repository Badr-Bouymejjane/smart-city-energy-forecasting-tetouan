import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\index.html")
html = html_path.read_text(encoding="utf-8")

# 1. Fix the CSS Grid Layout to be more spacious
html = html.replace('class="grid grid-cols-1 lg:grid-cols-5 gap-gutter items-start"', 'class="grid grid-cols-1 xl:grid-cols-2 gap-gutter items-start"')
html = html.replace('class="lg:col-span-2 flex flex-col gap-md"', 'class="flex flex-col gap-md w-full"')
html = html.replace('class="lg:col-span-3 flex flex-col gap-lg"', 'class="flex flex-col gap-lg w-full"')

# 2. Clean up the extra HTML garbage that was messing up the layout
garbage = """
<div class="font-headline-md text-headline-md text-on-surface mt-xs">Zone Industrielle</div>
<div class="font-body-sm text-body-sm text-secondary mt-xs flex items-center gap-xs">
<span class="w-2 h-2 rounded-full bg-secondary pulse-green block"></span>
                                Load: 28 MW (Stable)
                            </div>
</div>
<span class="material-symbols-outlined text-secondary text-3xl" style="font-variation-settings: 'FILL' 1;">check_circle</span>
</div>
"""
html = html.replace(garbage.strip(), "")

# 3. Add IDs for JS Interactivity to the Impact Tracker
# Replace "Campaign Active: 2,405 Citizens Responding" with an ID
html = html.replace("Campaign Active: 2,405 Citizens Responding", '<span id="citizensCount">Ready to Launch</span>')
html = html.replace('3.2 MW <span class="text-2xl">↓</span>', '<span id="mwReduced">0.0</span> MW <span class="text-2xl" id="arrowIcon" style="display:none;">↓</span>')
html = html.replace('style="width: 45%;"', 'id="impactProgressBar" style="width: 0%;"')
html = html.replace("Target: 5.0 MW Reduction", '<span id="targetReduction">Target: -- MW Reduction</span>')

# Add IDs to Button and Select
html = html.replace('<button class="mt-sm bg-primary', '<button id="launchCampaignBtn" class="mt-sm bg-primary')
html = html.replace('<select class="w-full appearance-none', '<select id="zoneSelect" class="w-full appearance-none')


# 4. Inject Javascript Controller
js_injection = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("launchCampaignBtn");
    const citizensCount = document.getElementById("citizensCount");
    const mwReduced = document.getElementById("mwReduced");
    const progressBar = document.getElementById("impactProgressBar");
    const targetReduction = document.getElementById("targetReduction");
    const zoneSelect = document.getElementById("zoneSelect");
    const arrowIcon = document.getElementById("arrowIcon");
    
    let isCampaignRunning = false;
    
    btn.addEventListener("click", function() {
        if (isCampaignRunning) return;
        isCampaignRunning = true;
        
        // Change button state
        const originalText = btn.innerHTML;
        btn.innerHTML = `<span class="material-symbols-outlined animate-spin">sync</span> Launching...`;
        btn.classList.add("opacity-80");
        
        setTimeout(() => {
            btn.innerHTML = `<span class="material-symbols-outlined">check_circle</span> Campaign Active`;
            btn.classList.remove("bg-primary");
            btn.classList.add("bg-secondary");
            
            startSimulation();
        }, 800);
    });
    
    function startSimulation() {
        // Reset
        let currentCitizens = 0;
        let currentMw = 0.0;
        arrowIcon.style.display = "inline-block";
        
        // Target based on zone
        let targetMwVal = 5.0;
        if(zoneSelect.value === "all") targetMwVal = 12.5;
        
        targetReduction.innerText = `Target: ${targetMwVal.toFixed(1)} MW Reduction`;
        
        const duration = 5000; // 5 seconds simulation
        const steps = 50;
        const intervalTime = duration / steps;
        
        let step = 0;
        const interval = setInterval(() => {
            step++;
            
            // Non-linear easing for realistic feel
            const progress = step / steps;
            const easeOutProgress = 1 - Math.pow(1 - progress, 3); 
            
            currentCitizens = Math.floor(easeOutProgress * (targetMwVal * 800)); // ~800 citizens per MW
            currentMw = easeOutProgress * targetMwVal;
            
            citizensCount.innerText = `Campaign Active: ${currentCitizens.toLocaleString()} Citizens Responding`;
            mwReduced.innerText = currentMw.toFixed(1);
            progressBar.style.width = `${(currentMw / targetMwVal) * 100}%`;
            
            if (step >= steps) {
                clearInterval(interval);
            }
        }, intervalTime);
    }
});
</script>
</body>
"""

if "function startSimulation" not in html:
    html = html.replace("</body>", js_injection)
    html_path.write_text(html, encoding="utf-8")
    print("Successfully fixed layout and injected JS into index.html")
else:
    print("JS already injected.")
