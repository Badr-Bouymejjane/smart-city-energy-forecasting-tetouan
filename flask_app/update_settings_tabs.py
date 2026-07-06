import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\settings.html")
html = html_path.read_text(encoding="utf-8")

# Let's extract the main panel content to wrap them in tabs
# The sections are currently just stacked.
# First, let's find the sidebar nav and replace it to use data-targets
old_nav = """<nav class="space-y-sm" id="settingsNav">
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#threshold-section">General</a>
<a class="block px-md py-sm rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md nav-link" href="#threshold-section">Alert Thresholds</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#api-section">API Integrations</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link" href="#">User Access</a>
</nav>"""

new_nav = """<nav class="space-y-sm" id="settingsNav">
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link cursor-pointer" data-target="tab-general">General</a>
<a class="block px-md py-sm rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md nav-link cursor-pointer" data-target="tab-thresholds">Alert Thresholds</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link cursor-pointer" data-target="tab-api">API Integrations</a>
<a class="block px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-low transition-colors font-label-md text-label-md nav-link cursor-pointer" data-target="tab-users">User Access</a>
</nav>"""

html = html.replace(old_nav, new_nav)

# Now let's restructure the content area
# I'll replace everything from `<div class="bg-surface-container-lowest rounded-xl` to `<div class="fixed bottom-0`

start_marker = '<div class="bg-surface-container-lowest rounded-xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.05),0_2px_4px_-2px_rgba(0,0,0,0.03)] p-lg border border-surface-container-low flex-1">'
end_marker = '<!-- Sticky Bottom Action Bar -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = """<div class="bg-surface-container-lowest rounded-xl shadow-[0_4px_6px_-1px_rgba(0,0,0,0.05),0_2px_4px_-2px_rgba(0,0,0,0.03)] p-lg border border-surface-container-low flex-1 relative min-h-[400px]">

<!-- TAB: GENERAL -->
<div id="tab-general" class="tab-content hidden animate-fade-in space-y-xl">
    <div class="mb-lg pb-md border-b border-surface-container-low">
        <h3 class="font-headline-md text-headline-md text-on-surface">General Settings</h3>
        <p class="font-body-sm text-body-sm text-tertiary mt-xs">System preferences and regional settings.</p>
    </div>
    <section class="space-y-md">
        <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant mb-xs">System Language</label>
            <select class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">
                <option>English (US)</option>
                <option>French (FR)</option>
                <option>Arabic (AR)</option>
            </select>
        </div>
        <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant mb-xs">Timezone</label>
            <select class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm">
                <option>Africa/Casablanca (GMT+1)</option>
                <option>UTC (GMT+0)</option>
            </select>
        </div>
    </section>
</div>

<!-- TAB: THRESHOLDS -->
<div id="tab-thresholds" class="tab-content block animate-fade-in space-y-xl">
    <div class="mb-lg pb-md border-b border-surface-container-low">
        <h3 class="font-headline-md text-headline-md text-on-surface">Threshold Configuration</h3>
        <p class="font-body-sm text-body-sm text-tertiary mt-xs">Define operational limits and automated response triggers.</p>
    </div>
    
    <section>
        <div class="flex justify-between items-center mb-md">
            <label class="font-label-md text-label-md text-on-surface">Critical Load Limit (MW)</label>
            <span class="font-label-md text-label-md text-primary bg-primary-fixed px-sm py-xs rounded" id="sliderValue">750 MW</span>
        </div>
        <div class="relative w-full">
            <input class="w-full h-2 bg-surface-container-highest rounded-lg appearance-none cursor-pointer" id="loadSlider" max="1000" min="0" type="range" value="750"/>
            <div class="absolute -z-10 top-1 left-0 h-1 bg-primary rounded-l-lg pointer-events-none" id="sliderProgress" style="width: 75%;"></div>
        </div>
        <div class="flex justify-between text-label-sm font-label-sm text-outline mt-sm">
            <span>0</span>
            <span>500</span>
            <span>1000</span>
        </div>
    </section>
    
    <section class="space-y-md">
        <div class="flex items-center justify-between p-md bg-surface-container-low rounded-lg border border-surface-variant">
            <div>
                <h4 class="font-label-md text-label-md text-on-surface">Auto-Initiate Challenges</h4>
                <p class="font-body-sm text-body-sm text-tertiary text-sm mt-xs">Automatically deploy load reduction protocols when limits are breached.</p>
            </div>
            <div class="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                <input checked="" class="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer transition-all duration-300 z-10 top-0" id="toggle1" name="toggle" type="checkbox"/>
                <label class="toggle-label block overflow-hidden h-6 rounded-full bg-surface-container-highest cursor-pointer transition-colors duration-300" for="toggle1"></label>
            </div>
        </div>
        <div class="flex items-center justify-between p-md bg-surface-container-low rounded-lg border border-surface-variant">
            <div>
                <h4 class="font-label-md text-label-md text-on-surface">System Notifications</h4>
                <p class="font-body-sm text-body-sm text-tertiary text-sm mt-xs">Receive instant alerts for threshold anomalies.</p>
            </div>
            <div class="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                <input class="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-surface-variant appearance-none cursor-pointer transition-all duration-300 z-10 top-0" id="toggle2" name="toggle2" type="checkbox"/>
                <label class="toggle-label block overflow-hidden h-6 rounded-full bg-surface-container-highest cursor-pointer transition-colors duration-300" for="toggle2"></label>
            </div>
        </div>
    </section>
