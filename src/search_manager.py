"""
Search manager for the LLM Web Scraper and Processor.

Handles integration with Tavily search API.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from tavily import TavilyClient

from .settings_manager import SettingsManager
from .url_list_manager import UrlListManager
from .utils import DATA_DIR, generate_id, load_json, save_json

# Constants
SEARCHES_FILE = DATA_DIR / "searches.json"


class SearchManager:
    """Manager for Tavily searches."""
    
    def __init__(self):
        """Initialize the search manager."""
        self.searches_file = SEARCHES_FILE
        self.settings_manager = SettingsManager()
        self.url_list_manager = UrlListManager()
        
        api_keys = self.settings_manager.get_api_keys()
        self.tavily_api_key = api_keys.get("tavily", os.getenv("TAVILY_API_KEY", ""))
        
        # Check if API key is available
        if not self.tavily_api_key:
            logger.warning("Tavily API key not found. Set TAVILY_API_KEY environment variable.")
    
    def get_searches(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all searches from the searches file.
        
        Returns:
            Dictionary containing all searches, keyed by ID.
        """
        return load_json(self.searches_file)
    
    def get_search(self, search_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific search by ID.
        
        Args:
            search_id: ID of the search to retrieve.
            
        Returns:
            Dictionary containing the search, or None if not found.
        """
        searches = self.get_searches()
        return searches.get(search_id)
    
    async def perform_search_async(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a search using Tavily's API.
        
        Args:
            query: Search query.
            **kwargs: Additional search parameters.
            
        Returns:
            Tavily search response.
        """
        if not self.tavily_api_key:
            raise ValueError("Tavily API key not found. Set TAVILY_API_KEY environment variable.")
        
        # Get settings and merge with provided kwargs
        tavily_settings = self.settings_manager.get_active_settings().get("tavily", {})
        
        # Use settings as defaults, but allow override from kwargs
        search_params = {**tavily_settings, **kwargs}
        
        # Create client and perform search
        try:
            client = TavilyClient(api_key=self.tavily_api_key)
            response = client.search(query=query, **search_params)
            return response
        except Exception as e:
            logger.error(f"Error performing Tavily search: {e}")
            raise
    
    def perform_search(self, query: str, save_results: bool = True, create_url_list: bool = False, 
                       url_list_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Perform a search using Tavily.
        
        Args:
            query: Search query.
            save_results: Whether to save search results.
            create_url_list: Whether to create a URL list from search results.
            url_list_name: Name for the URL list (if creating one).
            **kwargs: Additional search parameters.
            
        Returns:
            Tavily search response.
        """
        # Run async search in sync context
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.perform_search_async(query, **kwargs))
        finally:
            loop.close()
        
        search_id = None
        if save_results:
            search_id = self._save_search_results(query, response, kwargs)
        
        # Create URL list if requested
        if create_url_list and response:
            list_name = url_list_name or f"Search: {query[:30]}..."
            url_list_id = self.url_list_manager.create_list_from_tavily_response(list_name, response)
            
            # If we saved the search, link it to the URL list
            if search_id:
                searches = self.get_searches()
                if search_id in searches:
                    searches[search_id]["url_list_id"] = url_list_id
                    save_json(self.searches_file, searches)
        
        return response
    
    def _save_search_results(self, query: str, response: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Save search results to the searches file.
        
        Args:
            query: Search query.
            response: Tavily search response.
            params: Search parameters.
            
        Returns:
            ID of the saved search.
        """
        search_id = generate_id()
        searches = self.get_searches()
        
        searches[search_id] = {
            "id": search_id,
            "query": query,
            "parameters": params,
            "response": response,
            "created_at": datetime.now().isoformat()
        }
        
        save_json(self.searches_file, searches)
        logger.info(f"Saved search results for query: {query} (ID: {search_id})")
        return search_id
    
    def delete_search(self, search_id: str) -> bool:
        """
        Delete a search.
        
        Args:
            search_id: ID of the search to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        searches = self.get_searches()
        
        if search_id not in searches:
            logger.error(f"Search {search_id} not found for deletion")
            return False
        
        query = searches[search_id].get("query", "Unknown")
        del searches[search_id]
        
        save_json(self.searches_file, searches)
        logger.info(f"Deleted search: {query} (ID: {search_id})")
        return True 