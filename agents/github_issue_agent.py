import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from tools.github.issues import create_github_issue
from tools.repository.explorer import search_repository, read_file

class GitHubIssueAgent(BaseAgent):
    """Agent responsible for creating well-contextualized GitHub issues."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.tools = self._setup_tools()

    def _setup_tools(self) -> List[Dict[str, Any]]:
        """Setup the tools available to this agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_repository",
                    "description": "Search through repository files and code to gather context about a specific topic or area",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant files and code"
                            },
                            "file_patterns": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Optional file patterns to filter search results",
                                "default": []
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a specific file from the repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file in the repository"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_github_issue",
                    "description": "Create a new GitHub issue with the specified details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Issue title"
                            },
                            "body": {
                                "type": "string",
                                "description": "Detailed issue description with gathered context"
                            },
                            "labels": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Optional labels to apply to the issue",
                                "default": []
                            }
                        },
                        "required": ["title", "body"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_call: Any) -> Dict[str, Any]:
        """Execute the specified tool call."""
        try:
            # Extract tool name and arguments using dot notation for ChatCompletionMessageToolCall
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Execute the appropriate tool function
            if name == "search_repository":
                # Set default empty list for file_patterns if not provided
                args.setdefault('file_patterns', [])
                result = search_repository(**args)
            elif name == "read_file":
                result = read_file(**args)
            elif name == "create_github_issue":
                # Set default empty list for labels if not provided
                args.setdefault('labels', [])
                result = create_github_issue(**args)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return {
                "success": True,
                "data": result,
                "name": name,
                "tool_call_id": tool_call.id  # Include the tool call ID for proper response tracking
            }

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error executing tool {name if 'name' in locals() else 'unknown'}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "name": name if 'name' in locals() else 'unknown',
                "tool_call_id": getattr(tool_call, 'id', None)  # Include the tool call ID even in error case
            }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input request and generate a response."""
        # Initialize conversation if needed
        if not self.conversation_history:
            self.add_to_history("system", """You are an expert at creating detailed GitHub issues.
Your goal is to gather relevant context from the repository and create a well-structured issue.
Follow these steps:
1. Analyze the user's request
2. Search the repository for relevant context
3. Read specific files if needed
4. Create a detailed issue with the gathered context""")

        # Handle input data - support both "message" and "description" keys for backwards compatibility
        user_input = input_data.get("message", input_data.get("description", ""))
        if not user_input:
            return {
                "success": False,
                "error": "No input message or description provided"
            }

        # Add user input to conversation history
        self.add_to_history("user", user_input)

        # Call LLM with conversation history and available tools
        llm_response = self.call_llm(
            messages=self.conversation_history,
            tools=self.tools
        )

        if not llm_response["success"]:
            return {"success": False, "error": llm_response["error"]}

        message = llm_response["response"].choices[0].message

        # Handle assistant's message
        if message.tool_calls:
            # Add assistant message with tool calls first
            self.add_to_history(
                role="assistant",
                content=None,  # Must be None when using tool calls
                tool_calls=[{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in message.tool_calls]
            )

            # Process each tool call and add its response immediately
            error_occurred = False
            error_message = None
            
            for tool_call in message.tool_calls:
                # Execute the tool
                tool_result = self.execute_tool(tool_call)
                
                # Always add the response to maintain the conversation flow
                self.add_to_history(
                    role="function",  # Use "function" role directly instead of "tool"
                    content=str(tool_result["data"]) if tool_result["success"] else f"Error: {tool_result['error']}",
                    tool_call_id=tool_result["tool_call_id"],
                    tool_name=tool_result["name"]
                )
                
                # Track error but don't return immediately
                if not tool_result["success"]:
                    error_occurred = True
                    error_message = tool_result["error"]
                    break  # Stop processing more tools if one fails
            
            # After all responses are added, handle success/failure
            if error_occurred:
                return {
                    "success": False,
                    "error": error_message
                }
            
            # Continue the conversation
            return self.process({"message": "Continue with the previous request"})
        else:
            # Regular assistant message without tool calls
            self.add_to_history("assistant", message.content)
            
            # Return success response with assistant's message
            return {
                "success": True,
                "response": message.content if message.content else "Task completed successfully"
            }