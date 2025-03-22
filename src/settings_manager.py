"""
Settings manager for the LLM Web Scraper and Processor.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from loguru import logger

from .utils import DATA_DIR, generate_id, load_json, save_json

# Load environment variables
load_dotenv()

# Constants
SETTINGS_FILE = DATA_DIR / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "scraping": {
        "latency_seconds": 2,
        "timeout_seconds": 30,
        "max_concurrent_tasks": 3,
        "cache_timeout_hours": 24,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "headless": True,
        "proxy": "",  # Format: ip:port:username:password
        "rotate_proxies": False,
        "proxy_list": []  # List of proxy strings in the same format
    },
    "llm": {
        "openai": {
            "model": "gpt-4",
            "temperature": 0.0,
            "max_tokens": 1000
        },
        "google": {
            "model": "gemini-2.0-flash",
            "temperature": 0.0,
            "max_tokens": 1000
        }
    },
    "tavily": {
        "search_depth": "basic",
        "max_results": 10,
        "include_domains": [],
        "exclude_domains": [],
        "include_images": False,
        "include_answer": False,
        "include_raw_content": False
    }
}


class SettingsManager:
    """Manager for application settings."""
    
    def __init__(self):
        """Initialize the settings manager."""
        self.settings_file = SETTINGS_FILE
        
        # Ensure settings file exists with at least default values
        if not os.path.exists(self.settings_file):
            self.save_settings("default", DEFAULT_SETTINGS)
    
    def get_settings(self, profile_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get settings from the settings file.
        
        Args:
            profile_id: ID of the settings profile to retrieve. If None, returns all profiles.
            
        Returns:
            Dictionary containing the settings.
        """
        settings_data = load_json(self.settings_file)
        
        if profile_id is None:
            return settings_data
        
        if profile_id in settings_data:
            return settings_data[profile_id]
        else:
            # If profile doesn't exist, return default settings
            logger.warning(f"Settings profile {profile_id} not found, using default")
            return DEFAULT_SETTINGS
    
    def save_settings(self, profile_name: str, settings: Dict[str, Any]) -> str:
        """
        Save settings to the settings file.
        
        Args:
            profile_name: Name of the settings profile.
            settings: Settings to save.
            
        Returns:
            ID of the saved settings profile.
        """
        settings_data = load_json(self.settings_file)
        
        # Check if profile already exists by name
        existing_id = None
        for profile_id, profile in settings_data.items():
            if profile.get("name") == profile_name:
                existing_id = profile_id
                break
        
        if existing_id:
            profile_id = existing_id
        else:
            profile_id = generate_id()
        
        # Add/update settings with metadata
        settings_data[profile_id] = {
            "id": profile_id,
            "name": profile_name,
            "created_at": datetime.now().isoformat(),
            "settings": settings
        }
        
        save_json(self.settings_file, settings_data)
        return profile_id
    
    def update_settings(self, profile_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update an existing settings profile.
        
        Args:
            profile_id: ID of the settings profile to update.
            settings: New settings to save.
            
        Returns:
            True if successful, False otherwise.
        """
        settings_data = load_json(self.settings_file)
        
        if profile_id not in settings_data:
            logger.error(f"Settings profile {profile_id} not found for update")
            return False
        
        # Preserve metadata
        name = settings_data[profile_id].get("name", "Unknown")
        created_at = settings_data[profile_id].get("created_at", datetime.now().isoformat())
        
        settings_data[profile_id] = {
            "id": profile_id,
            "name": name,
            "created_at": created_at,
            "updated_at": datetime.now().isoformat(),
            "settings": settings
        }
        
        return save_json(self.settings_file, settings_data)
    
    def delete_settings(self, profile_id: str) -> bool:
        """
        Delete a settings profile.
        
        Args:
            profile_id: ID of the settings profile to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        settings_data = load_json(self.settings_file)
        
        if profile_id not in settings_data:
            logger.error(f"Settings profile {profile_id} not found for deletion")
            return False
        
        del settings_data[profile_id]
        return save_json(self.settings_file, settings_data)
    
    def get_active_settings(self) -> Dict[str, Any]:
        """
        Get the active settings profile.
        
        Returns:
            Dictionary containing the active settings.
        """
        settings_data = load_json(self.settings_file)
        
        # Get the active profile ID, or use 'default' if not set
        active_profile_id = settings_data.get("active_profile_id", "default")
        
        if active_profile_id in settings_data:
            return settings_data[active_profile_id].get("settings", DEFAULT_SETTINGS)
        else:
            logger.warning(f"Active settings profile {active_profile_id} not found, using default")
            return DEFAULT_SETTINGS
    
    def set_active_profile(self, profile_id: str) -> bool:
        """
        Set the active settings profile.
        
        Args:
            profile_id: ID of the settings profile to set as active.
            
        Returns:
            True if successful, False otherwise.
        """
        settings_data = load_json(self.settings_file)
        
        if profile_id not in settings_data:
            logger.error(f"Settings profile {profile_id} not found for setting as active")
            return False
        
        settings_data["active_profile_id"] = profile_id
        return save_json(self.settings_file, settings_data)
    
    def get_api_keys(self) -> Dict[str, str]:
        """
        Get API keys from environment variables.
        
        Returns:
            Dictionary containing the API keys.
        """
        return {
            "tavily": os.getenv("TAVILY_API_KEY", ""),
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "google": os.getenv("GOOGLE_API_KEY", "")
        } 