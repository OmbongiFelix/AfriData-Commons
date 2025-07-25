function copyToken() {
            const tokenValue = document.getElementById('tokenValue').textContent;
            
            // Create temporary textarea to copy text
            const textarea = document.createElement('textarea');
            textarea.value = tokenValue;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            // Show success toast
            const toast = new bootstrap.Toast(document.getElementById('copyToast'));
            toast.show();
        }

        function refreshToken() {
            const refreshBtn = document.querySelector('.refresh-btn');
            const tokenDisplay = document.getElementById('tokenDisplay');
            const tokenValue = document.getElementById('tokenValue');
            
            // Show loading state
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;
            tokenDisplay.classList.add('loading');
            tokenValue.textContent = 'Generating new token...';
            
            // Fetch new token
            fetch('{% url "token" %}')
                .then(response => response.text())
                .then(html => {
                    // Parse the HTML to extract the token
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newTokenElement = doc.getElementById('tokenValue');
                    
                    if (newTokenElement) {
                        tokenValue.textContent = newTokenElement.textContent;
                    } else {
                        // Fallback: reload the page
                        location.reload();
                    }
                })
                .catch(error => {
                    console.error('Error refreshing token:', error);
                    tokenValue.textContent = 'Error refreshing token. Please refresh the page.';
                })
                .finally(() => {
                    // Reset button state
                    refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Token';
                    refreshBtn.disabled = false;
                    tokenDisplay.classList.remove('loading');
                });
        }

        // Auto-refresh token every 50 minutes (before it expires)
        setInterval(() => {
            console.log('Auto-refreshing token...');
            refreshToken();
        }, 50 * 60 * 1000); // 50 minutes

        // Add current timestamp
        document.addEventListener('DOMContentLoaded', function() {
            const now = new Date().toLocaleString();
            const timestampElements = document.querySelectorAll('[data-timestamp]');
            timestampElements.forEach(el => {
                if (el.textContent.includes('Now')) {
                    el.textContent = el.textContent.replace('Now', now);
                }
            });
        });