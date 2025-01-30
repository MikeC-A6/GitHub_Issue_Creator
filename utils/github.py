import re
from urllib.parse import urlparse
import requests
from .openai_helper import generate_github_graphql_query

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def get_schema_info(token, type_name=None):
    """Get GraphQL schema information using introspection."""
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }

    if type_name:
        # Query specific type
        query = """
        query TypeInfo($name: String!) {
            __type(name: $name) {
                name
                kind
                description
                fields {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                    args {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"name": type_name}
    else:
        # Query schema overview
        query = """
        query {
            __schema {
                types {
                    name
                    kind
                    description
                    fields {
                        name
                    }
                }
            }
        }
        """
        variables = {}

    response = requests.post(
        GITHUB_GRAPHQL_URL,
        headers=headers,
        json={"query": query, "variables": variables}
    )

    if response.status_code != 200:
        raise Exception(f"Failed to fetch schema: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL schema error: {data['errors']}")

    return data["data"]

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
    """Create a GitHub issue using GraphQL API with dynamic query generation."""
    try:
        owner, repo = extract_repo_info(repo_url)

        # Get schema information for Repository type
        repo_schema = get_schema_info(token, "Repository")

        # Get schema information for CreateIssuePayload type
        mutation_schema = get_schema_info(token, "CreateIssuePayload")

        # First, get repository ID using schema-aware query generation
        repo_query, repo_variables = generate_github_graphql_query(
            "repository_id_query",
            {
                "owner": owner,
                "name": repo,
                "schema_info": repo_schema
            }
        )

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
                "variables": repo_variables
            }
        )

        repo_data = repo_response.json()
        if "errors" in repo_data:
            raise Exception(repo_data["errors"][0]["message"])

        repository_id = repo_data["data"]["repository"]["id"]

        # Generate the create issue mutation query with schema awareness
        create_query, create_variables = generate_github_graphql_query(
            "create_issue_mutation",
            {
                "repositoryId": repository_id,
                "title": title,
                "body": body,
                "schema_info": mutation_schema
            }
        )

        # Create the issue
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            headers=headers,
            json={
                "query": create_query,
                "variables": create_variables
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