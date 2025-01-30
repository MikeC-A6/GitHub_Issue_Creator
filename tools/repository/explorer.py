import os
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def search_repository(query: str, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search through repository files for relevant content.
    
    Args:
        query: Search query to find relevant files and code
        file_patterns: List of file patterns to filter search (e.g. ['*.py', '*.md']). 
                      Pass empty list or None to search all files.
        
    Returns:
        Dict containing search results with relevance scores and snippets
    """
    try:
        # Ensure file_patterns is always a list (even if empty)
        patterns = file_patterns if file_patterns is not None else []
        
        # This is a placeholder - you should implement actual search logic
        # Could use grep, ripgrep, or other search tools
        # Could also use semantic search with embeddings for better results
        
        # Mock response for now
        return {
            "matches": [
                {
                    "file": "example.py",
                    "line": 10,
                    "snippet": "def example_function():",
                    "score": 0.95,
                    "patterns_matched": patterns  # Include which patterns matched
                }
            ],
            "patterns_used": patterns  # Include which patterns were used in search
        }
    except Exception as e:
        logger.error(f"Error searching repository: {str(e)}")
        raise

def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read contents of a specific file from the repository.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Dict containing file contents and metadata
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(path, 'r') as f:
            content = f.read()
            
        return {
            "content": content,
            "size": path.stat().st_size,
            "last_modified": path.stat().st_mtime
        }
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise 