"""
URL list manager for the LLM Web Scraper and Processor.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from .utils import DATA_DIR, generate_id, load_json, save_json

# Constants
URL_LISTS_FILE = DATA_DIR / "url_lists.json"


class UrlListManager:
    """Manager for URL lists."""
    
    def __init__(self):
        """Initialize the URL list manager."""
        self.url_lists_file = URL_LISTS_FILE
    
    def get_lists(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all URL lists from the URL lists file.
        
        Returns:
            Dictionary containing all URL lists, keyed by ID.
        """
        return load_json(self.url_lists_file)
    
    def get_list(self, list_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific URL list by ID.
        
        Args:
            list_id: ID of the URL list to retrieve.
            
        Returns:
            Dictionary containing the URL list, or None if not found.
        """
        lists = self.get_lists()
        return lists.get(list_id)
    
    def create_list(self, name: str, urls: List[str], search_response: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new URL list.
        
        Args:
            name: Name of the URL list.
            urls: List of URLs to include.
            search_response: Optional Tavily search response data.
            
        Returns:
            ID of the created URL list.
        """
        list_id = generate_id()
        lists = self.get_lists()
        
        # Remove duplicates and empty URLs
        cleaned_urls = list(set(url.strip() for url in urls if url.strip()))
        
        lists[list_id] = {
            "id": list_id,
            "name": name,
            "urls": cleaned_urls,
            "search_response": search_response,
            "created_at": datetime.now().isoformat()
        }
        
        save_json(self.url_lists_file, lists)
        logger.info(f"Created URL list: {name} with {len(cleaned_urls)} URLs (ID: {list_id})")
        return list_id
    
    def create_list_from_tavily_response(self, name: str, response: Dict[str, Any]) -> str:
        """
        Create a URL list from a Tavily search response.
        
        Args:
            name: Name of the URL list.
            response: Tavily search response.
            
        Returns:
            ID of the created URL list.
        """
        # Extract URLs from Tavily search response
        try:
            results = response.get("results", [])
            urls = [result.get("url") for result in results if "url" in result]
            
            return self.create_list(name, urls, search_response=response)
        except Exception as e:
            logger.error(f"Error creating URL list from Tavily response: {e}")
            return self.create_list(name, [])
    
    def update_list(self, list_id: str, name: Optional[str] = None, urls: Optional[List[str]] = None) -> bool:
        """
        Update an existing URL list.
        
        Args:
            list_id: ID of the URL list to update.
            name: New name for the URL list (if provided).
            urls: New list of URLs (if provided).
            
        Returns:
            True if successful, False otherwise.
        """
        lists = self.get_lists()
        
        if list_id not in lists:
            logger.error(f"URL list {list_id} not found for update")
            return False
        
        # Update only provided fields
        if name is not None:
            lists[list_id]["name"] = name
        
        if urls is not None:
            # Remove duplicates and empty URLs
            cleaned_urls = list(set(url.strip() for url in urls if url.strip()))
            lists[list_id]["urls"] = cleaned_urls
        
        lists[list_id]["updated_at"] = datetime.now().isoformat()
        
        save_json(self.url_lists_file, lists)
        logger.info(f"Updated URL list: {lists[list_id]['name']} (ID: {list_id})")
        return True
    
    def delete_list(self, list_id: str) -> bool:
        """
        Delete a URL list.
        
        Args:
            list_id: ID of the URL list to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        lists = self.get_lists()
        
        if list_id not in lists:
            logger.error(f"URL list {list_id} not found for deletion")
            return False
        
        list_name = lists[list_id]["name"]
        del lists[list_id]
        
        save_json(self.url_lists_file, lists)
        logger.info(f"Deleted URL list: {list_name} (ID: {list_id})")
        return True
    
    def add_urls_to_list(self, list_id: str, urls: List[str]) -> bool:
        """
        Add URLs to an existing URL list.
        
        Args:
            list_id: ID of the URL list to update.
            urls: List of URLs to add.
            
        Returns:
            True if successful, False otherwise.
        """
        url_list = self.get_list(list_id)
        
        if not url_list:
            logger.error(f"URL list {list_id} not found for adding URLs")
            return False
        
        existing_urls = set(url_list.get("urls", []))
        new_urls = set(url.strip() for url in urls if url.strip())
        
        # Combine the lists and remove duplicates
        updated_urls = list(existing_urls | new_urls)
        
        return self.update_list(list_id, urls=updated_urls)
    
    def remove_urls_from_list(self, list_id: str, urls: List[str]) -> bool:
        """
        Remove URLs from an existing URL list.
        
        Args:
            list_id: ID of the URL list to update.
            urls: List of URLs to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        url_list = self.get_list(list_id)
        
        if not url_list:
            logger.error(f"URL list {list_id} not found for removing URLs")
            return False
        
        existing_urls = set(url_list.get("urls", []))
        urls_to_remove = set(url.strip() for url in urls if url.strip())
        
        # Remove specified URLs
        updated_urls = list(existing_urls - urls_to_remove)
        
        return self.update_list(list_id, urls=updated_urls) 