from typing import Dict, Any, List, Optional
from openai import OpenAI
import logging
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.conversation_history = []

    def add_to_history(self, role: str, content: Optional[str], tool_call_id: Optional[str] = None, tool_calls: Optional[List[Any]] = None, tool_name: Optional[str] = None):
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender (system, user, assistant, function)
            content: The message content (can be None for assistant messages with tool calls)
            tool_call_id: For function responses, the ID of the tool call this is responding to
            tool_calls: For assistant messages, the list of tool calls being made
            tool_name: For function responses, the name of the function that was called
        """
        if role == "tool":  # Convert "tool" role to "function" for OpenAI
            if not tool_call_id:
                self.logger.error("Function responses must include a tool_call_id")
                return
            if not tool_name:
                self.logger.error("Function responses must include a tool_name")
                return
            message = {
                "role": "function",
                "name": tool_name,
                "content": content,
                "tool_call_id": tool_call_id
            }
        elif role == "assistant" and tool_calls:
            # Assistant message with tool calls
            message = {
                "role": "assistant",
                "content": content,  # Must be None when using tool calls
                "tool_calls": tool_calls
            }
        else:
            # Regular message (system, user, or assistant without tool calls)
            message = {
                "role": role,
                "content": content
            }

        self.logger.debug(f"Adding message to history: {message}")
        self.conversation_history.append(message)

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return a response."""
        pass

    def call_llm(self, 
                messages: List[Dict[str, Any]], 
                tools: Optional[List[Dict[str, Any]]] = None,
                tool_choice: str = "auto") -> Dict[str, Any]:
        """Make a call to the LLM with proper error handling."""
        try:
            self.logger.debug(f"Calling LLM with messages: {messages}")
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use the latest model
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
            return {
                "success": True,
                "response": response
            }
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @abstractmethod
    def execute_tool(self, tool_call: Any) -> Dict[str, Any]:
        """Execute a tool call and return the result.

        Args:
            tool_call: A ChatCompletionMessageToolCall object containing the tool call details

        Returns:
            Dict containing:
                success: bool indicating if the tool execution was successful
                data: The result data if successful
                error: Error message if unsuccessful
                name: The name of the tool that was called
                tool_call_id: The ID of the tool call for proper response tracking
        """
        pass