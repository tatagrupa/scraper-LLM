"""
Prompt manager for the LLM Web Scraper and Processor.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .utils import DATA_DIR, generate_id, load_json, save_json

# Constants
PROMPTS_FILE = DATA_DIR / "prompts.json"


class PromptManager:
    """Manager for LLM prompts."""
    
    def __init__(self):
        """Initialize the prompt manager."""
        self.prompts_file = PROMPTS_FILE
    
    def get_prompts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all prompts from the prompts file.
        
        Returns:
            Dictionary containing all prompts, keyed by ID.
        """
        return load_json(self.prompts_file)
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific prompt by ID.
        
        Args:
            prompt_id: ID of the prompt to retrieve.
            
        Returns:
            Dictionary containing the prompt, or None if not found.
        """
        prompts = self.get_prompts()
        return prompts.get(prompt_id)
    
    def create_prompt(self, name: str, content: str, output_format: str = "json") -> str:
        """
        Create a new prompt.
        
        Args:
            name: Name of the prompt.
            content: Content of the prompt.
            output_format: Format for LLM output ("json" or "markdown").
            
        Returns:
            ID of the created prompt.
        """
        if output_format not in ["json", "markdown"]:
            logger.warning(f"Invalid output format: {output_format}. Using 'json'")
            output_format = "json"
        
        prompt_id = generate_id()
        prompts = self.get_prompts()
        
        prompts[prompt_id] = {
            "id": prompt_id,
            "name": name,
            "content": content,
            "output_format": output_format,
            "created_at": datetime.now().isoformat()
        }
        
        save_json(self.prompts_file, prompts)
        logger.info(f"Created prompt: {name} (ID: {prompt_id})")
        return prompt_id
    
    def update_prompt(self, prompt_id: str, name: Optional[str] = None, 
                      content: Optional[str] = None, output_format: Optional[str] = None) -> bool:
        """
        Update an existing prompt.
        
        Args:
            prompt_id: ID of the prompt to update.
            name: New name for the prompt (if provided).
            content: New content for the prompt (if provided).
            output_format: New output format for the prompt (if provided).
            
        Returns:
            True if successful, False otherwise.
        """
        prompts = self.get_prompts()
        
        if prompt_id not in prompts:
            logger.error(f"Prompt {prompt_id} not found for update")
            return False
        
        # Update only provided fields
        if name is not None:
            prompts[prompt_id]["name"] = name
        
        if content is not None:
            prompts[prompt_id]["content"] = content
        
        if output_format is not None:
            if output_format not in ["json", "markdown"]:
                logger.warning(f"Invalid output format: {output_format}. Ignoring")
            else:
                prompts[prompt_id]["output_format"] = output_format
        
        prompts[prompt_id]["updated_at"] = datetime.now().isoformat()
        
        save_json(self.prompts_file, prompts)
        logger.info(f"Updated prompt: {prompts[prompt_id]['name']} (ID: {prompt_id})")
        return True
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """
        Delete a prompt.
        
        Args:
            prompt_id: ID of the prompt to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        prompts = self.get_prompts()
        
        if prompt_id not in prompts:
            logger.error(f"Prompt {prompt_id} not found for deletion")
            return False
        
        prompt_name = prompts[prompt_id]["name"]
        del prompts[prompt_id]
        
        save_json(self.prompts_file, prompts)
        logger.info(f"Deleted prompt: {prompt_name} (ID: {prompt_id})")
        return True 