import os
import logging
from flask import Flask, render_template, request, jsonify
from utils.github import create_github_issue
from utils.openai_helper import process_issue_description

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

        if not all([repo_url, description, github_token]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Process the description with GPT-4o
        processed_issue = process_issue_description(description)
        
        # Create the issue using GitHub GraphQL API
        result = create_github_issue(
            repo_url=repo_url,
            title=processed_issue['title'],
            body=processed_issue['body'],
            token=github_token
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
