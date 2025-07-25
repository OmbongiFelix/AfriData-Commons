// AfriData API Documentation JavaScript

    // Global variables
    let currentUser = null;
    let apiKey = null;

    // Initialize the page
    document.addEventListener('DOMContentLoaded', function() {
        initializeNavigation();
        initializeLanguageSelector();
        initializeAuthSystem();
        initializeApiKeyManagement();
        checkAuthStatus();
    });

    // Navigation functionality
    function initializeNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
    
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
            
                // Remove active class from all links
                navLinks.forEach(nl => nl.classList.remove('active'));
            
                // Add active class to clicked link
                this.classList.add('active');
                // Scroll to section
                const targetSection = document.getElementById(targetId);
                if (targetSection) {
                    targetSection.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    
        // Update active navigation on scroll
        window.addEventListener('scroll', updateActiveNavigation);
    }

    function updateActiveNavigation() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');
    
        let currentSection = '';
    
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
        
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
    
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    }


    // Language selector functionality
    function initializeLanguageSelector() {
        const langButtons = document.querySelectorAll('.lang-btn');
        const exampleBlocks = document.querySelectorAll('.example-block');
    
        langButtons.forEach(button => {
            button.addEventListener('click', function() {
                const selectedLang = this.getAttribute('data-lang');
            
                // Remove active class from all buttons
                langButtons.forEach(btn => btn.classList.remove('active'));
            
                // Add active class to clicked button
                this.classList.add('active');
                // Hide all example blocks
                exampleBlocks.forEach(block => {
                    block.classList.add('hidden');
                });
            
                // Show selected language block
                const selectedBlock = document.getElementById(`${selectedLang}-example`);
                if (selectedBlock) {
                    selectedBlock.classList.remove('hidden');
                }
            });
        });
    }

    
    // Authentication system
    function initializeAuthSystem() {
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
    
        if (loginBtn) {
            loginBtn.addEventListener('click', showLoginModal);
        }
    
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }
    }

    function showLoginModal() {
        // Create modal dynamically
        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                <h3 class="text-lg font-semibold mb-4">Login to AfriData</h3>
                <form id="loginForm">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                        <input type="email" id="loginEmail" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                        <input type="password" id="loginPassword" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <div class="flex justify-end space-x-3">
                        <button type="button" class="px-4 py-2 text-gray-600 hover:text-gray-800" onclick="closeModal()">Cancel</button>
                        <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Login</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);
    
        // Handle form submission
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
        
            // Simulate login process
            login(email, password);
        });
    
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    function closeModal() {
        const modal = document.querySelector('.modal');
        if (modal) {
            modal.remove();
        }
    }

    function login(email, password) {
        // Simulate API call
        setTimeout(() => {
            // Mock successful login
            currentUser = {
                email: email,
                name: email.split('@')[0],
                apiKey: 'ak_prod_' + Math.random().toString(36).substr(2, 20)
            };
            apiKey = currentUser.apiKey;
            updateAuthUI();
            closeModal();
            showNotification('Login successful!', 'success');
        }, 1000);
    }

    function logout() {
        currentUser = null;
        apiKey = null;
        updateAuthUI();
        showNotification('Logged out successfully!', 'success');
    }

    function checkAuthStatus() {
        // Check if user is already logged in (in a real app, check localStorage or session)
        // For demo purposes, we'll start logged out
        updateAuthUI();
    }

    function updateAuthUI() {
        const loginBtn = document.getElementById('loginBtn');
        const userSection = document.getElementById('userSection');
        const userName = document.getElementById('userName');
        const authWarning = document.getElementById('authWarning');
        const apiKeySection = document.getElementById('apiKeySection');
    
        if (currentUser) {
            loginBtn.style.display = 'none';
            userSection.classList.remove('hidden');
            userName.textContent = currentUser.name;
        
            if (authWarning) authWarning.style.display = 'none';
            if (apiKeySection) apiKeySection.classList.remove('hidden');
        } else {
            loginBtn.style.display = 'block';
            userSection.classList.add('hidden');
        
            if (authWarning) authWarning.style.display = 'block';
            if (apiKeySection) apiKeySection.classList.add('hidden');
        }
    }


    // API Key Management
    function initializeApiKeyManagement() {
        const generateKeyBtn = document.getElementById('generateKeyBtn');
        if (generateKeyBtn) {
            generateKeyBtn.addEventListener('click', generateNewApiKey);
        }
    }

    function generateNewApiKey() {
        if (!currentUser) {
            showNotification('Please login first!', 'error');
            return;
        }
    
        // Simulate API key generation
        const newKey = 'ak_prod_' + Math.random().toString(36).substr(2, 20);
        currentUser.apiKey = newKey;
        apiKey = newKey;
    
        showNotification('New API key generated!', 'success');
    
        // Update the displayed key (in a real app, you'd refresh the key list)
        const keyDisplay = document.querySelector('code');
        if (keyDisplay) {
            keyDisplay.textContent = newKey + '...';
        }
    }


    // Endpoint testing functionality
    function testEndpoint(method, endpoint) {
        if (!apiKey) {
            showNotification('Please login and generate an API key first!', 'error');
            return;
        }
    
        const fullUrl = `https://afridata.com${endpoint}`;
        showNotification(`Testing ${method} ${endpoint}...`, 'success');
    
        // Simulate API request
        setTimeout(() => {
            const mockResponse = {
                status: 200,
                data: {
                    message: 'Mock response for testing',
                    endpoint: endpoint,
                    method: method,
                    timestamp: new Date().toISOString()
                }
            };
            console.log('API Test Result:', mockResponse);
            showNotification(`Test completed! Check console for details.`, 'success');
        }, 1500);
    }

    // Copy functionality
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy to clipboard!', 'error');
        });
    }

    function copyCode(exampleId) {
        const codeBlock = document.querySelector(`#${exampleId} code`);
        if (codeBlock) {
            const text = codeBlock.textContent;
            copyToClipboard(text);
        }
    }


    // Notification system
    function showNotification(message, type = 'success') {
        // Remove existing notifications
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
    
        // Create new notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
    
        document.body.appendChild(notification);
    
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    
        // Hide notification after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }


    // Mock API functions (replace with actual API calls in production)
    function mockApiCall(endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                if (Math.random() > 0.1) { // 90% success rate
                    resolve({
                        status: 200,
                        data: {
                            message: 'Mock API response',
                            endpoint: endpoint,
                            method: method,
                            timestamp: new Date().toISOString()
                        }
                    });
                } else {
                    reject({
                        status: 500,
                        error: 'Mock API error'
                    });
                }
            }, 1000 + Math.random() * 1000);
        });
    }


    // Real API functions (implement these with your actual API endpoints)
    async function apiRequest(endpoint, options = {}) {
        const baseUrl = 'https://afridata.com/api/v1';
        const url = `${baseUrl}${endpoint}`;
     
        const defaultOptions = {
            method: 'GET',
            headers:  {
                'Content-Type': 'application/json',
                ...(apiKey && { 'Authorization': `Api-Key ${apiKey}` })
            }
        };

        const requestOptions = { ...defaultOptions, ...options };
    
        try {
            const response = await fetch(url, requestOptions);
            const data = await response.json();
        
            if (!response.ok) {
                throw new Error(data.message || 'API request failed');
            }
        
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
 
    // Dataset-specific functions
    async function getDatasets(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/datasets/${queryString ? '?' + queryString : ''}`;
        return await apiRequest(endpoint);
    }

    async function getDataset(id) {
        return await apiRequest(`/datasets/${id}/`);
    }

    async function downloadDataset(id) {
        const response = await fetch(`https://afridata.com/api/v1/datasets/${id}/download/`, {
            headers: {
                'Authorization': `Api-Key ${apiKey}`
            }
        });
    
        if (!response.ok) {
            throw new Error('Download failed');
        }
    
        return response.blob();
    }

    async function uploadDataset(formData) {
        return await apiRequest('/datasets/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                ...(apiKey && { 'Authorization': `Api-Key ${apiKey}` })
            }
        });
    }


    // Comment functions
    async function postComment(datasetId, content) {
        return await apiRequest(`/comment/${datasetId}/post/`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }

    async function upvoteComment(commentId) {
        return await apiRequest(`/comment/${commentId}/upvote/`, {
            method: 'POST'
        });
    }
 
    // Usage statistics (mock data)
    function updateUsageStats() {
        // In a real application, this would fetch actual usage data from your API
        const stats = {
            requestsToday: Math.floor(Math.random() * 500) + 200,
            requestsThisMonth: Math.floor(Math.random() * 20000) + 10000,
            errorRate: (Math.random() * 2).toFixed(1),
            popularEndpoint: '/datasets/'
        };
    
        // Update the UI with these stats
        console.log('Usage stats updated:', stats);
    }

    // Initialize usage stats update
    setInterval(updateUsageStats, 30000); // Update every 30 seconds

    // Export functions for potential use in other scripts
    window.AfriDataAPI = {
        getDatasets,
        getDataset,
        downloadDataset,
        uploadDataset,
        postComment,
        upvoteComment,
        testEndpoint,
        copyToClipboard,
        showNotification
    };

