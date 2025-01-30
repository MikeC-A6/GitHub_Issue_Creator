import os
import logging
from flask import Flask, render_template, request, jsonify
from agents.github_issue_agent import GitHubIssueAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# Initialize the GitHub Issue Agent
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

github_issue_agent = GitHubIssueAgent(openai_api_key)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/create_issue', methods=['POST'])
def create_issue():
    """Handle issue creation requests."""
    try:
        # Validate input
        data = request.json
        required_fields = ['repo_url', 'description', 'github_token']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Process the request using our agent
        result = github_issue_agent.process({
            "description": data['description'],
            "repo_url": data['repo_url'],
            "github_token": data['github_token']
        })
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
