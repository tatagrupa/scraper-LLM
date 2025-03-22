"""
Main application for the LLM Web Scraper and Processor.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from .extractor import Extractor
from .prompt_manager import PromptManager
from .search_manager import SearchManager
from .settings_manager import SettingsManager
from .url_list_manager import UrlListManager
from .utils import ensure_directories

# Ensure required directories exist
ensure_directories()

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Set page config
st.set_page_config(
    page_title="LLM Web Scraper and Processor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Prompt Management"

if "background_tasks" not in st.session_state:
    st.session_state.background_tasks = {}

if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = {}

if "processing_results" not in st.session_state:
    st.session_state.processing_results = {}

# Initialize settings
settings_manager = SettingsManager()
if not settings_manager.get_settings():
    settings_manager.save_settings("default", settings_manager.get_active_settings())
    settings_manager.set_active_profile("default")

def check_api_keys() -> Dict[str, bool]:
    """Check if API keys are set and return their status."""
    settings_manager = SettingsManager()
    api_keys = settings_manager.get_api_keys()
    
    return {
        "tavily": bool(api_keys.get("tavily", "")),
        "openai": bool(api_keys.get("openai", "")),
        "google": bool(api_keys.get("google", ""))
    }


def run_background_task(task_id: str, func, *args, **kwargs):
    """Run a task in the background and update session state."""
    try:
        st.session_state["background_tasks"][task_id] = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "progress": 0
        }
        
        result = func(*args, **kwargs)
        
        st.session_state["background_tasks"][task_id] = {
            "status": "completed",
            "start_time": st.session_state["background_tasks"][task_id]["start_time"],
            "end_time": datetime.now().isoformat(),
            "progress": 100,
            "result": result
        }
        
        return result
    except Exception as e:
        logger.error(f"Background task {task_id} failed: {e}")
        st.session_state["background_tasks"][task_id] = {
            "status": "failed",
            "start_time": st.session_state["background_tasks"][task_id]["start_time"],
            "end_time": datetime.now().isoformat(),
            "progress": 100,
            "error": str(e)
        }
        raise


def get_background_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a background task."""
    return st.session_state["background_tasks"].get(task_id, {"status": "not_found"})


def display_sidebar():
    """Display the sidebar navigation."""
    st.sidebar.title("🔍 LLM Web Scraper")
    
    # Check API keys
    api_key_status = check_api_keys()
    
    # Display API key status
    st.sidebar.subheader("API Key Status")
    for api, status in api_key_status.items():
        if status:
            st.sidebar.success(f"✅ {api.capitalize()}")
        else:
            st.sidebar.error(f"❌ {api.capitalize()}")
    
    # Display navigation
    st.sidebar.subheader("Navigation")
    tabs = [
        "Prompt Management",
        "Search Management",
        "URL List Management",
        "Settings",
        "Extraction",
        "LLM Processing",
    ]
    
    selected_tab = st.sidebar.radio("Select a page:", tabs, index=tabs.index(st.session_state["active_tab"]))
    
    if selected_tab != st.session_state["active_tab"]:
        st.session_state["active_tab"] = selected_tab
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This application integrates Tavily search, Selenium web scraping, "
        "and LLM processing to extract and analyze data from websites."
    )


def prompt_management_page():
    """Display the prompt management page."""
    st.title("Prompt Management")
    
    prompt_manager = PromptManager()
    prompts = prompt_manager.get_prompts()
    
    # Tabs for viewing and creating/editing prompts
    tab1, tab2 = st.tabs(["View Prompts", "Create/Edit Prompt"])
    
    with tab1:
        if not prompts:
            st.info("No prompts found. Create a new prompt in the 'Create/Edit Prompt' tab.")
        else:
            # Convert prompts to a list of dictionaries for display
            prompt_list = []
            for prompt_id, prompt in prompts.items():
                prompt_data = {
                    "ID": prompt_id,
                    "Name": prompt.get("name", ""),
                    "Format": prompt.get("output_format", "json"),
                    "Created": prompt.get("created_at", "")
                }
                prompt_list.append(prompt_data)
            
            # Display prompts in a dataframe
            df = pd.DataFrame(prompt_list)
            st.dataframe(df, use_container_width=True)
            
            # Prompt details
            with st.expander("Prompt Details"):
                selected_prompt_id = st.selectbox("Select a prompt:", list(prompts.keys()))
                if selected_prompt_id:
                    prompt = prompts[selected_prompt_id]
                    st.text_area("Prompt Content", prompt.get("content", ""), height=200)
                    
                    # Delete button
                    if st.button("Delete Prompt"):
                        if prompt_manager.delete_prompt(selected_prompt_id):
                            st.success(f"Prompt '{prompt.get('name')}' deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to delete prompt.")
    
    with tab2:
        st.subheader("Create or Edit Prompt")
        
        # Edit existing prompt or create new
        edit_mode = st.checkbox("Edit existing prompt")
        
        if edit_mode and prompts:
            prompt_id = st.selectbox("Select prompt to edit:", list(prompts.keys()))
            prompt = prompts[prompt_id]
            name = st.text_input("Prompt Name", value=prompt.get("name", ""))
            content = st.text_area("Prompt Content", value=prompt.get("content", ""), height=300)
            output_format = st.selectbox("Output Format", ["json", "markdown"], index=0 if prompt.get("output_format", "json") == "json" else 1)
            
            if st.button("Update Prompt"):
                if prompt_manager.update_prompt(prompt_id, name, content, output_format):
                    st.success(f"Prompt '{name}' updated successfully.")
                else:
                    st.error("Failed to update prompt.")
        else:
            name = st.text_input("Prompt Name")
            content = st.text_area("Prompt Content", height=300)
            output_format = st.selectbox("Output Format", ["json", "markdown"])
            
            if st.button("Create Prompt"):
                if name and content:
                    prompt_id = prompt_manager.create_prompt(name, content, output_format)
                    st.success(f"Prompt '{name}' created successfully.")
                else:
                    st.error("Please provide a name and content for the prompt.")


