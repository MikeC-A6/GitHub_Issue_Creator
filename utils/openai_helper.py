import os
import json
import logging
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
    """Generate a GitHub GraphQL query using GPT-4o with schema awareness."""
    try:
        schema_info = params.pop('schema_info', None)
        schema_context = ""
        if schema_info:
            schema_context = f"\nHere is the relevant schema information:\n{json.dumps(schema_info, indent=2)}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert in GitHub's GraphQL API.
Generate precise and efficient GraphQL queries following GitHub's schema.
For mutations, always include minimal necessary fields in the response.{schema_context}

For repository_id_query, generate a query like this:
query GetRepositoryId($owner: String!, $name: String!) {{
    repository(owner: $owner, name: $name) {{
        id
    }}
}}

For create_issue_mutation, generate a mutation like this:
mutation CreateIssue($repositoryId: ID!, $title: String!, $body: String!) {{
    createIssue(input: {{
        repositoryId: $repositoryId
        title: $title
        body: $body
    }}) {{
        issue {{
            url
            number
        }}
    }}
}}

Format your response as a JSON object with two fields:
1. 'query': The complete GraphQL query string (properly formatted with correct indentation)
2. 'variables': An object containing the variables for the query"""
                },
                {
                    "role": "user",
                    "content": f"Generate a GraphQL query for {operation_type}. Parameters: {json.dumps(params)}"
                }
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        if not isinstance(result, dict) or 'query' not in result or 'variables' not in result:
            raise ValueError("Invalid response format from OpenAI")

        # Clean up the query string
        result['query'] = result['query'].strip()
        logging.debug(f"Generated GraphQL query: {result['query']}")
        logging.debug(f"Variables: {result['variables']}")

        return result['query'], result['variables']

    except Exception as e:
        raise Exception(f"Failed to generate GraphQL query: {str(e)}")