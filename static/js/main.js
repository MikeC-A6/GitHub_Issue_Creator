document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueForm');
    const submitButton = document.getElementById('submitButton');
    const resultDiv = document.getElementById('result');
    const alertDiv = resultDiv.querySelector('.alert');
    const toggleTokenBtn = document.getElementById('toggleToken');
    const tokenInput = document.getElementById('githubToken');
    const saveTokenBtn = document.getElementById('saveToken');
    const clearTokenBtn = document.getElementById('clearToken');
    const tokenAlert = document.getElementById('tokenAlert');
    let eventSource = null;

    // Initialize token state
    updateTokenState();

    // Token visibility toggle
    toggleTokenBtn.addEventListener('click', function() {
        const type = tokenInput.type === 'password' ? 'text' : 'password';
        tokenInput.type = type;
        toggleTokenBtn.innerHTML = `<i class="bi bi-eye${type === 'password' ? '' : '-slash'}"></i>`;
    });

    // Token management
    function updateTokenState() {
        const hasToken = tokenInput.value.trim() !== '';
        clearTokenBtn.style.display = hasToken ? 'inline-block' : 'none';
        saveTokenBtn.innerHTML = hasToken ? 
            '<i class="bi bi-check-circle me-1"></i>Update Token' : 
            '<i class="bi bi-check-circle me-1"></i>Save Token';
    }

    function showTokenAlert(message, type = 'success') {
        tokenAlert.className = `alert alert-${type}`;
        tokenAlert.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
        `;
        tokenAlert.style.display = 'block';
        setTimeout(() => {
            tokenAlert.style.display = 'none';
        }, 3000);
    }

    saveTokenBtn.addEventListener('click', async function() {
        const token = tokenInput.value.trim();
        if (!token) {
            showTokenAlert('Please enter a GitHub token', 'danger');
            return;
        }

        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token })
            });

            const data = await response.json();
            if (response.ok) {
                showTokenAlert(data.message);
                updateTokenState();
            } else {
                showTokenAlert(data.message, 'danger');
            }
        } catch (error) {
            showTokenAlert('Failed to save token', 'danger');
        }
    });

    clearTokenBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/token', {
                method: 'DELETE'
            });

            const data = await response.json();
            if (response.ok) {
                tokenInput.value = '';
                updateTokenState();
                showTokenAlert(data.message);
            }
        } catch (error) {
            showTokenAlert('Failed to clear token', 'danger');
        }
    });

    tokenInput.addEventListener('input', updateTokenState);

    // Create progress container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container mb-3';
    progressContainer.style.display = 'none';
    resultDiv.parentNode.insertBefore(progressContainer, resultDiv);

    const steps = {
        'processing_description': {
            message: 'Processing Description...',
            progress: 20,
            icon: 'chat-text'
        },
        'generating_query': {
            message: 'Generating GraphQL Query...',
            progress: 40,
            icon: 'code-square'
        },
        'fetching_repo': {
            message: 'Fetching Repository ID...',
            progress: 60,
            icon: 'git'
        },
        'submitting_issue': {
            message: 'Submitting Issue...',
            progress: 80,
            icon: 'arrow-up-circle'
        },
        'completed': {
            message: 'Issue Created!',
            progress: 100,
            icon: 'check-circle'
        }
    };

    function updateProgress(step, error = null) {
        progressContainer.style.display = 'block';
        let stepInfo = steps[step] || { 
            message: step,
            progress: 0,
            icon: 'question-circle'
        };
        
        let statusClass = error ? 'text-danger' : 'text-primary';
        let message = error ? `Error: ${error}` : stepInfo.message;
        let icon = error ? 'exclamation-circle' : stepInfo.icon;
        let progress = error ? stepInfo.progress : stepInfo.progress;
        
        // Update button state
        submitButton.innerHTML = `
            <span class="spinner-border spinner-border-sm ${error ? 'd-none' : ''}" role="status" aria-hidden="true"></span>
            <i class="bi bi-${icon} ${error ? '' : 'd-none'}"></i>
            ${message}
        `;
        
        // Update progress container with step list
        let stepsHtml = Object.entries(steps).map(([key, info]) => {
            let stepClass = '';
            if (key === step) {
                stepClass = error ? 'text-danger fw-bold' : 'text-primary fw-bold';
            } else if (getStepOrder(key) < getStepOrder(step)) {
                stepClass = 'text-success';
            } else {
                stepClass = 'text-muted';
            }
            
            return `
                <div class="step-item ${stepClass}">
                    <i class="bi bi-${key === step ? icon : info.icon} me-2"></i>
                    ${info.message}
                </div>
            `;
        }).join('');
        
        progressContainer.innerHTML = `
            <div class="steps-container mb-3">
                ${stepsHtml}
            </div>
            <div class="d-flex justify-content-between align-items-center">
                <div class="progress flex-grow-1">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         style="width: ${progress}%"></div>
                </div>
                <span class="${statusClass} ms-3">
                    <i class="bi bi-${icon} me-2"></i>${message}
                </span>
            </div>
        `;
    }

    function getStepOrder(step) {
        const order = {
            'processing_description': 1,
            'generating_query': 2,
            'fetching_repo': 3,
            'submitting_issue': 4,
            'completed': 5
        };
        return order[step] || 0;
    }

    function cleanupEventSource() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset and show loading state
        submitButton.disabled = true;
        resultDiv.style.display = 'none';
        alertDiv.style.display = 'none';
        progressContainer.style.display = 'block';
        
        // Clean up any existing event source
        cleanupEventSource();

        try {
            let codeContext = '';
            const codebaseFile = document.getElementById('codebaseFile').files[0];

            if (codebaseFile) {
                codeContext = await codebaseFile.text();
            }

            // Generate a unique session ID for this submission
            const sessionId = Date.now().toString();

            // Set up SSE connection first
            eventSource = new EventSource(`/progress/${sessionId}`);
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.step) {
                    updateProgress(data.step, data.error);
                }
                if (data.complete || data.error) {
                    cleanupEventSource();
                }
            };

            eventSource.onerror = function() {
                cleanupEventSource();
            };

            // Start with processing description
            updateProgress('processing_description');

            const response = await fetch('/create_issue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    repo_url: document.getElementById('repoUrl').value,
                    description: document.getElementById('description').value,
                    github_token: document.getElementById('githubToken').value,
                    code_context: codeContext
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Update progress to completed
                updateProgress('completed');
                
                // Show success message
                alertDiv.className = 'alert alert-success';
                alertDiv.innerHTML = `
                    <h5><i class="bi bi-check-circle me-2"></i>Issue Created Successfully!</h5>
                    <p>Your issue has been created. You can view it here:</p>
                    <a href="${data.url}" target="_blank" class="btn btn-outline-success">
                        <i class="bi bi-box-arrow-up-right me-2"></i>View Issue #${data.number}
                    </a>
                `;
                form.reset();
            } else {
                // Show error in progress and alert
                updateProgress(data.step || 'unknown', data.error);
                alertDiv.className = 'alert alert-danger';
                alertDiv.innerHTML = `
                    <h5><i class="bi bi-exclamation-triangle me-2"></i>Error Creating Issue</h5>
                    <p>${data.error}</p>
                    ${data.details ? `<p><small class="text-muted"><i class="bi bi-info-circle me-1"></i>Details: ${data.details}</small></p>` : ''}
                `;
            }
        } catch (error) {
            // Show error message
            updateProgress('unknown', 'An unexpected error occurred');
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = `
                <h5><i class="bi bi-exclamation-triangle me-2"></i>Error</h5>
                <p>An error occurred while creating the issue.</p>
            `;
        } finally {
            // Reset button state but keep progress visible
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Create Issue';
            resultDiv.style.display = 'block';
            alertDiv.style.display = 'block';
            cleanupEventSource();
        }
    });

    // Real-time validation with improved feedback
    const repoUrlInput = document.getElementById('repoUrl');
    repoUrlInput.addEventListener('input', function() {
        const isValid = /^https:\/\/github\.com\/[\w-]+\/[\w-]+\/?$/.test(this.value);
        this.classList.remove('is-invalid', 'is-valid');
        if (this.value) {
            this.classList.add(isValid ? 'is-valid' : 'is-invalid');
            
            // Update feedback message
            let feedback = this.parentElement.querySelector('.invalid-feedback');
            if (!feedback && !isValid) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                this.parentElement.appendChild(feedback);
            }
            if (feedback) {
                feedback.innerHTML = '<i class="bi bi-exclamation-circle me-1"></i>Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)';
            }
        }
    });
});