def settings_page():
    """Display the settings page."""
    st.title("Settings")
    
    settings_manager = SettingsManager()
    all_settings = settings_manager.get_settings()
    
    # Remove special keys from display
    display_settings = {k: v for k, v in all_settings.items() if k != "active_profile_id"}
    
    # Get active profile
    active_profile_id = all_settings.get("active_profile_id", "default")
    
    # Tabs for viewing and editing settings
    tab1, tab2, tab3 = st.tabs(["View Settings", "Create/Edit Settings", "API Keys"])
    
    with tab1:
        if not display_settings:
            st.info("No settings profiles found. Create a new profile in the 'Create/Edit Settings' tab.")
        else:
            # Convert settings to a list for display
            settings_list = []
            for profile_id, profile in display_settings.items():
                settings_data = {
                    "ID": profile_id,
                    "Name": profile.get("name", "Unknown"),
                    "Created": profile.get("created_at", ""),
                    "Active": "✓" if profile_id == active_profile_id else ""
                }
                settings_list.append(settings_data)
            
            # Display settings in a dataframe
            df = pd.DataFrame(settings_list)
            st.dataframe(df, use_container_width=True)
            
            # Settings details
            with st.expander("Settings Details"):
                selected_profile_id = st.selectbox("Select a profile:", list(display_settings.keys()))
                if selected_profile_id:
                    profile = display_settings[selected_profile_id]
                    settings = profile.get("settings", {})
                    
                    # Display settings as JSON
                    st.json(settings)
                    
                    # Set as active profile
                    col1, col2 = st.columns(2)
                    with col1:
                        if selected_profile_id != active_profile_id:
                            if st.button("Set as Active Profile"):
                                if settings_manager.set_active_profile(selected_profile_id):
                                    st.success(f"Profile '{profile.get('name')}' set as active.")
                                    st.rerun()
                                else:
                                    st.error("Failed to set profile as active.")
                    
                    # Delete profile
                    with col2:
                        if selected_profile_id != "default":  # Don't allow deleting default profile
                            if st.button("Delete Profile"):
                                if settings_manager.delete_settings(selected_profile_id):
                                    st.success(f"Profile '{profile.get('name')}' deleted successfully.")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete profile.")
    
    with tab2:
        st.subheader("Create or Edit Settings Profile")
        
        # Edit existing profile or create new
        edit_mode = st.checkbox("Edit existing profile")
        
        if edit_mode and display_settings:
            profile_id = st.selectbox("Select profile to edit:", list(display_settings.keys()))
            profile = display_settings[profile_id]
            name = st.text_input("Profile Name", value=profile.get("name", ""))
            settings = profile.get("settings", {})
            
            # Scraping settings
            st.subheader("Scraping Settings")
            scraping_settings = settings.get("scraping", {})
            col1, col2 = st.columns(2)
            with col1:
                latency = st.number_input("Latency (seconds)", min_value=0.0, max_value=10.0, value=float(scraping_settings.get("latency_seconds", 2)), step=0.5)
                timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=int(scraping_settings.get("timeout_seconds", 30)))
                cache_timeout = st.number_input("Cache Timeout (hours)", min_value=1, max_value=168, value=int(scraping_settings.get("cache_timeout_hours", 24)))
            with col2:
                max_tasks = st.number_input("Max Concurrent Tasks", min_value=1, max_value=10, value=int(scraping_settings.get("max_concurrent_tasks", 3)))
                user_agent = st.text_input("User Agent", value=scraping_settings.get("user_agent", ""))
                headless = st.checkbox("Headless Mode", value=bool(scraping_settings.get("headless", True)))
            
            # LLM settings
            st.subheader("LLM Settings")
            llm_settings = settings.get("llm", {})
            
            # OpenAI settings
            openai_settings = llm_settings.get("openai", {})
            st.write("OpenAI Settings")
            col1, col2, col3 = st.columns(3)
            with col1:
                openai_model = st.text_input("Model", value=openai_settings.get("model", "gpt-4"))
            with col2:
                openai_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(openai_settings.get("temperature", 0.0)), step=0.1)
            with col3:
                openai_tokens = st.number_input("Max Tokens", min_value=100, max_value=4000, value=int(openai_settings.get("max_tokens", 1000)))
            
            # Google settings
            google_settings = llm_settings.get("google", {})
            st.write("Google Gemini Settings")
            col1, col2, col3 = st.columns(3)
            with col1:
                google_model = st.text_input("Model", value=google_settings.get("model", "gemini-pro"), key="google_model")
            with col2:
                google_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(google_settings.get("temperature", 0.0)), step=0.1, key="google_temp")
            with col3:
                google_tokens = st.number_input("Max Tokens", min_value=100, max_value=4000, value=int(google_settings.get("max_tokens", 1000)), key="google_tokens")
            
            # Tavily settings
            st.subheader("Tavily Search Settings")
            tavily_settings = settings.get("tavily", {})
            col1, col2 = st.columns(2)
            with col1:
                search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=0 if tavily_settings.get("search_depth", "basic") == "basic" else 1)
                max_results = st.number_input("Max Results", min_value=1, max_value=20, value=int(tavily_settings.get("max_results", 10)))
                include_domains = st.text_area("Include Domains (one per line)", value="\n".join(tavily_settings.get("include_domains", [])))
            with col2:
                exclude_domains = st.text_area("Exclude Domains (one per line)", value="\n".join(tavily_settings.get("exclude_domains", [])))
                include_images = st.checkbox("Include Images", value=bool(tavily_settings.get("include_images", False)))
                include_answer = st.checkbox("Include Answer", value=bool(tavily_settings.get("include_answer", False)))
                include_raw = st.checkbox("Include Raw Content", value=bool(tavily_settings.get("include_raw_content", False)))
            
            # Proxy settings
            st.subheader("Proxy Settings")
            scraping_settings["proxy"] = st.text_input(
                "Default Proxy (format: ip:port:username:password)",
                value=scraping_settings.get("proxy", ""),
                help="Example: 38.154.227.167:5868:ernkyfgk:rg1odve9ocpj"
            )
            scraping_settings["rotate_proxies"] = st.checkbox(
                "Rotate through proxy list",
                value=scraping_settings.get("rotate_proxies", False)
            )
            proxy_list = "\n".join(scraping_settings.get("proxy_list", []))
            proxy_list = st.text_area(
                "Proxy List (one per line, same format as above)",
                value=proxy_list,
                height=150,
                help="Enter multiple proxies, one per line"
            )
            scraping_settings["proxy_list"] = [p.strip() for p in proxy_list.split("\n") if p.strip()]
            
            # Create updated settings dictionary
            updated_settings = {
                "scraping": {
                    "latency_seconds": latency,
                    "timeout_seconds": timeout,
                    "max_concurrent_tasks": max_tasks,
                    "cache_timeout_hours": cache_timeout,
                    "user_agent": user_agent,
                    "headless": headless,
                    "proxy": scraping_settings["proxy"],
                    "rotate_proxies": scraping_settings["rotate_proxies"],
                    "proxy_list": scraping_settings["proxy_list"]
                },
                "llm": {
                    "openai": {
                        "model": openai_model,
                        "temperature": openai_temp,
                        "max_tokens": openai_tokens
                    },
                    "google": {
                        "model": google_model,
                        "temperature": google_temp,
                        "max_tokens": google_tokens
                    }
                },
                "tavily": {
                    "search_depth": search_depth,
                    "max_results": max_results,
                    "include_domains": [domain.strip() for domain in include_domains.split("\n") if domain.strip()],
                    "exclude_domains": [domain.strip() for domain in exclude_domains.split("\n") if domain.strip()],
                    "include_images": include_images,
                    "include_answer": include_answer,
                    "include_raw_content": include_raw
                }
            }
            
            # Update button
            if st.button("Update Settings"):
                if settings_manager.update_settings(profile_id, updated_settings):
                    st.success(f"Settings profile '{name}' updated successfully.")
                    st.rerun()
                else:
                    st.error("Failed to update settings profile.")
        
        else:
            # Create new profile
            name = st.text_input("Profile Name")
            
            if name:
                # Use default settings as a starting point
                default_settings = settings_manager.get_active_settings()
                
                # Scraping settings
                st.subheader("Scraping Settings")
                scraping_settings = default_settings.get("scraping", {})
                col1, col2 = st.columns(2)
                with col1:
                    latency = st.number_input("Latency (seconds)", min_value=0.0, max_value=10.0, value=float(scraping_settings.get("latency_seconds", 2)), step=0.5)
                    timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=int(scraping_settings.get("timeout_seconds", 30)))
                    cache_timeout = st.number_input("Cache Timeout (hours)", min_value=1, max_value=168, value=int(scraping_settings.get("cache_timeout_hours", 24)))
                with col2:
                    max_tasks = st.number_input("Max Concurrent Tasks", min_value=1, max_value=10, value=int(scraping_settings.get("max_concurrent_tasks", 3)))
                    user_agent = st.text_input("User Agent", value=scraping_settings.get("user_agent", ""))
                    headless = st.checkbox("Headless Mode", value=bool(scraping_settings.get("headless", True)))
                
                # Create new settings dictionary
                new_settings = {
                    "scraping": {
                        "latency_seconds": latency,
                        "timeout_seconds": timeout,
                        "max_concurrent_tasks": max_tasks,
                        "cache_timeout_hours": cache_timeout,
                        "user_agent": user_agent,
                        "headless": headless
                    },
                    "llm": default_settings.get("llm", {}),
                    "tavily": default_settings.get("tavily", {})
                }
                
                # Create button
                if st.button("Create Settings Profile"):
                    profile_id = settings_manager.save_settings(name, new_settings)
                    st.success(f"Settings profile '{name}' created successfully.")
                    st.rerun()
            else:
                st.warning("Please provide a name for the settings profile.")
    
    with tab3:
        st.subheader("API Keys")
        
        # Display API key configuration instructions
        st.write("""
        API keys are stored as environment variables for security. 
        To set up your API keys, create a `.env` file in the project root with the following:
        ```
        TAVILY_API_KEY=your_tavily_api_key_here
        OPENAI_API_KEY=your_openai_api_key_here
        GOOGLE_API_KEY=your_google_api_key_here
        ```
        """)
        
        # Display current API key status
        api_key_status = check_api_keys()
        for api, status in api_key_status.items():
            if status:
                st.success(f"{api.capitalize()} API key is configured.")
            else:
                st.error(f"{api.capitalize()} API key is not configured.")


