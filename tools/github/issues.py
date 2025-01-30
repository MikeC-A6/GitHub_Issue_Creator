import json
from typing import Dict, Any, Optional, List
import requests
from urllib.parse import urlparse
import logging
from .graphql import get_schema_info, execute_graphql_query

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def extract_repo_info(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    parsed = urlparse(repo_url)
    if parsed.netloc != "github.com":
        raise ValueError("Invalid GitHub repository URL")

    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) < 2:
        raise ValueError("Invalid repository path")

    return path_parts[0], path_parts[1]

def create_github_issue(
    repo_url: str,
    title: str,
    body: str,
    token: str,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a GitHub issue using GraphQL API.
    
    Args:
        repo_url: Full GitHub repository URL
        title: Issue title
        body: Issue body/description
        token: GitHub API token
        labels: List of labels to apply to the issue. Pass empty list if no labels needed.
        
    Returns:
        Dict containing issue URL and number
    """
    try:
        owner, repo = extract_repo_info(repo_url)
        
        # Ensure labels is always a list
        label_list = labels if labels is not None else []
        
        # Get repository ID
        repo_query = """
        query GetRepositoryId($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                id
                labels(first: 100) {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        
        repo_variables = {
            "owner": owner,
            "name": repo
        }
        
        repo_result = execute_graphql_query(repo_query, repo_variables, token)
        repository_id = repo_result["data"]["repository"]["id"]
        
        # Get label IDs if labels are provided
        available_labels = {
            label["name"]: label["id"] 
            for label in repo_result["data"]["repository"]["labels"]["nodes"]
        }
        
        label_ids = [
            available_labels[label]
            for label in label_list
            if label in available_labels
        ]
        
        # Create issue mutation
        create_mutation = """
        mutation CreateIssue($input: CreateIssueInput!) {
            createIssue(input: $input) {
                issue {
                    url
                    number
                }
            }
        }
        """
        
        mutation_variables = {
            "input": {
                "repositoryId": repository_id,
                "title": title,
                "body": body,
                "labelIds": label_ids
            }
        }
            
        result = execute_graphql_query(create_mutation, mutation_variables, token)
        issue_data = result["data"]["createIssue"]["issue"]
        
        return {
            "success": True,
            "url": issue_data["url"],
            "number": issue_data["number"],
            "labels_applied": label_list
        }
        
    except Exception as e:
        logger.error(f"Failed to create GitHub issue: {str(e)}")
        raise 