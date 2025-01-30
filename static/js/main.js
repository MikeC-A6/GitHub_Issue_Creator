// Form validation and enhancement
document.addEventListener('DOMContentLoaded', function() {
    // Enhanced form validation
    const form = document.getElementById('issueForm');
    if (form) {
        enhanceFormValidation(form);
    }
    
    // Initialize any tooltips or popovers
    initializeTooltips();
});

function enhanceFormValidation(form) {
    const inputs = form.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
        // Real-time validation
        input.addEventListener('input', function() {
            validateInput(this);
        });
        
        // Blur validation
        input.addEventListener('blur', function() {
            validateInput(this);
        });
    });
    
    // GitHub URL validation
    const repoUrlInput = form.querySelector('#repo_url');
    if (repoUrlInput) {
        repoUrlInput.addEventListener('input', function() {
            validateGitHubUrl(this);
        });
    }
}

function validateInput(input) {
    const isValid = input.checkValidity();
    
    if (isValid) {
        input.classList.remove('border-red-300');
        input.classList.add('border-gray-300');
        
        // Clear any existing error message
        const errorDiv = input.parentElement.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    } else {
        input.classList.remove('border-gray-300');
        input.classList.add('border-red-300');
        
        // Show error message if not already present
        if (!input.parentElement.querySelector('.error-message')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message mt-1 text-sm text-red-600';
            errorDiv.textContent = input.validationMessage;
            input.parentElement.appendChild(errorDiv);
        }
    }
}

function validateGitHubUrl(input) {
    const url = input.value.trim();
    const githubPattern = /^https:\/\/github\.com\/[\w-]+\/[\w-]+\/?$/;
    
    if (url && !githubPattern.test(url)) {
        input.setCustomValidity('Please enter a valid GitHub repository URL');
    } else {
        input.setCustomValidity('');
    }
    
    validateInput(input);
}

function initializeTooltips() {
    // Add any tooltip initialization here if needed
    // This is a placeholder for future enhancement
}

// Status message handling
function updateStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    const statusMessage = document.getElementById('statusMessage');
    
    if (statusDiv && statusMessage) {
        statusMessage.textContent = message;
        
        // Show the status
        statusDiv.classList.remove('hidden');
        
        // Auto-hide after 5 seconds if it's a success or error message
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }
}

// Form submission handling
async function handleFormSubmission(formData) {
    try {
        updateStatus('Creating issue...', 'info');
        
        const response = await fetch('/create_issue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create issue');
        }
        
        // Show success message
        updateStatus('Issue created successfully!', 'success');
        
        // Update UI with issue link
        const issueLink = document.getElementById('issueLink');
        if (issueLink) {
            issueLink.href = data.url;
            document.getElementById('result').classList.remove('hidden');
        }
        
        return true;
        
    } catch (error) {
        updateStatus(error.message, 'error');
        return false;
    }
}

// Export functions for use in other scripts if needed
window.githubIssueCreator = {
    handleFormSubmission,
    updateStatus,
    validateGitHubUrl
};
