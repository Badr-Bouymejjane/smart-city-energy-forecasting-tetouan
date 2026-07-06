from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\data.html")
html = html_path.read_text(encoding="utf-8")

script_injection = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    // Select elements
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const startDateInput = dateInputs[0];
    const endDateInput = dateInputs[1];
    
    const zoneSelect = document.querySelector('select');
    
    const checkInputs = document.querySelectorAll('input[type="checkbox"]');
    const checkTemp = checkInputs[0];
    const checkHumidity = checkInputs[1];
    const checkWind = checkInputs[2];
    
    const buttons = document.querySelectorAll('button');
    let resetBtn = null;
    let exportBtn = null;
    buttons.forEach(btn => {
        if (btn.innerText.includes("Reset Filters")) resetBtn = btn;
        if (btn.innerText.includes("Export to CSV")) exportBtn = btn;
    });
    
    const tbody = document.querySelector('tbody');
    
    // Pagination state
    let currentPage = 1;
    const perPage = 15;
    
    function fetchAndRenderData() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const zone = zoneSelect.value;
        
        const params = new URLSearchParams({
            start_date: startDate,
            end_date: endDate,
            zone: zone,
            page: currentPage,
            per_page: perPage
        });
        
        fetch('/api/data?' + params.toString())
            .then(response => response.json())
            .then(data => {
                if(data.error) {
                    console.error(data.error);
                    return;
                }
                renderTable(data.data);
                renderPagination(data.total, data.page, data.per_page);
            })
            .catch(err => console.error(err));
    }
    
    function renderTable(rows) {
        tbody.innerHTML = ''; // clear existing static rows
        
        const showTemp = checkTemp.checked;
        const showHum = checkHumidity.checked;
        const showWind = checkWind.checked;
        
        rows.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.className = index % 2 === 0 ? "table-row-hover bg-surface-container-lowest" : "table-row-hover bg-[#F8FAFC]";
            
            // Format status badge
            let statusBadge = '';
            if (row.status === 'Peak Alert') {
                statusBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full bg-error-container/50 text-on-error-container font-label-sm text-[10px]">Peak Alert</span>';
            } else {
                statusBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/20 text-on-secondary-container font-label-sm text-[10px]">Normal</span>';
            }
            
            // Format consumption styling
            const consClass = row.status === 'Peak Alert' ? 'p-4 text-right font-medium text-error' : 'p-4 text-right font-medium';
            
            let html = `
                <td class="p-4 whitespace-nowrap">${row.timestamp}</td>
                <td class="p-4">${row.zone}</td>
                <td class="${consClass}">${row.consumption.toLocaleString()}</td>
            `;
            
            if (showTemp) {
                html += `<td class="p-4 text-right">${row.temperature}</td>`;
            } else {
                html += `<td class="p-4 text-right text-outline-variant">-</td>`;
            }
            
            if (showHum) {
                html += `<td class="p-4 text-right">${row.humidity}</td>`;
            } else {
                html += `<td class="p-4 text-right text-outline-variant">-</td>`;
            }
            
            if (showWind) { // Need to add wind column dynamically since original didn't have it
                html += `<td class="p-4 text-right">${row.wind}</td>`;
            } else {
                html += `<td class="p-4 text-right text-outline-variant">-</td>`;
            }
            
            html += `<td class="p-4 text-center">${statusBadge}</td>`;
            
            tr.innerHTML = html;
            tbody.appendChild(tr);
        });
    }
    
    function renderPagination(total, page, perPage) {
        const paginationNav = document.querySelector('nav[aria-label="Pagination"]');
        const summaryText = document.querySelector('.sm\\\\:flex-1 > div > p');
        
        if (!paginationNav || !summaryText) return;
        
        const totalPages = Math.ceil(total / perPage);
        const startItem = ((page - 1) * perPage) + 1;
        const endItem = Math.min(page * perPage, total);
        
        if (total === 0) {
            summaryText.innerHTML = `Showing <span class="font-medium text-on-surface">0</span> results`;
            paginationNav.innerHTML = '';
            return;
        }
        
        summaryText.innerHTML = `Showing <span class="font-medium text-on-surface">${startItem}</span> to <span class="font-medium text-on-surface">${endItem}</span> of <span class="font-medium text-on-surface">${total.toLocaleString()}</span> results`;
        
        let navHtml = `
            <a href="#" id="prevPage" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-outline-variant/50 bg-surface-container-lowest text-sm font-medium text-on-surface-variant hover:bg-surface-container-low transition-colors">
                <span class="sr-only">Previous</span>
                <span class="material-symbols-outlined text-sm">chevron_left</span>
            </a>
        `;
        
        navHtml += `
            <span class="z-10 bg-primary-container/10 border-primary text-primary relative inline-flex items-center px-4 py-2 border text-sm font-medium">
                ${page} / ${totalPages}
            </span>
        `;
        
        navHtml += `
            <a href="#" id="nextPage" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-outline-variant/50 bg-surface-container-lowest text-sm font-medium text-on-surface-variant hover:bg-surface-container-low transition-colors">
                <span class="sr-only">Next</span>
                <span class="material-symbols-outlined text-sm">chevron_right</span>
            </a>
        `;
        
        paginationNav.innerHTML = navHtml;
        
        document.getElementById('prevPage').addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                fetchAndRenderData();
            }
        });
        
        document.getElementById('nextPage').addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                fetchAndRenderData();
            }
        });
    }
    
    // Fix table headers for Wind
    const theadTr = document.querySelector('thead tr');
    // Ensure the Wind column exists in header, the original design missed it
    if (theadTr.children.length === 6) {
        const windTh = document.createElement('th');
        windTh.className = "sticky top-0 p-4 font-label-sm text-label-sm text-tertiary whitespace-nowrap bg-surface-container-low z-10 text-right";
        windTh.innerText = "Wind Speed (m/s)";
        theadTr.insertBefore(windTh, theadTr.children[5]);
    }
    
    // Event Listeners
    startDateInput.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
    endDateInput.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
    zoneSelect.addEventListener('change', () => { currentPage = 1; fetchAndRenderData(); });
    checkTemp.addEventListener('change', () => fetchAndRenderData());
    checkHumidity.addEventListener('change', () => fetchAndRenderData());
    checkWind.addEventListener('change', () => fetchAndRenderData());
    
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            startDateInput.value = "2023-01-01";
            endDateInput.value = "2023-12-31";
            zoneSelect.value = "All Zones";
            checkTemp.checked = true;
            checkHumidity.checked = true;
            checkWind.checked = true;
            currentPage = 1;
            fetchAndRenderData();
        });
    }
    
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;
            const zone = zoneSelect.value;
            
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate,
                zone: zone
            });
            window.location.href = '/api/export?' + params.toString();
        });
    }
    
    // Initial fetch
    // Set default dates based on the dataset to ensure we see data
    startDateInput.value = "2017-01-01";
    endDateInput.value = "2017-01-07"; // Just a week initially to avoid huge payloads
    
    fetchAndRenderData();
});
</script>
</body>
"""

if "function fetchAndRenderData" not in html:
    html = html.replace("</body>", script_injection)
    html_path.write_text(html, encoding="utf-8")
    print("Successfully injected JS into data.html")
else:
    print("JS already injected.")
