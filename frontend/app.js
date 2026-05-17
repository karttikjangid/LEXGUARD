document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    
    const uploadSection = document.getElementById('upload-section');
    const resultSection = document.getElementById('result-section');
    const resetBtn = document.getElementById('reset-btn');
    
    const spinnerContainer = document.getElementById('loading-spinner');
    const errorContainer = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    // Drag and Drop Event Listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-active'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect, false);
    resetBtn.addEventListener('click', resetView);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    function handleFileSelect(e) {
        if (this.files.length > 0) {
            processFile(this.files[0]);
        }
    }

    async function processFile(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['pdf', 'docx', 'txt'].includes(ext)) {
            showError("Unsupported file type. Please upload a .pdf, .docx, or .txt file.");
            return;
        }

        dropZone.classList.add('hidden');
        spinnerContainer.classList.remove('hidden');
        errorContainer.classList.add('hidden');

        try {
            let rawContent = "";
            let fileFormat = ext;

            if (ext === 'txt') {
                rawContent = await file.text();
                fileFormat = 'plain'; // Maps to "plain" in backend FORMAT_ALIASES
            } else {
                // For PDF and DOCX, base64 encode the file
                const arrayBuffer = await file.arrayBuffer();
                const base64String = btoa(
                    new Uint8Array(arrayBuffer)
                    .reduce((data, byte) => data + String.fromCharCode(byte), '')
                );
                rawContent = base64String;
            }

            const payload = {
                raw_content: rawContent,
                file_format: fileFormat,
                source: "web_dashboard"
            };

            const response = await fetch('https://lexguard-api-81249095052.asia-south1.run.app/api/analyze-contract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Server error: ${response.status}`);
            }

            const report = await response.json();
            renderResults(report);

        } catch (error) {
            console.error("Analysis failed:", error);
            showError(error.message);
        }
    }

    function showError(message) {
        spinnerContainer.classList.add('hidden');
        dropZone.classList.remove('hidden');
        errorContainer.classList.remove('hidden');
        errorText.textContent = message;
    }

    function renderResults(report) {
        uploadSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        // Overall Score
        const scoreValue = document.getElementById('overall-score-value');
        scoreValue.textContent = `${report.overall_risk_score}/10`;
        
        // Color-code score based on value (higher is worse)
        if (report.overall_risk_score >= 8) {
            scoreValue.style.color = "var(--md-sys-color-error)";
        } else if (report.overall_risk_score >= 5) {
            scoreValue.style.color = "var(--md-sys-color-warning-high)";
        } else if (report.overall_risk_score >= 3) {
            scoreValue.style.color = "var(--md-sys-color-warning-medium)";
        } else {
            scoreValue.style.color = "var(--md-sys-color-success)";
        }

        // Executive Summary
        document.getElementById('executive-summary-text').textContent = report.executive_summary;

        // Render Risk Cards
        const container = document.getElementById('risk-cards-container');
        container.innerHTML = ''; // Clear previous

        const template = document.getElementById('risk-card-template');

        // Sort risks by severity: CRITICAL > HIGH > MEDIUM > LOW
        const severityScores = { "CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1 };
        const sortedRisks = [...report.flagged_risks].sort((a, b) => {
            return severityScores[b.severity] - severityScores[a.severity];
        });

        sortedRisks.forEach(risk => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.risk-card');
            
            // Set Severity Class
            card.classList.add(`severity-${risk.severity.toLowerCase()}`);

            // Populate Content
            clone.querySelector('.risk-category').textContent = risk.category.replace(/_/g, ' ');
            clone.querySelector('.risk-severity-badge').textContent = risk.severity;
            clone.querySelector('.risk-explanation').textContent = risk.plain_language_explanation;
            clone.querySelector('.risk-recommendation').textContent = risk.recommendation;
            clone.querySelector('.original-text-content').textContent = risk.original_text;

            container.appendChild(clone);
        });
    }

    function resetView() {
        resultSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        dropZone.classList.remove('hidden');
        spinnerContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        fileInput.value = ''; // Reset file input
    }
});
