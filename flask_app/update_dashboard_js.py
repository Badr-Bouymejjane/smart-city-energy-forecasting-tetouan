import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\index.html")
html = html_path.read_text(encoding="utf-8")

# 1. Fix the Select options
old_select = """<select id="zoneSelect" class="w-full appearance-none bg-surface-container-lowest border border-outline-variant text-on-surface font-body-md rounded-lg pl-md pr-xl py-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none">
<option value="zone2">Target: Zone 2 Residents Only</option>
<option value="all">City-Wide Broadcast</option>
</select>"""

new_select = """<select id="zoneSelect" class="w-full appearance-none bg-surface-container-lowest border border-outline-variant text-on-surface font-body-md rounded-lg pl-md pr-xl py-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none">
<option value="zone1">Target: Zone 1 Residents Only</option>
<option value="zone2" selected>Target: Zone 2 Residents Only</option>
<option value="zone3">Target: Zone 3 Residents Only</option>
<option value="all">City-Wide Broadcast</option>
</select>"""

html = html.replace(old_select, new_select)

# 2. Rewrite the Javascript to allow resetting
# Find the start and end of the script block we injected previously
script_start = html.find('<script>\ndocument.addEventListener("DOMContentLoaded", function() {')
script_end = html.find('</script>\n</body>') + len('</script>')

if script_start != -1 and script_end != -1:
    old_script = html[script_start:script_end]
    
    new_script = """<script>
document.addEventListener("DOMContentLoaded", function() {
    const btn = document.getElementById("launchCampaignBtn");
    const citizensCount = document.getElementById("citizensCount");
    const mwReduced = document.getElementById("mwReduced");
    const progressBar = document.getElementById("impactProgressBar");
    const targetReduction = document.getElementById("targetReduction");
    const zoneSelect = document.getElementById("zoneSelect");
    const arrowIcon = document.getElementById("arrowIcon");
    
    let isCampaignRunning = false;
    let simulationInterval = null;
    
    function resetSimulation() {
        isCampaignRunning = false;
        clearInterval(simulationInterval);
        
        // Reset button UI
        btn.innerHTML = `<span class="material-symbols-outlined group-hover:scale-110 transition-transform">rocket_launch</span> Launch Citizen Challenge Campaign`;
        btn.classList.remove("bg-secondary", "bg-error", "opacity-80");
        btn.classList.add("bg-primary");
        
        // Reset progress UI
        citizensCount.innerText = `Ready to Launch`;
        mwReduced.innerText = `0.0`;
        progressBar.style.width = `0%`;
        arrowIcon.style.display = "none";
        
        let targetMwVal = 5.0;
        if(zoneSelect.value === "all") targetMwVal = 12.5;
        targetReduction.innerText = `Target: ${targetMwVal.toFixed(1)} MW Reduction`;
    }
    
    // When changing target, reset everything so we can launch again
    zoneSelect.addEventListener("change", resetSimulation);
    
    // Allow clicking button to STOP campaign if already running
    btn.addEventListener("click", function() {
        if (isCampaignRunning) {
            resetSimulation();
            return;
        }
        
        isCampaignRunning = true;
        
        // Change button state to launching
        btn.innerHTML = `<span class="material-symbols-outlined animate-spin">sync</span> Launching...`;
        btn.classList.add("opacity-80");
        
        setTimeout(() => {
            // Change button state to Active / Stop
            btn.innerHTML = `<span class="material-symbols-outlined">stop_circle</span> Stop Campaign`;
            btn.classList.remove("bg-primary");
            btn.classList.add("bg-error"); // Make it red to indicate "Stop"
            
            startSimulation();
        }, 800);
    });
    
    function startSimulation() {
        let currentCitizens = 0;
        let currentMw = 0.0;
        arrowIcon.style.display = "inline-block";
        
        let targetMwVal = 5.0;
        if(zoneSelect.value === "all") targetMwVal = 12.5;
        if(zoneSelect.value === "zone1") targetMwVal = 4.2;
        if(zoneSelect.value === "zone3") targetMwVal = 3.8;
        
        targetReduction.innerText = `Target: ${targetMwVal.toFixed(1)} MW Reduction`;
        
        const duration = 5000; 
        const steps = 50;
        const intervalTime = duration / steps;
        
        let step = 0;
        simulationInterval = setInterval(() => {
            step++;
            
            const progress = step / steps;
            const easeOutProgress = 1 - Math.pow(1 - progress, 3); 
            
            currentCitizens = Math.floor(easeOutProgress * (targetMwVal * 800));
            currentMw = easeOutProgress * targetMwVal;
            
            citizensCount.innerText = `Campaign Active: ${currentCitizens.toLocaleString()} Citizens Responding`;
            mwReduced.innerText = currentMw.toFixed(1);
            progressBar.style.width = `${(currentMw / targetMwVal) * 100}%`;
            
            if (step >= steps) {
                clearInterval(simulationInterval);
            }
        }, intervalTime);
    }
});
</script>"""
    
    html = html.replace(old_script, new_script)
    html_path.write_text(html, encoding="utf-8")
    print("Successfully updated Javascript and Dropdown in index.html")
else:
    print("Could not find the script block to replace.")
