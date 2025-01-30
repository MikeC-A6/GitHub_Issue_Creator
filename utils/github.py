import re
from urllib.parse import urlparse
import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def extract_repo_info(repo_url):
    """Extract owner and repo name from GitHub URL."""
    parsed = urlparse(repo_url)
    if parsed.netloc != "github.com":
        raise ValueError("Invalid GitHub repository URL")
    
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) < 2:
        raise ValueError("Invalid repository path")
    
    return path_parts[0], path_parts[1]

def create_github_issue(repo_url, title, body, token):
    """Create a GitHub issue using GraphQL API."""
    try:
        owner, repo = extract_repo_info(repo_url)
        
        # GraphQL mutation query
        query = """
        mutation CreateIssue($repositoryId: ID!, $title: String!, $body: String!) {
            createIssue(input: {
                repositoryId: $repositoryId,
                title: $title,
                body: $body
            }) {
                issue {
                    url
                    number
                }
            }
        }
        """
        
        # First, get the repository ID
        repo_query = """
        query GetRepositoryId($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                id
            }
        }
        """
        
        headers = {
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
        }
        
        # Get repository ID
        repo_response = requests.post(
            GITHUB_GRAPHQL_URL,
            headers=headers,
            json={
                "query": repo_query,
                "variables": {
                    "owner": owner,
                    "name": repo
                }
            }
        )
        
        repo_data = repo_response.json()
        if "errors" in repo_data:
            raise Exception(repo_data["errors"][0]["message"])
            
        repository_id = repo_data["data"]["repository"]["id"]
        
        # Create the issue
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            headers=headers,
            json={
                "query": query,
                "variables": {
                    "repositoryId": repository_id,
                    "title": title,
                    "body": body
                }
            }
        )
        
        data = response.json()
        if "errors" in data:
            raise Exception(data["errors"][0]["message"])
            
        issue_data = data["data"]["createIssue"]["issue"]
        return {
            "success": True,
            "url": issue_data["url"],
            "number": issue_data["number"]
        }
        
    except Exception as e:
        raise Exception(f"Failed to create GitHub issue: {str(e)}")
