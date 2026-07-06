import re
from pathlib import Path

index_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\index.html")
html = index_path.read_text(encoding="utf-8")

# Let's create a macro or simply define the dynamic structure for a Zone Box
def get_dynamic_zone(zone_num, zone_name):
    return f"""
{{% if zone{zone_num}_status == 'CRITICAL' %}}
<div class="bg-error-container border border-error p-lg rounded-lg shadow-[0_4px_6px_-1px_rgba(0,0,0,0.05)] flex items-center justify-between relative overflow-hidden">
<div class="absolute top-0 left-0 w-1 h-full bg-error"></div>
<div>
<div class="font-label-md text-label-md text-error">Zone {zone_num}</div>
<div class="font-headline-md text-headline-md text-on-error-container font-bold mt-xs">{zone_name}</div>
<div class="font-label-md text-label-md text-error mt-xs flex items-center gap-xs font-bold">
<span class="w-3 h-3 rounded-full bg-error pulse-red block"></span>
                                Load: {{{{ zone{zone_num}_load }}}} MW (CRITICAL - {{{{ zone{zone_num}_cap }}}}% Capacity)
                            </div>
</div>
<span class="material-symbols-outlined text-error text-4xl" style="font-variation-settings: 'FILL' 1;">warning</span>
</div>
{{% else %}}
<div class="bg-surface-container-lowest border border-secondary p-lg rounded-lg shadow-[0_4px_6px_-1px_rgba(0,0,0,0.05)] flex items-center justify-between">
<div>
<div class="font-label-md text-label-md text-on-surface-variant">Zone {zone_num}</div>
<div class="font-headline-md text-headline-md text-on-surface mt-xs">{zone_name}</div>
<div class="font-body-sm text-body-sm text-secondary mt-xs flex items-center gap-xs">
<span class="w-2 h-2 rounded-full bg-secondary pulse-green block"></span>
                                Load: {{{{ zone{zone_num}_load }}}} MW (Stable)
                            </div>
</div>
<span class="material-symbols-outlined text-secondary text-3xl" style="font-variation-settings: 'FILL' 1;">check_circle</span>
</div>
{{% endif %}}
"""

# We need to replace the static HTML zones with the dynamic Jinja blocks.
# The structure goes from <!-- Zone 1 --> down to just before <!-- Zone 2
# Let's use regex to extract and replace the big blocks.

zone_block_pattern = re.compile(
    r'<!-- Zone 1 -->.*?<!-- Zone 2 \(CRITICAL\) -->.*?<!-- Zone 3 -->.*?</div>', 
    re.DOTALL
)

dynamic_blocks = f"""
<!-- Zone 1 -->
{get_dynamic_zone(1, 'Quarters Nord')}
<!-- Zone 2 -->
{get_dynamic_zone(2, 'Centre Ville')}
<!-- Zone 3 -->
{get_dynamic_zone(3, 'Zone Industrielle')}
"""

html = zone_block_pattern.sub(dynamic_blocks, html)

index_path.write_text(html, encoding="utf-8")
print("Successfully injected Jinja templates into index.html")
