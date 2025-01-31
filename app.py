import os
import logging
import json
import queue
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session
from utils.github import create_github_issue, validate_github_token
from utils.gemini_helper import process_issue_description

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Use a strong secret key in production
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Store progress updates for each session
progress_queues = {}
progress_cleanup = {}

def cleanup_old_sessions():
    """Remove progress queues for sessions older than 5 minutes"""
    current_time = datetime.now()
    to_remove = []
    for session_id, timestamp in progress_cleanup.items():
        if current_time - timestamp > timedelta(minutes=5):
            to_remove.append(session_id)
    
    for session_id in to_remove:
        if session_id in progress_queues:
            del progress_queues[session_id]
        del progress_cleanup[session_id]

@app.route('/')
def index():
    return render_template('index.html', github_token=session.get('github_token', ''))

@app.route('/token', methods=['POST'])
def save_token():
    """Save or validate the GitHub token"""
    token = request.json.get('token')
    if not token:
        session.pop('github_token', None)
        return jsonify({'status': 'success', 'message': 'Token cleared'})
    
    try:
        # Validate the token before saving
        if validate_github_token(token):
            session['github_token'] = token
            return jsonify({
                'status': 'success',
                'message': 'Token saved successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid GitHub token'
            }), 400
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error validating token'
        }), 400

@app.route('/token', methods=['DELETE'])
def clear_token():
    """Clear the stored GitHub token"""
    session.pop('github_token', None)
    return jsonify({'status': 'success', 'message': 'Token cleared'})

def send_progress_update(session_id, step, error=None, complete=False):
    """Send a progress update to the client"""
    if session_id in progress_queues:
        progress_queues[session_id].put({
            'step': step,
            'error': error,
            'complete': complete
        })

@app.route('/progress/<session_id>')
def progress(session_id):
    """SSE endpoint for progress updates"""
    cleanup_old_sessions()
    
    if session_id not in progress_queues:
        progress_queues[session_id] = queue.Queue()
        progress_cleanup[session_id] = datetime.now()

    def generate():
        q = progress_queues[session_id]
        while True:
            try:
                progress_data = q.get(timeout=30)  # 30 second timeout
                if progress_data.get('complete') or progress_data.get('error'):
                    break
                yield f"data: {json.dumps(progress_data)}\n\n"
            except queue.Empty:
                break
        
        # Clean up the queue
        if session_id in progress_queues:
            del progress_queues[session_id]
        if session_id in progress_cleanup:
            del progress_cleanup[session_id]
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/create_issue', methods=['POST'])
def create_issue():
    try:
        data = request.json
        session_id = data.get('session_id')
        repo_url = data.get('repo_url')
        description = data.get('description')
        github_token = data.get('github_token') or session.get('github_token')
        code_context = data.get('code_context', '')

        if not all([repo_url, description]):
            return jsonify({
                'error': 'Missing required fields',
                'step': 'validation',
                'status': 'error'
            }), 400

        if not github_token:
            return jsonify({
                'error': 'GitHub token is required',
                'step': 'validation',
                'status': 'error'
            }), 400

        try:
            # Process the description with Gemini
            send_progress_update(session_id, 'processing_description')
            processed_issue = process_issue_description(description, code_context)
            
            # Update progress for GraphQL query generation
            send_progress_update(session_id, 'generating_query')
            
            # Create the issue using GitHub GraphQL API
            send_progress_update(session_id, 'fetching_repo')
            
            # Submitting the issue
            send_progress_update(session_id, 'submitting_issue')
            result = create_github_issue(
                repo_url=repo_url,
                title=processed_issue['title'],
                body=processed_issue['body'],
                token=github_token
            )
            
            # Mark as complete
            send_progress_update(session_id, 'completed', complete=True)
            result['status'] = 'success'
            result['step'] = 'completed'
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error in GitHub API call: {str(e)}")
            error_msg = 'Failed to create GitHub issue'
            send_progress_update(session_id, 'submitting_issue', error=str(e))
            return jsonify({
                'error': error_msg,
                'step': 'submitting_issue',
                'status': 'error',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error creating issue: {str(e)}")
        if session_id:
            send_progress_update(session_id, 'unknown', error=str(e))
        return jsonify({
            'error': str(e),
            'step': 'unknown',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)