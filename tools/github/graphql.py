from typing import Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

def get_schema_info(token: str, type_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get GraphQL schema information using introspection.
    
    Args:
        token: GitHub API token
        type_name: Optional specific type to query
        
    Returns:
        Dict containing schema information
    """
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }

    if type_name:
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

    return execute_graphql_query(query, variables, token)

def execute_graphql_query(query: str, variables: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Execute a GraphQL query against GitHub's API.
    
    Args:
        query: GraphQL query string
        variables: Query variables
        token: GitHub API token
        
    Returns:
        Dict containing query results
    """
    try:
        headers = {
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            GITHUB_GRAPHQL_URL,
            headers=headers,
            json={
                "query": query,
                "variables": variables
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.text}")
            
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")
            
        return data
        
    except Exception as e:
        logger.error(f"GraphQL query failed: {str(e)}")
        raise 