def url_list_management_page():
    """Display the URL list management page."""
    st.title("URL List Management")
    
    url_list_manager = UrlListManager()
    url_lists = url_list_manager.get_lists()
    
    # Tabs for viewing and creating/editing URL lists
    tab1, tab2 = st.tabs(["View URL Lists", "Create/Edit URL List"])
    
    with tab1:
        if not url_lists:
            st.info("No URL lists found. Create a new URL list in the 'Create/Edit URL List' tab.")
        else:
            # Convert URL lists to a list of dictionaries for display
            list_data = []
            for list_id, url_list in url_lists.items():
                url_count = len(url_list.get("urls", []))
                list_item = {
                    "ID": list_id,
                    "Name": url_list.get("name", ""),
                    "URLs": url_count,
                    "Created": url_list.get("created_at", "")
                }
                list_data.append(list_item)
            
            # Display URL lists in a dataframe
            df = pd.DataFrame(list_data)
            st.dataframe(df, use_container_width=True)
            
            # URL list details
            with st.expander("URL List Details"):
                selected_list_id = st.selectbox("Select a URL list:", list(url_lists.keys()))
                if selected_list_id:
                    url_list = url_lists[selected_list_id]
                    urls = url_list.get("urls", [])
                    
                    # Display URLs
                    st.subheader(f"URLs in '{url_list.get('name')}'")
                    
                    for i, url in enumerate(urls):
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            st.text(url)
                        with col2:
                            st.write(f"{i+1}")
                    
                    # Search response details (if available)
                    search_response = url_list.get("search_response")
                    if search_response:
                        with st.expander("Search Response Details"):
                            st.json(search_response)
                    
                    # Delete button
                    if st.button("Delete URL List"):
                        if url_list_manager.delete_list(selected_list_id):
                            st.success(f"URL list '{url_list.get('name')}' deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to delete URL list.")
    
    with tab2:
        st.subheader("Create or Edit URL List")
        
        # Edit existing list or create new
        edit_mode = st.checkbox("Edit existing URL list")
        
        if edit_mode and url_lists:
            list_id = st.selectbox("Select URL list to edit:", list(url_lists.keys()))
            url_list = url_lists[list_id]
            name = st.text_input("URL List Name", value=url_list.get("name", ""))
            urls_text = st.text_area(
                "URLs (one per line)", 
                value="\n".join(url_list.get("urls", [])), 
                height=300,
                help="Enter one URL per line."
            )
            
            if st.button("Update URL List"):
                urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
                if name and urls:
                    if url_list_manager.update_list(list_id, name, urls):
                        st.success(f"URL list '{name}' updated successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update URL list.")
                else:
                    st.error("Please provide a name and at least one URL.")
                    
            # Add URLs from text input
            st.subheader("Add URLs")
            additional_urls = st.text_area(
                "Additional URLs (one per line)",
                height=150,
                help="Enter one URL per line to add to the existing list."
            )
            
            if st.button("Add URLs"):
                urls_to_add = [url.strip() for url in additional_urls.split("\n") if url.strip()]
                if urls_to_add:
                    if url_list_manager.add_urls_to_list(list_id, urls_to_add):
                        st.success(f"Added {len(urls_to_add)} URLs to list '{name}'.")
                        st.rerun()
                    else:
                        st.error("Failed to add URLs to list.")
                else:
                    st.warning("No URLs provided to add.")
        else:
            name = st.text_input("URL List Name")
            urls_text = st.text_area(
                "URLs (one per line)", 
                height=300,
                help="Enter one URL per line."
            )
            
            if st.button("Create URL List"):
                urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
                if name and urls:
                    list_id = url_list_manager.create_list(name, urls)
                    st.success(f"URL list '{name}' created successfully with {len(urls)} URLs.")
                    st.rerun()
                else:
                    st.error("Please provide a name and at least one URL.")
                    
        # Import URLs from CSV file
        st.subheader("Import URLs from CSV")
        csv_file = st.file_uploader("Upload CSV file with URLs", type=["csv"])
        
        if csv_file is not None:
            try:
                # Read CSV data
                df = pd.read_csv(csv_file)
                
                # Try to find URL column
                url_column = None
                for col in df.columns:
                    if col.lower() in ["url", "urls", "link", "links"]:
                        url_column = col
                        break
                
                if url_column is None and len(df.columns) > 0:
                    # If no obvious URL column, let user select
                    url_column = st.selectbox("Select URL column:", df.columns)
                
                if url_column:
                    # Show preview
                    st.subheader("Preview URLs from CSV")
                    st.dataframe(df[[url_column]].head())
                    
                    # Get unique, non-empty URLs
                    urls = [url for url in df[url_column].unique() if isinstance(url, str) and url.strip()]
                    
                    if edit_mode and url_lists:
                        # Add to existing list
                        if st.button("Add URLs from CSV to List"):
                            if urls:
                                if url_list_manager.add_urls_to_list(list_id, urls):
                                    st.success(f"Added {len(urls)} URLs from CSV to list '{name}'.")
                                    st.rerun()
                                else:
                                    st.error("Failed to add URLs to list.")
                            else:
                                st.warning("No valid URLs found in the CSV file.")
                    else:
                        # Create new list from CSV
                        csv_list_name = st.text_input("New URL List Name for CSV Import")
                        
                        if st.button("Create URL List from CSV"):
                            if csv_list_name and urls:
                                list_id = url_list_manager.create_list(csv_list_name, urls)
                                st.success(f"URL list '{csv_list_name}' created with {len(urls)} URLs from CSV.")
                                st.rerun()
                            else:
                                if not csv_list_name:
                                    st.error("Please provide a name for the new URL list.")
                                if not urls:
                                    st.warning("No valid URLs found in the CSV file.")
            except Exception as e:
                st.error(f"Error processing CSV file: {e}")


