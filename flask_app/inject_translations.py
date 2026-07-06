import re
from pathlib import Path

html_path = Path(r"C:\Users\jarro\OneDrive\Desktop\smart-city-energy-forecasting-tetouan\flask_app\templates\settings.html")
html = html_path.read_text(encoding="utf-8")

translation_js = """
        // --- 4. Language Translation Simulation ---
        function applyLanguage(lang) {
            const isFrench = lang === 'French (FR)';
            
            const dictionary = {
                'Dashboard': 'Tableau de bord',
                'Model Comparison': 'Comparaison des Modèles',
                'Historical Data': 'Données Historiques',
                'Correlations': 'Corrélations',
                'Settings': 'Paramètres',
                'General': 'Général',
                'Alert Thresholds': 'Seuils d\\'Alerte',
                'API Integrations': 'Intégrations API',
                'User Access': 'Accès Utilisateur',
                'General Settings': 'Paramètres Généraux',
                'System Language': 'Langue du Système',
                'Timezone': 'Fuseau Horaire',
                'Cancel': 'Annuler',
                'Save Changes': 'Enregistrer les Modifications'
            };
            
            const reverseDictionary = Object.fromEntries(Object.entries(dictionary).map(([k, v]) => [v, k]));

            // Simple text replacement function for specific elements
            function translateNode(node) {
                if (node.nodeType === 3) { // Text node
                    let text = node.nodeValue.trim();
                    if (text) {
                        if (isFrench && dictionary[text]) {
                            node.nodeValue = dictionary[text];
                        } else if (!isFrench && reverseDictionary[text]) {
                            node.nodeValue = reverseDictionary[text];
                        }
                    }
                } else {
                    node.childNodes.forEach(translateNode);
                }
            }

            // Target elements we want to translate
            const navs = document.querySelectorAll('nav');
            navs.forEach(nav => translateNode(nav));
            
            const headers = document.querySelectorAll('h2, h3');
            headers.forEach(h => translateNode(h));
            
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => translateNode(btn));
            
            const labels = document.querySelectorAll('label');
            labels.forEach(lbl => translateNode(lbl));
        }

        // Apply on load
        if (savedLang) {
            applyLanguage(savedLang);
        }

        // Apply immediately when Save is clicked
        const saveBtnElem = document.getElementById('saveSettingsBtn');
        if (saveBtnElem) {
            saveBtnElem.addEventListener('click', function() {
                const selectedLang = document.getElementById('langSelect') ? document.getElementById('langSelect').value : null;
                if (selectedLang) {
                    setTimeout(() => applyLanguage(selectedLang), 100); // Apply shortly after saving starts
                }
            });
        }
"""

if "// --- 4. Language Translation Simulation ---" not in html:
    html = html.replace('// --- 3. Tab Navigation ---', translation_js + '\n        // --- 3. Tab Navigation ---')
    html_path.write_text(html, encoding="utf-8")
    print("Translation logic injected successfully!")
else:
    print("Translation logic already exists.")
