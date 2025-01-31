document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueForm');
    const submitButton = document.getElementById('submitButton');
    const resultDiv = document.getElementById('result');
    const alertDiv = resultDiv.querySelector('.alert');
    const toggleTokenBtn = document.getElementById('toggleToken');
    const tokenInput = document.getElementById('githubToken');

    // Token visibility toggle
    toggleTokenBtn.addEventListener('click', function() {
        const type = tokenInput.type === 'password' ? 'text' : 'password';
        tokenInput.type = type;
        toggleTokenBtn.innerHTML = `<i class="bi bi-eye${type === 'password' ? '' : '-slash'}"></i>`;
    });

    // Create progress container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container mb-3';
    progressContainer.style.display = 'none';
    resultDiv.parentNode.insertBefore(progressContainer, resultDiv);

    const steps = {
        'processing_description': 'Processing Description...',
        'generating_query': 'Generating GraphQL Query...',
        'fetching_repo': 'Fetching Repository ID...',
        'submitting_issue': 'Submitting Issue...',
        'completed': 'Issue Created!'
    };

    function updateProgress(step, error = null) {
        progressContainer.style.display = 'block';
        let statusClass = error ? 'text-danger' : 'text-primary';
        let message = error ? `Error: ${error}` : (steps[step] || step);
        let icon = error ? 'exclamation-circle' : 'arrow-right-circle';
        
        submitButton.innerHTML = `
            <span class="spinner-border spinner-border-sm ${error ? 'd-none' : ''}" role="status" aria-hidden="true"></span>
            <i class="bi bi-${icon} ${error ? '' : 'd-none'}"></i>
            ${message}
        `;
        
        // Update progress container
        progressContainer.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="progress flex-grow-1 mx-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         style="width: ${step === 'completed' ? '100' : '75'}%"></div>
                </div>
                <span class="${statusClass}">
                    <i class="bi bi-${icon} me-2"></i>${message}
                </span>
            </div>
        `;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Reset and show loading state
        submitButton.disabled = true;
        resultDiv.style.display = 'none';
        progressContainer.style.display = 'block';
        updateProgress('processing_description');

        try {
            let codeContext = '';
            const codebaseFile = document.getElementById('codebaseFile').files[0];

            if (codebaseFile) {
                codeContext = await codebaseFile.text();
            }

            const response = await fetch('/create_issue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
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