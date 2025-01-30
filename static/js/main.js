document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('issueForm');
    const submitButton = document.getElementById('submitButton');
    const resultDiv = document.getElementById('result');
    const alertDiv = resultDiv.querySelector('.alert');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';

        // Hide previous results
        resultDiv.style.display = 'none';

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
                // Show error message
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = data.error || 'An error occurred while creating the issue.';
            }
        } catch (error) {
            // Show error message
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = 'An error occurred while creating the issue.';
        } finally {
            // Reset button state
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