def search_management_page():
    """Display the search management page."""
    st.title("Search Management")
    
    search_manager = SearchManager()
    url_list_manager = UrlListManager()
    settings_manager = SettingsManager()
    
    # Get all past searches
    searches = search_manager.get_searches()
    
    # Check API key
    api_key_status = check_api_keys()
    if not api_key_status.get("tavily", False):
        st.error("Tavily API key is not configured. Please set it up in your .env file.")
        st.stop()
    
    # Tabs for new search and viewing past searches
    tab1, tab2 = st.tabs(["New Search", "Past Searches"])
    
    with tab1:
        st.subheader("Tavily Search")
        
        # Get settings for default values
        settings = settings_manager.get_active_settings()
        tavily_settings = settings.get("tavily", {})
        
        # Search query input
        query = st.text_input("Search Query", help="Enter your search query")
        
        # Advanced options
        with st.expander("Search Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_depth = st.selectbox(
                    "Search Depth", 
                    ["basic", "advanced"],
                    index=0 if tavily_settings.get("search_depth", "basic") == "basic" else 1,
                    help="Basic is faster, Advanced provides more comprehensive results"
                )
                
                max_results = st.number_input(
                    "Max Results", 
                    min_value=1, 
                    max_value=20, 
                    value=int(tavily_settings.get("max_results", 10)),
                    help="Maximum number of results to return (1-20)"
                )
                
                include_domains_text = st.text_area(
                    "Include Domains (one per line)",
                    value="\n".join(tavily_settings.get("include_domains", [])),
                    help="Only include results from these domains"
                )
                include_domains = [domain.strip() for domain in include_domains_text.split("\n") if domain.strip()]
                
            with col2:
                exclude_domains_text = st.text_area(
                    "Exclude Domains (one per line)",
                    value="\n".join(tavily_settings.get("exclude_domains", [])),
                    help="Exclude results from these domains"
                )
                exclude_domains = [domain.strip() for domain in exclude_domains_text.split("\n") if domain.strip()]
                
                include_answer = st.checkbox(
                    "Include Answer", 
                    value=bool(tavily_settings.get("include_answer", False)),
                    help="Include a generated answer in the response"
                )
                
                include_raw = st.checkbox(
                    "Include Raw Content", 
                    value=bool(tavily_settings.get("include_raw_content", False)),
                    help="Include raw content in the response"
                )
                
                include_images = st.checkbox(
                    "Include Images", 
                    value=bool(tavily_settings.get("include_images", False)),
                    help="Include images in the response"
                )
        
        # Save settings
        save_url_list = st.checkbox("Save search results as URL list", value=True)
        url_list_name = ""
        if save_url_list:
            url_list_name = st.text_input("URL List Name", value=f"Search: {query[:30]}..." if query else "")
        
        # Search button
        if st.button("Search"):
            if query:
                with st.spinner("Searching..."):
                    try:
                        # Prepare search parameters
                        params = {
                            "search_depth": search_depth,
                            "max_results": max_results,
                            "include_domains": include_domains,
                            "exclude_domains": exclude_domains,
                            "include_answer": include_answer,
                            "include_raw_content": include_raw,
                            "include_images": include_images
                        }
                        
                        # Perform search
                        response = search_manager.perform_search(
                            query=query,
                            save_results=True,
                            create_url_list=save_url_list,
                            url_list_name=url_list_name if url_list_name else None,
                            **params
                        )
                        
                        # Display results
                        st.success(f"Search completed with {len(response.get('results', []))} results.")
                        
                        # Process results for display
                        results = response.get("results", [])
                        
                        if not results:
                            st.warning("No results found.")
                        else:
                            # Display answer if available
                            if "answer" in response and response["answer"]:
                                st.subheader("Answer")
                                st.write(response["answer"])
                                st.markdown("---")
                            
                            # Display search results in a table
                            result_data = []
                            for i, result in enumerate(results):
                                result_data.append({
                                    "#": i + 1,
                                    "Title": result.get("title", "No title"),
                                    "URL": result.get("url", ""),
                                    "Score": f"{result.get('score', 0):.2f}" if "score" in result else "-"
                                })
                            
                            result_df = pd.DataFrame(result_data)
                            st.dataframe(result_df, use_container_width=True)
                            
                            # Detailed results
                            for i, result in enumerate(results):
                                with st.expander(f"Result {i+1}: {result.get('title', 'No title')}"):
                                    st.write(f"**URL:** {result.get('url', '')}")
                                    st.write(f"**Score:** {result.get('score', '-')}")
                                    
                                    if "content" in result:
                                        st.subheader("Content")
                                        st.write(result["content"])
                                    
                                    if "raw_content" in result and result["raw_content"]:
                                        with st.expander("Raw Content"):
                                            st.text(result["raw_content"])
                                    
                                    if "images" in result and result["images"]:
                                        st.subheader("Images")
                                        for img_url in result["images"]:
                                            st.image(img_url)
                    
                    except Exception as e:
                        st.error(f"Error performing search: {e}")
            else:
                st.warning("Please enter a search query.")
    
    with tab2:
        st.subheader("Past Searches")
        
        if not searches:
            st.info("No past searches found. Perform a search in the 'New Search' tab.")
        else:
            # Convert searches to a list for display
            search_list = []
            for search_id, search in searches.items():
                # Skip special keys
                if search_id == "active_profile_id":
                    continue
                    
                search_data = {
                    "ID": search_id,
                    "Query": search.get("query", "Unknown"),
                    "Results": len(search.get("response", {}).get("results", [])),
                    "Created": search.get("created_at", ""),
                    "URL List": "✓" if search.get("url_list_id") else ""
                }
                search_list.append(search_data)
            
            # Display searches in a dataframe
            if search_list:
                df = pd.DataFrame(search_list)
                st.dataframe(df, use_container_width=True)
                
                # Search details
                with st.expander("Search Details"):
                    selected_search_id = st.selectbox("Select a search:", list(searches.keys()))
                    if selected_search_id and selected_search_id in searches:
                        search = searches[selected_search_id]
                        
                        st.write(f"**Query:** {search.get('query', 'Unknown')}")
                        st.write(f"**Date:** {search.get('created_at', 'Unknown')}")
                        
                        # Show parameters
                        with st.expander("Search Parameters"):
                            st.json(search.get("parameters", {}))
                        
                        # Show response
                        response = search.get("response", {})
                        
                        # Display answer if available
                        if "answer" in response and response["answer"]:
                            st.subheader("Answer")
                            st.write(response["answer"])
                            st.markdown("---")
                        
                        # Display search results
                        results = response.get("results", [])
                        if results:
                            result_data = []
                            for i, result in enumerate(results):
                                result_data.append({
                                    "#": i + 1,
                                    "Title": result.get("title", "No title"),
                                    "URL": result.get("url", ""),
                                    "Score": f"{result.get('score', 0):.2f}" if "score" in result else "-"
                                })
                            
                            result_df = pd.DataFrame(result_data)
                            st.dataframe(result_df, use_container_width=True)
                        else:
                            st.info("No results in this search.")
                        
                        # Create URL list from this search if it doesn't already have one
                        if not search.get("url_list_id") and results:
                            create_list_name = st.text_input("URL List Name", value=f"Search: {search.get('query', '')[:30]}...")
                            
                            if st.button("Create URL List from Search"):
                                if create_list_name:
                                    urls = [result.get("url") for result in results if "url" in result]
                                    if urls:
                                        list_id = url_list_manager.create_list(create_list_name, urls, search_response=response)
                                        
                                        # Update search with URL list ID
                                        searches[selected_search_id]["url_list_id"] = list_id
                                        st.success(f"URL list '{create_list_name}' created with {len(urls)} URLs.")
                                        st.rerun()
                                    else:
                                        st.warning("No URLs found in search results.")
                                else:
                                    st.error("Please provide a name for the URL list.")
                        
                        # Delete search
                        if st.button("Delete Search"):
                            if search_manager.delete_search(selected_search_id):
                                st.success(f"Search '{search.get('query')}' deleted successfully.")
                                st.rerun()
                            else:
                                st.error("Failed to delete search.")


