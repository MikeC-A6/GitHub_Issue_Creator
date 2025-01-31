import os
import logging
from flask import Flask, render_template, request, jsonify
from utils.github import create_github_issue
from utils.gemini_helper import process_issue_description

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_issue', methods=['POST'])
def create_issue():
    try:
        data = request.json
        repo_url = data.get('repo_url')
        description = data.get('description')
        github_token = data.get('github_token')
        code_context = data.get('code_context', '')

        if not all([repo_url, description, github_token]):
            return jsonify({
                'error': 'Missing required fields',
                'step': 'validation',
                'status': 'error'
            }), 400

        try:
            # Process the description with Gemini
            processed_issue = process_issue_description(description, code_context)
        except Exception as e:
            logger.error(f"Error processing description: {str(e)}")
            return jsonify({
                'error': 'Failed to process issue description',
                'step': 'processing_description',
                'status': 'error',
                'details': str(e)
            }), 500

        try:
            # Create the issue using GitHub GraphQL API
            result = create_github_issue(
                repo_url=repo_url,
                title=processed_issue['title'],
                body=processed_issue['body'],
                token=github_token
            )
            result['status'] = 'success'
            result['step'] = 'completed'
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in GitHub API call: {str(e)}")
            return jsonify({
                'error': 'Failed to create GitHub issue',
                'step': 'submitting_issue',
                'status': 'error',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error creating issue: {str(e)}")
        return jsonify({
            'error': str(e),
            'step': 'unknown',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)