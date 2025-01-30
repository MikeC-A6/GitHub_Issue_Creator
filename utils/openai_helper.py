import os
import json
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def process_issue_description(description):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at formatting GitHub issues.
Given a description, create a well-structured issue with a clear title and detailed markdown-formatted body.
Include relevant sections like Description, Steps to Reproduce, Expected Behavior, etc. as appropriate.

Return a JSON response in exactly this format:
{
    "title": "Brief, clear issue title",
    "body": "Full markdown-formatted issue body"
}"""
                },
                {
                    "role": "user",
                    "content": f"Create a GitHub issue from this description and format it as JSON: {description}"
                }
            ],
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            if not isinstance(result, dict) or 'title' not in result or 'body' not in result:
                raise ValueError("Invalid response format from OpenAI")
            return result
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse OpenAI response as JSON: {str(e)}")

    except Exception as e:
        raise Exception(f"Failed to process issue description: {str(e)}")

def generate_github_graphql_query(operation_type, params):
    """Generate a GitHub GraphQL query using GPT-4o."""
    try:
        tools = [{
            "type": "function",
            "function": {
                "name": "create_graphql_query",
                "description": "Generate a GitHub GraphQL query based on the operation type and parameters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The complete GraphQL query string"
                        },
                        "variables": {
                            "type": "object",
                            "description": "Variables to be used in the query"
                        }
                    },
                    "required": ["query", "variables"]
                },
                "strict": True
            }
        }]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in GitHub's GraphQL API.
Generate precise and efficient GraphQL queries following GitHub's schema.
For mutations, always include minimal necessary fields in the response."""
                },
                {
                    "role": "user",
                    "content": f"Generate a GraphQL query for {operation_type}. Parameters: {json.dumps(params)}"
                }
            ],
            tools=tools,
            response_format={"type": "json_object"}
        )

        query_data = json.loads(response.choices[0].message.content)
        return query_data["query"], query_data["variables"]

    except Exception as e:
        raise Exception(f"Failed to generate GraphQL query: {str(e)}")