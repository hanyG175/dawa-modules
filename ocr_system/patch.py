import re

with open("src/web/templates/ddi_analyzer.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Change the order so donnee structure is at the bottom
# First, extract extractedDataPanel
extracted_panel_pattern = r"(<!-- Middle Row: Pre-Analysis JSON Data \(OCR\) -->\s*<div class=\"cyber-panel p-6\" id=\"extractedDataPanel\"(.|\n)*?</div>\s*</div>)"
match = re.search(extracted_panel_pattern, content)
if match:
    extracted_html = match.group(0)
    # Remove it from the current position
    content = content.replace(extracted_html, "")
    
    # Insert it right before </main>
    content = content.replace("</main>", extracted_html + "\n    </main>")


# 2. Add LLM Button and fix dynamic styling
# Find where the llmPanel is
llm_panel_pattern = r"(<!-- Bottom Rows: LLM Panel -->\s*<div class=\"cyber-panel p-6 flex flex-col relative\" id=\"llmPanel\">)"

# Remove the automatic LLM logic in JS, add a button above LLM panel if not exist
if 'id="analyzeLlmBtn"' not in content:
    llm_btn_html = """
        <div class="mt-4 mb-4 flex justify-center">
            <button id="analyzeLlmBtn" class="hidden bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-transform transform hover:scale-105 flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                Générer le Rapport IA (LLM)
            </button>
        </div>
"""
    content = content.replace(llm_panel_pattern, llm_btn_html + "\n        " + llm_panel_pattern)


# Also in the JavaScript, update renderAnalysis and api calls
js_patch = """
        let currentAnalysisData = null;
        let currentTargetLang = 'fr';

        function renderAnalysis(analysisData, targetLang) {
            currentAnalysisData = analysisData;
            currentTargetLang = targetLang;
            
            // Show Parsed Data
            extractedDataPanel.style.display = 'block';
            jsonOutput.textContent = JSON.stringify(analysisData.parsed_prescription, null, 2);
            
            // Render Static DDI Table if we have ANSM pairs
            staticDdiPanel.classList.remove('hidden');
            ddiTableBody.innerHTML = ''; // clear old rows
            
            const tableHeader = staticDdiPanel.querySelector('.bg-red-50');
            const tableTitle = staticDdiPanel.querySelector('h2');
            
            if (analysisData.ansm_pairs && analysisData.ansm_pairs.length > 0) {
                // IT HAS INTERACTIONS (RED)
                staticDdiPanel.style.border = '2px solid #ef4444';
                if(tableHeader) tableHeader.className = 'bg-red-50 px-6 py-4 border-b border-red-200 flex items-center justify-between';
                if(tableTitle) tableTitle.className = 'text-xl font-bold text-red-900';
                
                analysisData.ansm_pairs.forEach((pair, idx) => {
                    // ... (existing code for rows)
                    let severities = Array.isArray(pair.severity) ? pair.severity : [pair.severity];
                    let severityHtml = severities.map(sev => {
                        let severityClass = "bg-red-50 text-red-700";
                        if(sev.toLowerCase().includes("déconseill") || sev.toLowerCase().includes("precaution")) {
                            severityClass = "bg-yellow-50 text-yellow-700";
                        }
                        return `<span class="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border border-current mb-1 block w-fit ${severityClass}">${sev}</span>`;
                    }).join('');

                    let riskHtml = "";
                    if (Array.isArray(pair.risk)) {
                        for(let i=0; i<pair.risk.length; i++) {
                            riskHtml += `<div class="mb-2"><strong class="text-sm text-gray-800">${severities[i] || 'Risque'}</strong>: ${pair.risk[i]}<br/>`;
                            if (pair.management && pair.management[i]) {
                                let mgmt = pair.management[i];
                                let isLong = mgmt.length > 100;
                                let mgmtId = `mgmt-${idx}-${i}`;
                                if(isLong) {
                                    riskHtml += `<span class="italic text-gray-600">Conduite:</span> <span id="${mgmtId}-short">${mgmt.substring(0, 100)}...</span> <span id="${mgmtId}-full" class="hidden">${mgmt}</span> <button onclick="document.getElementById('${mgmtId}-short').classList.toggle('hidden'); document.getElementById('${mgmtId}-full').classList.toggle('hidden'); this.textContent = this.textContent === 'Voir plus' ? 'Voir moins' : 'Voir plus';" class="text-xs text-blue-500 hover:text-blue-700 underline focus:outline-none">Voir plus</button></div>`;
                                } else {
                                    riskHtml += `<span class="italic text-gray-600">Conduite:</span> ${mgmt}</div>`;
                                }
                            } else {
                                riskHtml += `</div>`;
                            }
                        }
                    } else {
                        riskHtml = `<div class="mb-2">${pair.risk}</div>`;
                        if (pair.management) {
                            let mgmt = pair.management;
                            let isLong = mgmt.length > 100;
                            let mgmtId = `mgmt-${idx}`;
                            if(isLong) {
                                riskHtml += `<div class="mt-1"><span class="italic text-gray-600">Conduite:</span> <span id="${mgmtId}-short">${mgmt.substring(0, 100)}...</span> <span id="${mgmtId}-full" class="hidden">${mgmt}</span> <button onclick="document.getElementById('${mgmtId}-short').classList.toggle('hidden'); document.getElementById('${mgmtId}-full').classList.toggle('hidden'); this.textContent = this.textContent === 'Voir plus' ? 'Voir moins' : 'Voir plus';" class="text-xs text-blue-500 hover:text-blue-700 underline focus:outline-none">Voir plus</button></div>`;
                            } else {
                                riskHtml += `<div class="mt-1"><span class="italic text-gray-600">Conduite:</span> ${mgmt}</div>`;
                            }
                        }
                    }

                    let dciClassHtml = `
                        <div class="mb-1"><span class="font-semibold text-gray-800">${pair.drug_a_dci || pair.drug_a}</span> <span class="text-xs text-gray-500">(${pair.class_a || 'Substance principale'})</span></div>
                        <div class="text-xs text-gray-400 italic my-1">associé à</div>
                        <div><span class="font-semibold text-gray-800">${pair.drug_b_dci || pair.drug_b}</span> <span class="text-xs text-gray-500">(${pair.class_b || 'Substance principale'})</span></div>
                    `;

                    const rowHTML = `
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 font-bold text-gray-900 border-r border-gray-100">
                                <div class="flex flex-col">
                                    <span class="text-indigo-600">${pair.original_a || pair.drug_a}</span>
                                    <span class="text-xs text-gray-400 font-normal italic my-1">associé à</span>
                                    <span class="text-indigo-600">${pair.original_b || pair.drug_b}</span>
                                </div>
                            </td>
                            <td class="px-6 py-4 text-sm border-r border-gray-100">
                                ${dciClassHtml}
                            </td>
                            <td class="px-3 py-4 border-r border-gray-100">
                                ${severityHtml}
                            </td>
                            <td class="px-6 py-4 text-gray-700 font-medium text-sm">
                                ${riskHtml}
                            </td>
                        </tr>
                    `;
                    ddiTableBody.insertAdjacentHTML('beforeend', rowHTML);
                });
            } else {
                // NO INTERACTIONS (GREEN)
                staticDdiPanel.style.border = '2px solid #22c55e'; // tailwind green-500
                if(tableHeader) tableHeader.className = 'bg-green-50 px-6 py-4 border-b border-green-200 flex items-center justify-between';
                if(tableTitle) tableTitle.className = 'text-xl font-bold text-green-900';
                
                const emptyRow = `
                    <tr class="bg-gray-50">
                        <td colspan="4" class="px-6 py-8 text-center text-green-600 font-bold italic">
                            ✓ Aucune interaction sévère identifiée dans le thésaurus ANSM pour ces molécules.
                        </td>
                    </tr>
                `;
                ddiTableBody.insertAdjacentHTML('beforeend', emptyRow);
            }

            // Show LLM Button
            document.getElementById('analyzeLlmBtn').classList.remove('hidden');
            llmOutput.innerHTML = '<div class="flex flex-col items-center justify-center h-full text-slate-400"><p class="text-center">Cliquez sur le bouton pour générer le rapport IA (OpenFDA + LLM).</p></div>';
        }

        // New event listener for the LLM button
        const analyzeLlmBtn = document.getElementById('analyzeLlmBtn');
        if (analyzeLlmBtn) {
            analyzeLlmBtn.addEventListener('click', async () => {
                if (!currentAnalysisData) return;
                
                analyzeLlmBtn.disabled = true;
                analyzeLlmBtn.innerHTML = '<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Génération du Rapport IA en cours...';
                
                llmOverlay.classList.remove('hidden');
                updateStage("Interrogation du modèle IA (Qwen) avec les données OpenFDA...");
                
                try {
                    const response = await fetch('/api/generate_llm_report', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            parsed_prescription: currentAnalysisData.parsed_prescription,
                            ddi_context: currentAnalysisData.ddi_context,
                            language: currentTargetLang
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success && result.llm_report) {
                        llmOutput.innerHTML = marked.parse(result.llm_report);
                        
                        // Handle RTL for Arabic
                        if (currentTargetLang === 'ar') {
                            llmOutput.setAttribute('dir', 'rtl');
                            llmOutput.classList.add('text-right');
                            llmOutput.classList.remove('text-left');
                        } else {
                            llmOutput.setAttribute('dir', 'ltr');
                            llmOutput.classList.remove('text-right');
                            llmOutput.classList.add('text-left');
                        }
                    } else {
                        llmOutput.innerHTML = `<div class="text-red-500">Erreur LLM: ${result.error || "Rapport vide"}</div>`;
                    }
                } catch(e) {
                    llmOutput.innerHTML = `<div class="text-red-500">Erreur critique LLM: ${e.message}</div>`;
                } finally {
                    llmOverlay.classList.add('hidden');
                    analyzeLlmBtn.disabled = false;
                    analyzeLlmBtn.innerHTML = '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Régénérer le Rapport IA';
                }
            });
        }
"""

# Replace the entire renderAnalysis function definition using regex
render_analysis_pattern = r"function renderAnalysis\(analysisData, targetLang\) \{.*?(?=</script>)"
content = re.sub(render_analysis_pattern, js_patch.strip(), content, flags=re.DOTALL)

with open("src/web/templates/ddi_analyzer.html", "w", encoding="utf-8") as f:
    f.write(content)
