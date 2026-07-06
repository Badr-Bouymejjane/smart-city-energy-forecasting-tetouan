import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\settings.html")
html = html_path.read_text(encoding="utf-8")

# 1. Add IDs to the selects and inputs
html = html.replace('<select class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">', 
                    '<select id="langSelect" class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">', 1)

html = html.replace('<select class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">', 
                    '<select id="tzSelect" class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">', 1)

html = html.replace('<input class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-body-sm text-body-sm" type="text" value="https://api.nexustetouan.gov/v2/telemetry"/>',
                    '<input id="apiUrlInput" class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-body-sm text-body-sm" type="text" value="https://api.nexustetouan.gov/v2/telemetry"/>')

# 2. Inject LocalStorage Load Logic
load_logic = """
        // --- 0. Load Settings from LocalStorage ---
        const savedLang = localStorage.getItem('nexus_lang');
        if(savedLang && document.getElementById('langSelect')) document.getElementById('langSelect').value = savedLang;
        
        const savedTz = localStorage.getItem('nexus_tz');
        if(savedTz && document.getElementById('tzSelect')) document.getElementById('tzSelect').value = savedTz;
        
        const savedSlider = localStorage.getItem('nexus_loadSlider');
        if(savedSlider && document.getElementById('loadSlider')) {
            const slider = document.getElementById('loadSlider');
            slider.value = savedSlider;
            // update visuals
            if(document.getElementById('sliderValue')) document.getElementById('sliderValue').textContent = savedSlider + ' MW';
            if(document.getElementById('sliderProgress')) {
                const percent = (savedSlider / slider.max) * 100;
                document.getElementById('sliderProgress').style.width = percent + '%';
            }
        }
        
        const savedToggle1 = localStorage.getItem('nexus_toggle1');
        if(savedToggle1 !== null && document.getElementById('toggle1')) document.getElementById('toggle1').checked = savedToggle1 === 'true';
        
        const savedToggle2 = localStorage.getItem('nexus_toggle2');
        if(savedToggle2 !== null && document.getElementById('toggle2')) document.getElementById('toggle2').checked = savedToggle2 === 'true';
        
        const savedApiUrl = localStorage.getItem('nexus_apiUrl');
        if(savedApiUrl && document.getElementById('apiUrlInput')) document.getElementById('apiUrlInput').value = savedApiUrl;
        
        const savedApiKey = localStorage.getItem('nexus_apiKey');
        if(savedApiKey && document.getElementById('apiKeyInput')) document.getElementById('apiKeyInput').value = savedApiKey;
"""

# Insert load logic at the top of DOMContentLoaded
html = html.replace('document.addEventListener("DOMContentLoaded", function() {\n        // --- 1. Password Visibility Toggle ---', 'document.addEventListener("DOMContentLoaded", function() {\n' + load_logic + '\n        // --- 1. Password Visibility Toggle ---')

# 3. Update Save Button Logic to Write to LocalStorage
old_save_logic = """        // --- 2. Save Button Simulation ---
        const saveBtn = document.getElementById('saveSettingsBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                const originalHtml = this.innerHTML;
                this.innerHTML = `<span class="material-symbols-outlined text-sm mr-xs animate-spin">sync</span> Saving...`;
                this.classList.add("opacity-80");
                
                setTimeout(() => {
                    this.innerHTML = `<span class="material-symbols-outlined text-sm mr-xs">check</span> Saved Successfully`;
                    this.classList.remove("bg-primary");
                    this.classList.add("bg-secondary");
                    
                    setTimeout(() => {
                        this.innerHTML = originalHtml;
                        this.classList.remove("bg-secondary", "opacity-80");
                        this.classList.add("bg-primary");
                    }, 2500);
                }, 1000);
            });
        }"""

new_save_logic = """        // --- 2. Save Button Simulation & Storage ---
        const saveBtn = document.getElementById('saveSettingsBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                // Save to localStorage
                if(document.getElementById('langSelect')) localStorage.setItem('nexus_lang', document.getElementById('langSelect').value);
                if(document.getElementById('tzSelect')) localStorage.setItem('nexus_tz', document.getElementById('tzSelect').value);
                if(document.getElementById('loadSlider')) localStorage.setItem('nexus_loadSlider', document.getElementById('loadSlider').value);
                if(document.getElementById('toggle1')) localStorage.setItem('nexus_toggle1', document.getElementById('toggle1').checked);
                if(document.getElementById('toggle2')) localStorage.setItem('nexus_toggle2', document.getElementById('toggle2').checked);
                if(document.getElementById('apiUrlInput')) localStorage.setItem('nexus_apiUrl', document.getElementById('apiUrlInput').value);
                if(document.getElementById('apiKeyInput')) localStorage.setItem('nexus_apiKey', document.getElementById('apiKeyInput').value);

                const originalHtml = this.innerHTML;
                this.innerHTML = `<span class="material-symbols-outlined text-sm mr-xs animate-spin">sync</span> Saving...`;
                this.classList.add("opacity-80");
                
                setTimeout(() => {
                    this.innerHTML = `<span class="material-symbols-outlined text-sm mr-xs">check</span> Saved Successfully`;
                    this.classList.remove("bg-primary");
                    this.classList.add("bg-secondary");
                    
                    setTimeout(() => {
                        this.innerHTML = originalHtml;
                        this.classList.remove("bg-secondary", "opacity-80");
                        this.classList.add("bg-primary");
                    }, 2500);
                }, 1000);
            });
        }"""

html = html.replace(old_save_logic, new_save_logic)

html_path.write_text(html, encoding="utf-8")
print("Settings saving logic successfully injected!")