</div>

<!-- TAB: API INTEGRATIONS -->
<div id="tab-api" class="tab-content hidden animate-fade-in space-y-xl">
    <div class="mb-lg pb-md border-b border-surface-container-low">
        <h3 class="font-headline-md text-headline-md text-on-surface">API Integration Settings</h3>
        <p class="font-body-sm text-body-sm text-tertiary mt-xs">Manage your endpoints and authentication keys.</p>
    </div>
    
    <section class="space-y-md">
        <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant mb-xs">Primary Endpoint URL</label>
            <input class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-body-sm text-body-sm" type="text" value="https://api.nexustetouan.gov/v2/telemetry"/>
        </div>
        <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant mb-xs">API Authentication Key</label>
            <div class="relative">
                <input class="w-full border border-outline-variant rounded-md px-md py-sm bg-surface-bright text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-body-sm text-body-sm pr-10" type="password" id="apiKeyInput" value="sk_test_1234567890abcdef"/>
                <button id="togglePasswordBtn" class="absolute right-2 top-1/2 -translate-y-1/2 p-xs text-outline hover:text-primary transition-colors">
                    <span class="material-symbols-outlined text-sm">visibility</span>
                </button>
            </div>
        </div>
    </section>
</div>

<!-- TAB: USER ACCESS -->
<div id="tab-users" class="tab-content hidden animate-fade-in space-y-xl">
    <div class="mb-lg pb-md border-b border-surface-container-low">
        <h3 class="font-headline-md text-headline-md text-on-surface">User Access</h3>
        <p class="font-body-sm text-body-sm text-tertiary mt-xs">Manage roles and permissions for the dashboard.</p>
    </div>
    <div class="flex items-center justify-center p-xl border-2 border-dashed border-outline-variant rounded-lg bg-surface-container-low/50">
        <div class="text-center">
            <span class="material-symbols-outlined text-outline text-[48px] mb-md">group_add</span>
            <h4 class="font-headline-sm text-headline-sm text-on-surface mb-xs">No active invitations</h4>
            <p class="font-body-sm text-body-sm text-tertiary">You are currently the only Administrator on this account.</p>
            <button class="mt-md px-md py-sm bg-primary-container text-on-primary-container rounded font-label-md text-label-md">Invite Team Member</button>
        </div>
    </div>
</div>

</div>
</div>
"""
    html = html[:start_idx] + new_content + html[end_idx:]

# Let's fix the javascript logic to handle tab switching
# I need to find the old sidebar active state JS and replace it
js_start = html.find('// --- 3. Sidebar Active State ---')
js_end = html.find('});\n    });\n</script>')

if js_start != -1 and js_end != -1:
    new_js = """// --- 3. Tab Navigation ---
        const navLinks = document.querySelectorAll('.nav-link');
        const tabs = document.querySelectorAll('.tab-content');
        
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('data-target');
                
                // Remove active classes from all links
                navLinks.forEach(l => {
                    l.classList.remove('bg-primary-container', 'text-on-primary-container');
                    l.classList.add('text-on-surface-variant');
                });
                // Add active to clicked link
                this.classList.add('bg-primary-container', 'text-on-primary-container');
                this.classList.remove('text-on-surface-variant');
                
                // Hide all tabs
                tabs.forEach(tab => {
                    tab.classList.add('hidden');
                    tab.classList.remove('block');
                });
                
                // Show target tab
                const targetTab = document.getElementById(targetId);
                if(targetTab) {
                    targetTab.classList.remove('hidden');
                    targetTab.classList.add('block');
                }
            });
        """
    html = html[:js_start] + new_js + html[js_end:]

html_path.write_text(html, encoding="utf-8")
print("Successfully updated settings.html to use Tabs!")
