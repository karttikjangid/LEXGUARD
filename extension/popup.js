document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const statusMessage = document.getElementById('status-message');
    const errorMessage = document.getElementById('error-message');

    analyzeBtn.addEventListener('click', async () => {
        analyzeBtn.classList.add('hidden');
        statusMessage.classList.remove('hidden');
        errorMessage.classList.add('hidden');

        try {
            // Get active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) {
                throw new Error("No active tab found.");
            }

            // Send message to content script
            chrome.tabs.sendMessage(tab.id, { action: "ANALYZE_PAGE" }, (response) => {
                if (chrome.runtime.lastError) {
                    showError("Please refresh the page and try again.");
                    return;
                }

                if (response && response.success) {
                    // Content script is handling the banner UI
                    window.close(); // Close popup on success
                } else {
                    showError(response ? response.error : "Unknown error occurred.");
                }
            });

        } catch (error) {
            showError(error.message);
        }
    });

    function showError(msg) {
        statusMessage.classList.add('hidden');
        analyzeBtn.classList.remove('hidden');
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }
});
