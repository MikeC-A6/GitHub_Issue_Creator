import os
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def process_issue_description(description, code_context=''):
    """Generate a well-formatted GitHub issue using Gemini."""
    try:
        # Prepare the context prompt
        context_prompt = ""
        if code_context:
            context_prompt = f"""
Here is the relevant code context to consider:
```
{code_context}
```

Please use this code context to create a more detailed and specific issue."""

        # Create the full prompt
        prompt = f"""You are an expert at formatting GitHub issues.
Given the following description and optional code context, create a well-structured issue with a clear title and detailed markdown-formatted body.
Follow this exact structure:

1. Title: Brief, descriptive, and specific
2. Description: Clear explanation of the current situation
3. Proposed Feature/Changes: Bullet points of what needs to be implemented
4. Benefits: List the advantages
5. Expected Behavior: Numbered steps of how it should work
6. Additional Information: Any other relevant details

IMPORTANT: 
- Do not include any external links
- Do not reference any issues or pull requests
- Keep all information factual and based only on the provided description and code context
- If code context is provided, use it to make the issue more specific and technical
- Include relevant code snippets from the context if they help explain the issue
- Format your response as a JSON object with two fields: "title" and "body"

Description: {description}

{context_prompt}"""

        # Generate content using Gemini
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        
        # Parse and validate the response
        content = response.text
        
        # Extract the JSON-like structure from the response
        # Remove any markdown formatting if present
        content = content.strip('`').strip()
        if content.startswith('json'):
            content = content[4:].strip()
            
        # Convert to Python dict
        import json
        result = json.loads(content)
        
        if not isinstance(result, dict) or 'title' not in result or 'body' not in result:
            raise ValueError("Invalid response format from Gemini")
            
        return result

    except Exception as e:
        raise Exception(f"Failed to process issue description with Gemini: {str(e)}")