def extraction_page():
    """Display the extraction page for web scraping with Selenium."""
    st.title("Extraction")
    
    extractor = Extractor()
    url_list_manager = UrlListManager()
    settings_manager = SettingsManager()
    
    # Get all URL lists
    url_lists = url_list_manager.get_lists()
    
    if not url_lists:
        st.warning("No URL lists found. Please create a URL list in the 'URL List Management' tab.")
        return
    
    # Tabs for extraction and results
    tab1, tab2 = st.tabs(["Extract URLs", "Extraction Results"])
    
    with tab1:
        st.subheader("Extract Content from URLs")
        
        # Select URL list
        list_ids = list(url_lists.keys())
        list_names = [url_lists[list_id].get("name", f"List {list_id}") for list_id in list_ids]
        
        selected_list_index = st.selectbox(
            "Select URL List",
            range(len(list_ids)),
            format_func=lambda i: list_names[i]
        )
        
        selected_list_id = list_ids[selected_list_index]
        selected_list = url_lists[selected_list_id]
        urls = selected_list.get("urls", [])
        
        if not urls:
            st.warning(f"The selected list '{selected_list.get('name')}' contains no URLs.")
            return
        
        # Display URLs
        st.write(f"**{len(urls)} URLs in this list**")
        
        # Check which URLs are cached
        if st.button("Check Cache Status"):
            with st.spinner("Checking cache..."):
                cached_urls, uncached_urls = extractor.check_url_cache_status(urls)
                
                # Store in session state for use in extraction
                st.session_state["cached_urls"] = cached_urls
                st.session_state["uncached_urls"] = uncached_urls
                
                # Display results
                if cached_urls:
                    st.success(f"{len(cached_urls)} URLs are already cached.")
                
                if uncached_urls:
                    st.warning(f"{len(uncached_urls)} URLs need to be extracted.")
                    
                    # Show first few uncached URLs
                    st.write("URLs to extract:")
                    for url in uncached_urls[:5]:
                        st.write(f"- {url}")
                    if len(uncached_urls) > 5:
                        st.write(f"- ... and {len(uncached_urls) - 5} more")
        
        # Extraction options
        st.subheader("Extraction Options")
        
        # Get current settings
        settings = settings_manager.get_active_settings()
        scraping_settings = settings.get("scraping", {})
        
        col1, col2 = st.columns(2)
        with col1:
            max_workers = st.number_input(
                "Max Concurrent Workers",
                min_value=1,
                max_value=10,
                value=int(scraping_settings.get("max_concurrent_tasks", 3)),
                help="Number of URLs to process concurrently"
            )
            
            latency = st.slider(
                "Latency (seconds)",
                min_value=0.0,
                max_value=10.0,
                value=float(scraping_settings.get("latency_seconds", 2.0)),
                step=0.5,
                help="Wait time after page load to ensure JavaScript executes"
            )
            
        with col2:
            timeout = st.slider(
                "Timeout (seconds)",
                min_value=5,
                max_value=120,
                value=int(scraping_settings.get("timeout_seconds", 30)),
                step=5,
                help="Maximum time to wait for a page to load"
            )
            
            headless = st.checkbox(
                "Headless Mode",
                value=bool(scraping_settings.get("headless", True)),
                help="Run Chrome in headless mode (no visible browser window)"
            )
        
        # Custom user agent
        user_agent = st.text_input(
            "User Agent (optional)",
            value=scraping_settings.get("user_agent", ""),
            help="Custom user agent string for the browser"
        )
        
        # Select which URLs to extract
        extract_all = True
        if "uncached_urls" in st.session_state and st.session_state["uncached_urls"]:
            extract_all = st.radio(
                "Extract:",
                ["All URLs", "Only Uncached URLs"],
                index=1,
                help="Extract all URLs or only those not in cache"
            ) == "All URLs"
        
        # Start extraction
        if st.button("Start Extraction"):
            # Determine which URLs to extract
            urls_to_extract = urls
            if not extract_all and "uncached_urls" in st.session_state:
                urls_to_extract = st.session_state["uncached_urls"]
                
            if not urls_to_extract:
                st.success("All URLs are already cached. No extraction needed.")
                return
            
            # Update settings for this extraction only
            temp_settings = settings.copy()
            temp_settings["scraping"] = {
                "latency_seconds": latency,
                "timeout_seconds": timeout,
                "max_concurrent_tasks": max_workers,
                "headless": headless,
                "user_agent": user_agent
            }
            extractor.settings = temp_settings
            
            # Create a unique task ID
            task_id = f"extract_{selected_list_id}_{int(time.time())}"
            
            # Start extraction in background
            with st.spinner(f"Extracting {len(urls_to_extract)} URLs..."):
                try:
                    # Store in session state for reference
                    st.session_state["current_extraction_task"] = task_id
                    st.session_state["extraction_list_id"] = selected_list_id
                    
                    # Run extraction
                    results = run_background_task(
                        task_id,
                        extractor.extract_urls,
                        urls_to_extract,
                        max_workers
                    )
                    
                    # Store results
                    st.session_state["extraction_results"][task_id] = {
                        "list_id": selected_list_id,
                        "list_name": selected_list.get("name", ""),
                        "urls": urls_to_extract,
                        "results": results,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Success message
                    st.success(f"Extraction completed for {len(results)} URLs.")
                    
                    # Suggest going to results tab
                    st.info("View the results in the 'Extraction Results' tab.")
                    
                except Exception as e:
                    st.error(f"Error during extraction: {e}")
    
    with tab2:
        st.subheader("Extraction Results")
        
        # Check if there are any extraction results
        if "extraction_results" not in st.session_state or not st.session_state["extraction_results"]:
            st.info("No extraction results found. Extract some URLs in the 'Extract URLs' tab.")
            return
        
        # List all extraction results
        extraction_results = st.session_state["extraction_results"]
        
        # Sort by timestamp (most recent first)
        sorted_results = sorted(
            extraction_results.items(),
            key=lambda x: x[1]["timestamp"] if "timestamp" in x[1] else "",
            reverse=True
        )
        
        # Select an extraction result
        result_options = [
            f"{result['list_name']} ({len(result['results'])} URLs, {result['timestamp'][:16]})"
            for _, result in sorted_results
        ]
        
        if not result_options:
            st.info("No extraction results found.")
            return
            
        selected_result_index = st.selectbox(
            "Select Extraction Result",
            range(len(result_options)),
            format_func=lambda i: result_options[i]
        )
        
        task_id, selected_result = sorted_results[selected_result_index]
        
        # Display result stats
        total_urls = len(selected_result["urls"])
        successful_urls = sum(1 for url, data in selected_result["results"].items() if "error" not in data)
        failed_urls = total_urls - successful_urls
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total URLs", total_urls)
        with col2:
            st.metric("Successfully Extracted", successful_urls)
        with col3:
            st.metric("Failed", failed_urls)
        
        # Display extraction results
        st.subheader("Extracted Content")
        
        # Filter options
        show_option = st.radio(
            "Show:",
            ["All URLs", "Successfully Extracted", "Failed URLs"],
            horizontal=True
        )
        
        # Filter URLs based on selection
        filtered_results = {}
        if show_option == "All URLs":
            filtered_results = selected_result["results"]
        elif show_option == "Successfully Extracted":
            filtered_results = {url: data for url, data in selected_result["results"].items() if "error" not in data}
        else:  # Failed URLs
            filtered_results = {url: data for url, data in selected_result["results"].items() if "error" in data}
        
        if not filtered_results:
            st.info(f"No URLs match the filter: {show_option}")
            return
        
        # Display URLs and their extraction status
        url_data = []
        for url, data in filtered_results.items():
            url_data.append({
                "URL": url,
                "Status": "❌ Failed" if "error" in data else "✅ Success",
                "Title": data.get("title", "N/A") if "error" not in data else "N/A",
                "Content Size": len(data.get("text_content", "")) if "error" not in data else 0
            })
        
        # Display as dataframe
        url_df = pd.DataFrame(url_data)
        st.dataframe(url_df, use_container_width=True)
        
        # View extracted content
        st.subheader("View Extracted Content")
        
        # Select URL to view
        urls = list(filtered_results.keys())
        selected_url_index = st.selectbox(
            "Select URL to view",
            range(len(urls)),
            format_func=lambda i: urls[i]
        )
        
        selected_url = urls[selected_url_index]
        url_content = filtered_results[selected_url]
        
        # Display content
        if "error" in url_content:
            st.error(f"Error extracting content: {url_content['error']}")
        else:
            st.write(f"**Title:** {url_content.get('title', 'N/A')}")
            st.write(f"**Extracted at:** {url_content.get('extracted_at', 'N/A')}")
            
            # Content tabs
            content_tab1, content_tab2, content_tab3, content_tab4 = st.tabs(["Text Content", "Links", "Metadata", "HTML"])
            
            with content_tab1:
                text_content = url_content.get("text_content", "")
                st.text_area("Text Content", text_content, height=400)
            
            with content_tab2:
                links = url_content.get("links", [])
                if links:
                    link_data = [{"URL": link.get("href", ""), "Text": link.get("text", "")} for link in links]
                    st.dataframe(pd.DataFrame(link_data), use_container_width=True)
                else:
                    st.info("No links extracted.")
            
            with content_tab3:
                meta_tags = url_content.get("meta_tags", {})
                if meta_tags:
                    st.json(meta_tags)
                else:
                    st.info("No metadata extracted.")
            
            with content_tab4:
                html = url_content.get("html", "")
                st.text_area("HTML", html, height=400)


def llm_processing_page():
    """Display the LLM processing page."""
    st.title("LLM Processing")
    
    extractor = Extractor()
    url_list_manager = UrlListManager()
    prompt_manager = PromptManager()
    settings_manager = SettingsManager()
    
    # Get URL lists, prompts, and settings
    url_lists = url_list_manager.get_lists()
    prompts = prompt_manager.get_prompts()
    settings = settings_manager.get_active_settings()
    
    # Check for necessary components
    if not url_lists:
        st.warning("No URL lists found. Please create a URL list in the 'URL List Management' tab.")
        return
    
    if not prompts:
        st.warning("No prompts found. Please create a prompt in the 'Prompt Management' tab.")
        return
    
    # Check API keys
    api_key_status = check_api_keys()
    if not (api_key_status.get("openai", False) or api_key_status.get("google", False)):
        st.error("No LLM API keys configured. Please set up at least one of OpenAI or Google API keys in your .env file.")
        return
    
    # Tabs for processing and results
    tab1, tab2 = st.tabs(["Process Content", "Processing Results"])
    
    with tab1:
        st.subheader("Process Content with LLM")
        
        # Select URL list
        list_ids = list(url_lists.keys())
        list_names = [url_lists[list_id].get("name", f"List {list_id}") for list_id in list_ids]
        
        selected_list_index = st.selectbox(
            "Select URL List",
            range(len(list_ids)),
            format_func=lambda i: list_names[i]
        )
        
        selected_list_id = list_ids[selected_list_index]
        selected_list = url_lists[selected_list_id]
        urls = selected_list.get("urls", [])
        
        if not urls:
            st.warning(f"The selected list '{selected_list.get('name')}' contains no URLs.")
            return
        
        # Display URLs
        st.write(f"**{len(urls)} URLs in this list**")
        
        # Check which URLs are cached (extracted)
        if st.button("Check Cache Status"):
            with st.spinner("Checking cache..."):
                cached_urls, uncached_urls = extractor.check_url_cache_status(urls)
                
                # Store in session state for use in processing
                st.session_state["cached_urls"] = cached_urls
                st.session_state["uncached_urls"] = uncached_urls
                
                # Display results
                if cached_urls:
                    st.success(f"{len(cached_urls)} URLs are cached and ready for processing.")
                
                if uncached_urls:
                    st.warning(f"{len(uncached_urls)} URLs need to be extracted before processing.")
                    
                    # Show first few uncached URLs
                    st.write("URLs that need extraction:")
                    for url in uncached_urls[:5]:
                        st.write(f"- {url}")
                    if len(uncached_urls) > 5:
                        st.write(f"- ... and {len(uncached_urls) - 5} more")
                    
                    # Link to extraction page
                    st.info("Please extract these URLs in the 'Extraction' tab before processing.")
        
        # Select prompt
        st.subheader("Select Prompt")
        prompt_ids = list(prompts.keys())
        prompt_names = [prompts[prompt_id].get("name", f"Prompt {prompt_id}") for prompt_id in prompt_ids]
        
        selected_prompt_index = st.selectbox(
            "Select Prompt",
            range(len(prompt_ids)),
            format_func=lambda i: prompt_names[i]
        )
        
        selected_prompt_id = prompt_ids[selected_prompt_index]
        selected_prompt = prompts[selected_prompt_id]
        
        # Display prompt details
        with st.expander("Prompt Details"):
            st.write(f"**Name:** {selected_prompt.get('name', '')}")
            st.write(f"**Output Format:** {selected_prompt.get('output_format', 'json')}")
            st.text_area("Prompt Content", selected_prompt.get("content", ""), height=200)
        
        # Select LLM provider
        st.subheader("LLM Provider")
        
        available_providers = []
        if api_key_status.get("openai", False):
            available_providers.append("OpenAI")
        if api_key_status.get("google", False):
            available_providers.append("Google")
        
        provider = st.radio(
            "Select LLM Provider",
            available_providers,
            horizontal=True
        )
        
        # Processing options
        st.subheader("Processing Options")
        
        # Get current settings
        llm_settings = settings.get("llm", {})
        
        # Only show options for the selected provider
        if provider == "OpenAI":
            openai_settings = llm_settings.get("openai", {})
            model = st.text_input(
                "Model",
                value=openai_settings.get("model", "gpt-4"),
                help="The OpenAI model to use for processing"
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=float(openai_settings.get("temperature", 0.0)),
                step=0.1,
                help="Controls randomness in the output (0.0 = deterministic, 1.0 = creative)"
            )
            
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=int(openai_settings.get("max_tokens", 1000)),
                help="Maximum number of tokens to generate in the response"
            )
        else:  # Google
            google_settings = llm_settings.get("google", {})
            model = st.text_input(
                "Model",
                value=google_settings.get("model", "gemini-pro"),
                help="The Google Gemini model to use for processing"
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=float(google_settings.get("temperature", 0.0)),
                step=0.1,
                help="Controls randomness in the output (0.0 = deterministic, 1.0 = creative)"
            )
            
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=int(google_settings.get("max_tokens", 1000)),
                help="Maximum number of tokens to generate in the response"
            )
        
        # Concurrent processing
        max_workers = st.number_input(
            "Max Concurrent Workers",
            min_value=1,
            max_value=10,
            value=int(settings.get("scraping", {}).get("max_concurrent_tasks", 3)),
            help="Number of URLs to process concurrently"
        )
        
        # Select which URLs to process
        process_all = True
        if "uncached_urls" in st.session_state and st.session_state["uncached_urls"]:
            process_cached_only = st.checkbox(
                "Process only cached URLs",
                value=True,
                help="Process only URLs that have been extracted and cached"
            )
            
            if process_cached_only:
                process_all = False
        
        # Start processing
        if st.button("Start Processing"):
            # Determine which URLs to process
            urls_to_process = urls
            if not process_all and "cached_urls" in st.session_state:
                urls_to_process = st.session_state["cached_urls"]
                
            if not urls_to_process:
                st.error("No URLs to process. Please check cache status and extract URLs if needed.")
                return
            
            # Get prompt content
            prompt_content = selected_prompt.get("content", "")
            if not prompt_content:
                st.error("Selected prompt has no content.")
                return
            
            # Create a unique task ID
            task_id = f"process_{selected_list_id}_{selected_prompt_id}_{int(time.time())}"
            
            # Provider-specific settings
            provider_name = provider.lower()
            
            # Temporarily update extractor settings for the LLM
            temp_settings = settings.copy()
            
            if provider_name == "openai":
                temp_settings["llm"]["openai"] = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            else:  # google
                temp_settings["llm"]["google"] = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            
            extractor.settings = temp_settings
            
            # Start processing in background
            with st.spinner(f"Processing {len(urls_to_process)} URLs with {provider}..."):
                try:
                    # Store in session state for reference
                    st.session_state["current_processing_task"] = task_id
                    
                    # Run processing
                    results = run_background_task(
                        task_id,
                        extractor.process_urls,
                        urls_to_process,
                        prompt_content,
                        provider_name,
                        max_workers
                    )
                    
                    # Store results
                    st.session_state["processing_results"][task_id] = {
                        "list_id": selected_list_id,
                        "list_name": selected_list.get("name", ""),
                        "prompt_id": selected_prompt_id,
                        "prompt_name": selected_prompt.get("name", ""),
                        "provider": provider,
                        "urls": urls_to_process,
                        "results": results,
                        "output_format": selected_prompt.get("output_format", "json"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Success message
                    st.success(f"Processing completed for {len(results)} URLs.")
                    
                    # Suggest going to results tab
                    st.info("View the results in the 'Processing Results' tab.")
                    
                except Exception as e:
                    st.error(f"Error during processing: {e}")
    
    with tab2:
        st.subheader("Processing Results")
        
        # Check if there are any processing results
        if "processing_results" not in st.session_state or not st.session_state["processing_results"]:
            st.info("No processing results found. Process some URLs in the 'Process Content' tab.")
            return
        
        # List all processing results
        processing_results = st.session_state["processing_results"]
        
        # Sort by timestamp (most recent first)
        sorted_results = sorted(
            processing_results.items(),
            key=lambda x: x[1]["timestamp"] if "timestamp" in x[1] else "",
            reverse=True
        )
        
        # Select a processing result
        result_options = [
            f"{result['list_name']} → {result['prompt_name']} ({result['provider']}, {result['timestamp'][:16]})"
            for _, result in sorted_results
        ]
        
        if not result_options:
            st.info("No processing results found.")
            return
            
        selected_result_index = st.selectbox(
            "Select Processing Result",
            range(len(result_options)),
            format_func=lambda i: result_options[i]
        )
        
        task_id, selected_result = sorted_results[selected_result_index]
        
        # Display result stats
        total_urls = len(selected_result["urls"])
        successful_urls = sum(1 for url, data in selected_result["results"].items() if "error" not in data)
        failed_urls = total_urls - successful_urls
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total URLs", total_urls)
        with col2:
            st.metric("Successfully Processed", successful_urls)
        with col3:
            st.metric("Failed", failed_urls)
        with col4:
            st.metric("Provider", selected_result["provider"])
        
        # Display processing results
        st.subheader("LLM Outputs")
        
        # Filter options
        show_option = st.radio(
            "Show:",
            ["All URLs", "Successfully Processed", "Failed URLs"],
            horizontal=True
        )
        
        # Filter URLs based on selection
        filtered_results = {}
        if show_option == "All URLs":
            filtered_results = selected_result["results"]
        elif show_option == "Successfully Processed":
            filtered_results = {url: data for url, data in selected_result["results"].items() if "error" not in data}
        else:  # Failed URLs
            filtered_results = {url: data for url, data in selected_result["results"].items() if "error" in data}
        
        if not filtered_results:
            st.info(f"No URLs match the filter: {show_option}")
            return
        
        # Display URLs and their processing status
        url_data = []
        for url, data in filtered_results.items():
            url_data.append({
                "URL": url,
                "Status": "❌ Failed" if "error" in data else "✅ Success",
                "Title": data.get("title", "N/A") if "error" not in data else "N/A",
                "Model": data.get("model", "N/A") if "error" not in data else "N/A"
            })
        
        # Display as dataframe
        url_df = pd.DataFrame(url_data)
        st.dataframe(url_df, use_container_width=True)
        
        # View processed content
        st.subheader("View LLM Output")
        
        # Select URL to view
        urls = list(filtered_results.keys())
        selected_url_index = st.selectbox(
            "Select URL to view",
            range(len(urls)),
            format_func=lambda i: urls[i],
            key="llm_url_select"
        )
        
        selected_url = urls[selected_url_index]
        url_content = filtered_results[selected_url]
        
        # Display content
        if "error" in url_content:
            st.error(f"Error processing content: {url_content['error']}")
        else:
            st.write(f"**URL:** {selected_url}")
            st.write(f"**Title:** {url_content.get('title', 'N/A')}")
            st.write(f"**Model:** {url_content.get('model', 'N/A')}")
            st.write(f"**Processed at:** {url_content.get('processed_at', 'N/A')}")
            
            # Display response based on format
            output_format = selected_result.get("output_format", "json")
            response_text = url_content.get("response", "")
            
            if output_format == "json":
                try:
                    # Try to parse as JSON
                    json_data = json.loads(response_text)
                    st.json(json_data)
                except json.JSONDecodeError:
                    # If not valid JSON, display as text
                    st.text_area("Response", response_text, height=400)
            else:
                # Display as markdown
                st.markdown(response_text)
        
        # Download options
        st.subheader("Download Results")
        
        # Create download functions
        def get_all_results():
            """Prepare all results for download."""
            results = {}
            for url, data in selected_result["results"].items():
                if "error" not in data:
                    results[url] = {
                        "title": data.get("title", "N/A"),
                        "response": data.get("response", ""),
                        "model": data.get("model", "N/A"),
                        "processed_at": data.get("processed_at", "")
                    }
            return results
        
        def get_single_result():
            """Prepare the selected result for download."""
            data = selected_result["results"][selected_url]
            if "error" in data:
                return {}
            
            return {
                "url": selected_url,
                "title": data.get("title", "N/A"),
                "response": data.get("response", ""),
                "model": data.get("model", "N/A"),
                "processed_at": data.get("processed_at", "")
            }
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download All Results (JSON)"):
                results = get_all_results()
                if results:
                    # Create JSON string
                    json_str = json.dumps(results, indent=2)
                    
                    # Create a download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"llm_results_{timestamp}.json"
                    
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=filename,
                        mime="application/json"
                    )
                else:
                    st.warning("No successful results to download.")
        
        with col2:
            if st.button("Download Selected Result"):
                result = get_single_result()
                if result:
                    # Format depends on the output format
                    if output_format == "json":
                        # Create JSON string
                        json_str = json.dumps(result, indent=2)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"llm_result_{timestamp}.json"
                        
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=filename,
                            mime="application/json"
                        )
                    else:
                        # For markdown, just download the response text
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"llm_result_{timestamp}.md"
                        
                        st.download_button(
                            label="Download Markdown",
                            data=result["response"],
                            file_name=filename,
                            mime="text/markdown"
                        )
                else:
                    st.warning("No successful result to download.")


def main():
    """Main application function."""
    display_sidebar()
    
    # Display the selected tab
    if st.session_state["active_tab"] == "Prompt Management":
        prompt_management_page()
    elif st.session_state["active_tab"] == "Search Management":
        search_management_page()
    elif st.session_state["active_tab"] == "URL List Management":
        url_list_management_page()
    elif st.session_state["active_tab"] == "Settings":
        settings_page()
    elif st.session_state["active_tab"] == "Extraction":
        extraction_page()
    elif st.session_state["active_tab"] == "LLM Processing":
        llm_processing_page()


if __name__ == "__main__":
    main() 