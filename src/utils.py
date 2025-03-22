"""
Utility functions for the LLM Web Scraper and Processor.
"""

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

# Set up logger
logger.add("logs/app.log", rotation="10 MB", level="INFO", retention="1 week")

# Constants
DATA_DIR = Path("../data").resolve()
CACHE_DIR = Path("../cache").resolve()


def ensure_directories() -> None:
    """Ensure that data and cache directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the data from the JSON file.
    """
    file_path = Path(file_path)
    try:
        if not file_path.exists():
            # If file doesn't exist, create it with an empty dictionary
            save_json(file_path, {})
            return {}
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return {}


def save_json(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        data: Data to save.
        
    Returns:
        True if successful, False otherwise.
    """
    file_path = Path(file_path)
    try:
        # Ensure parent directory exists
        os.makedirs(file_path.parent, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False


def hash_url(url: str) -> str:
    """
    Create a hash of a URL for use as a cache filename.
    
    Args:
        url: The URL to hash.
        
    Returns:
        SHA-256 hash of the URL.
    """
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def save_to_cache(url: str, content: Dict[str, Any]) -> bool:
    """
    Save scraped content to cache.
    
    Args:
        url: The URL that was scraped.
        content: The scraped content to cache.
        
    Returns:
        True if successful, False otherwise.
    """
    url_hash = hash_url(url)
    cache_file = CACHE_DIR / f"{url_hash}.json"
    
    data = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "content": content
    }
    
    return save_json(cache_file, data)


def get_from_cache(url: str, cache_timeout_hours: int = 24) -> Optional[Dict[str, Any]]:
    """
    Get content from cache if it exists and is not expired.
    
    Args:
        url: The URL to retrieve from cache.
        cache_timeout_hours: Maximum age of cache in hours.
        
    Returns:
        Cached content if available and not expired, None otherwise.
    """
    url_hash = hash_url(url)
    cache_file = CACHE_DIR / f"{url_hash}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        data = load_json(cache_file)
        timestamp = datetime.fromisoformat(data["timestamp"])
        now = datetime.now()
        
        # Check if cache is expired
        age_hours = (now - timestamp).total_seconds() / 3600
        if age_hours > cache_timeout_hours:
            logger.info(f"Cache for {url} is expired ({age_hours:.1f} hours old)")
            return None
        
        logger.info(f"Using cached content for {url} ({age_hours:.1f} hours old)")
        return data["content"]
    except Exception as e:
        logger.error(f"Error retrieving from cache for {url}: {e}")
        return None


def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        Unique ID string based on current timestamp and a random component.
    """
    return f"{int(time.time())}-{hashlib.md5(os.urandom(8)).hexdigest()[:8]}"


# Initialize directories when module is imported
ensure_directories() 