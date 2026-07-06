import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\settings.html")
html = html_path.read_text(encoding="utf-8")

# 1. Add IDs to the password input and toggle button
html = html.replace('type="password" value="sk_test_1234567890abcdef"/>', 'type="password" id="apiKeyInput" value="sk_test_1234567890abcdef"/>')
html = html.replace('<button class="absolute right-2 top-1/2 -translate-y-1/2 p-xs text-outline hover:text-primary transition-colors">', '<button id="togglePasswordBtn" class="absolute right-2 top-1/2 -translate-y-1/2 p-xs text-outline hover:text-primary transition-colors">')

# 2. Add ID to the Save button
html = html.replace('<button class="px-lg py-sm bg-primary text-on-primary font-label-md text-label-md rounded-md hover:bg-on-primary-fixed-variant shadow-sm transition-colors flex items-center">', '<button id="saveSettingsBtn" class="px-lg py-sm bg-primary text-on-primary font-label-md text-label-md rounded-md hover:bg-on-primary-fixed-variant shadow-sm transition-colors flex items-center relative overflow-hidden">')

# 3. Add IDs to sections for smooth scrolling
html = html.replace('<h3 class="font-headline-md text-headline-md text-on-surface">Threshold Configuration</h3>', '<h3 id="threshold-section" class="font-headline-md text-headline-md text-on-surface scroll-mt-24">Threshold Configuration</h3>')
html = html.replace('<h4 class="font-headline-sm text-headline-sm text-on-surface font-semibold mb-sm">API Integration Settings</h4>', '<h4 id="api-section" class="font-headline-sm text-headline-sm text-on-surface font-semibold mb-sm scroll-mt-24">API Integration Settings</h4>')

# 4. Update the Sidebar links to anchor to the sections
old_nav = """<nav class="space-y-sm">
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md" href="#">General</a>
<a class="block px-md py-sm rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md" href="#">Alert Thresholds</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md" href="#">API Integrations</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md" href="#">User Access</a>
</nav>"""

new_nav = """<nav class="space-y-sm" id="settingsNav">
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#threshold-section">General</a>
<a class="block px-md py-sm rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md nav-link" href="#threshold-section">Alert Thresholds</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#api-section">API Integrations</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#">User Access</a>
</nav>"""

html = html.replace(old_nav, new_nav)

# 5. Inject the Javascript Controller
js_injection = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        // --- 1. Password Visibility Toggle ---
        const togglePasswordBtn = document.getElementById('togglePasswordBtn');
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (togglePasswordBtn && apiKeyInput) {
            togglePasswordBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const type = apiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
                apiKeyInput.setAttribute('type', type);
                
                const icon = this.querySelector('span');
                if (type === 'text') {
                    icon.textContent = 'visibility_off';
                    this.classList.add('text-primary');
                } else {
                    icon.textContent = 'visibility';
                    this.classList.remove('text-primary');
                }
            });
        }

        // --- 2. Save Button Simulation ---
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
        }
        
        // --- 3. Sidebar Active State ---
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Remove active classes from all
                navLinks.forEach(l => {
                    l.classList.remove('bg-primary-container', 'text-on-primary-container');
                    l.classList.add('text-on-surface-variant');
                });
                // Add active to clicked
                this.classList.add('bg-primary-container', 'text-on-primary-container');
                this.classList.remove('text-on-surface-variant');
            });
        });
    });
</script>
"""

# Append just before the end of body, avoiding duplication
if "Password Visibility Toggle" not in html:
    html = html.replace("</body>", js_injection + "</body>")

html_path.write_text(html, encoding="utf-8")
print("Successfully injected JS into settings.html")
