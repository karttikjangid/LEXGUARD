chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "ANALYZE_PAGE") {
        analyzeCurrentPage().then(() => {
            sendResponse({ success: true });
        }).catch((err) => {
            console.error("LexGuard Error:", err);
            sendResponse({ success: false, error: err.message });
        });
        return true; // Keep message channel open for async response
    }
});

async function analyzeCurrentPage() {
    // 1. Extract text from the page.
    // Try to find the main content, otherwise fallback to body
    let container = document.querySelector('main') || document.querySelector('article') || document.body;
    let rawContent = container.innerText;

    if (!rawContent || rawContent.trim().length === 0) {
        throw new Error("Could not extract text from this page.");
    }

    // 2. Send to local backend
    const payload = {
        raw_content: rawContent,
        file_format: "plain",
        source: "chrome_extension"
    };

    const response = await fetch('https://lexguard-api-81249095052.asia-south1.run.app/api/analyze-contract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        let errorMsg = `Server returned ${response.status}`;
        try {
            const errData = await response.json();
            if (errData.detail) errorMsg = errData.detail;
        } catch (e) {}
        throw new Error(errorMsg);
    }

    const report = await response.json();

    // 3. Inject Banner
    injectBanner(report);
}

function injectBanner(report) {
    // Check if banner already exists and remove it
    const existingBanner = document.getElementById('lexguard-warning-banner');
    if (existingBanner) {
        existingBanner.remove();
    }

    const banner = document.createElement('div');
    banner.id = 'lexguard-warning-banner';
    
    // Style the banner to float at the top with a glassmorphism effect
    Object.assign(banner.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100%',
        zIndex: '999999',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', // elevation-4
        fontFamily: '"Roboto", "Google Sans", sans-serif',
        color: '#1c1b1f',
        padding: '16px 24px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        borderBottom: '4px solid #3f51b5' // Primary brand color bottom border
    });

    // Find highest severity risks
    const criticalRisks = report.flagged_risks.filter(r => r.severity === 'CRITICAL');
    const highRisks = report.flagged_risks.filter(r => r.severity === 'HIGH');
    
    let summaryHtml = '';
    
    // Determine overall color based on score
    if (report.overall_risk_score >= 8) {
        banner.style.borderBottomColor = '#b3261e'; // Material Red
    } else if (report.overall_risk_score >= 5) {
        banner.style.borderBottomColor = '#f57c00'; // Material Orange
    } else if (report.overall_risk_score >= 3) {
        banner.style.borderBottomColor = '#fbc02d'; // Material Yellow
    } else {
        banner.style.borderBottomColor = '#388e3c'; // Material Green
    }

    let topRisksHtml = '';
    const risksToShow = [...criticalRisks, ...highRisks].slice(0, 2); // Show top 2

    if (risksToShow.length > 0) {
        topRisksHtml = `
            <div style="margin-top: 8px;">
                <strong style="font-size: 13px; text-transform: uppercase; color: #49454f;">Top Risks:</strong>
                <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 14px;">
                    ${risksToShow.map(r => `
                        <li style="margin-bottom: 4px;">
                            <span style="font-weight: 600; color: ${r.severity === 'CRITICAL' ? '#b3261e' : '#f57c00'}">[${r.severity}]</span> 
                            ${r.plain_language_explanation}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    banner.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <h2 style="margin: 0 0 4px 0; font-size: 18px; color: #3f51b5; display: flex; align-items: center; gap: 8px;">
                    <span style="font-weight: 700;">LexGuard Analysis</span>
                    <span style="font-size: 14px; font-weight: 500; background: #e8eaf6; padding: 2px 8px; border-radius: 12px; color: #1a237e;">
                        Risk Score: ${report.overall_risk_score}/10
                    </span>
                </h2>
                <p style="margin: 0; font-size: 14px; color: #49454f; line-height: 1.4;">${report.executive_summary}</p>
                ${topRisksHtml}
            </div>
            <button id="lexguard-close-btn" style="background: none; border: none; cursor: pointer; padding: 4px; font-size: 20px; line-height: 1; color: #49454f;">&times;</button>
        </div>
    `;

    document.body.appendChild(banner);

    // Ensure space at top of body so banner doesn't cover content
    const bannerHeight = banner.offsetHeight;
    if (document.body.style.marginTop) {
        const currentMargin = parseInt(document.body.style.marginTop);
        document.body.style.marginTop = `${currentMargin + bannerHeight}px`;
    } else {
        document.body.style.marginTop = `${bannerHeight}px`;
    }

    document.getElementById('lexguard-close-btn').addEventListener('click', () => {
        banner.remove();
        // Restore margin
        const currentMargin = parseInt(document.body.style.marginTop);
        document.body.style.marginTop = `${Math.max(0, currentMargin - bannerHeight)}px`;
    });
}
