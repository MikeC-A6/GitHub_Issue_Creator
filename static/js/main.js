document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueForm');
    const submitButton = document.getElementById('submitButton');
    const resultDiv = document.getElementById('result');
    const alertDiv = resultDiv.querySelector('.alert');

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
        
        submitButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${message}`;
        
        // Update progress container
        progressContainer.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="progress flex-grow-1 mx-2" style="height: 2px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: ${step === 'completed' ? '100' : '75'}%"></div>
                </div>
                <span class="${statusClass}">${message}</span>
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
                    <h5>Issue Created Successfully!</h5>
                    <p>Your issue has been created. You can view it here:</p>
                    <a href="${data.url}" target="_blank" class="btn btn-outline-success">
                        View Issue #${data.number}
                    </a>
                `;
                form.reset();
            } else {
                // Show error in progress and alert
                updateProgress(data.step || 'unknown', data.error);
                alertDiv.className = 'alert alert-danger';
                alertDiv.innerHTML = `
                    <h5>Error Creating Issue</h5>
                    <p>${data.error}</p>
                    ${data.details ? `<p><small class="text-muted">Details: ${data.details}</small></p>` : ''}
                `;
            }
        } catch (error) {
            // Show error message
            updateProgress('unknown', 'An unexpected error occurred');
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = 'An error occurred while creating the issue.';
        } finally {
            // Reset button state but keep progress visible
            submitButton.disabled = false;
            submitButton.textContent = 'Create Issue';
            resultDiv.style.display = 'block';
            alertDiv.style.display = 'block';
        }
    });

    // Real-time validation
    const repoUrlInput = document.getElementById('repoUrl');
    repoUrlInput.addEventListener('input', function() {
        const isValid = /^https:\/\/github\.com\/[\w-]+\/[\w-]+\/?$/.test(this.value);
        if (isValid) {
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
        } else {
            this.classList.remove('is-valid');
            this.classList.add('is-invalid');
        }
    });
});