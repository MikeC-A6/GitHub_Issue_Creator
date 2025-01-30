import os
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
                    "content": (
                        "You are an expert at formatting GitHub issues. "
                        "Given a description, create a well-structured issue with a "
                        "clear title and detailed markdown-formatted body. Include "
                        "relevant sections like Description, Steps to Reproduce, "
                        "Expected Behavior, etc. as appropriate. "
                        "Return your response as a JSON object with 'title' and 'body' fields."
                    )
                },
                {
                    "role": "user", 
                    "content": (
                        f"Create a GitHub issue from this description and return it as JSON: {description}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content
        return {
            "title": result["title"],
            "body": result["body"]
        }
    except Exception as e:
        raise Exception(f"Failed to process issue description: {str(e)}")