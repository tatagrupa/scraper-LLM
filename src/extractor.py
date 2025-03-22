"""
Extractor for the LLM Web Scraper and Processor.

Handles web scraping with Selenium and LLM processing.
"""

import asyncio
import json
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import google.generativeai as genai
import openai
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

from .settings_manager import SettingsManager
from .utils import get_from_cache, save_to_cache, hash_url


class Extractor:
    """Handles web scraping and LLM processing."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.get_active_settings()
        self.api_keys = self.settings_manager.get_api_keys()
        
        # Set up OpenAI
        openai.api_key = self.api_keys.get("openai", os.getenv("OPENAI_API_KEY", ""))
        
        # Set up Google Gemini
        self.google_api_key = self.api_keys.get("google", os.getenv("GOOGLE_API_KEY", ""))
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            # Initialize default model
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            logger.warning("Google API key not found. Gemini processing will not be available.")
    
    def _get_chrome_options(self, user_agent: Optional[str] = None, proxy: Optional[str] = None) -> webdriver.ChromeOptions:
        """Get Chrome options with anti-detection settings."""
        options = webdriver.ChromeOptions()
        
        # Basic options
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Enhanced JavaScript support
        options.add_argument('--enable-javascript')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Memory and performance options
        options.add_argument('--disable-dev-tools')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--blink-settings=imagesEnabled=true')
        options.add_argument('--js-flags=--expose-gc')
        options.add_argument('--disk-cache-size=0')
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional preferences
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.cookies': 1
        })
        
        # Set random user agent if not provided
        if not user_agent:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ]
            user_agent = random.choice(user_agents)
        
        options.add_argument(f'user-agent={user_agent}')
        
        # Add proxy if provided (format: ip:port:username:password)
        if proxy:
            try:
                parts = proxy.split(':')
                if len(parts) == 4:
                    ip, port, username, password = parts
                    proxy_url = f'http://{username}:{password}@{ip}:{port}'
                    options.add_argument(f'--proxy-server={proxy_url}')
            except Exception as e:
                logger.error(f"Error setting proxy: {e}")
        
        return options

    def extract_url(self, url: str) -> Dict[str, Any]:
        """Extract content from a URL using Selenium."""
        settings = self.settings.get("scraping", {})
        latency = float(settings.get("latency_seconds", 2))
        timeout = int(settings.get("timeout_seconds", 30))
        user_agent = settings.get("user_agent", "")
        proxy = settings.get("proxy", "")
        
        logger.info(f"Extracting content from {url}")
        
        try:
            # Get Chrome options with anti-detection measures
            options = self._get_chrome_options(user_agent, proxy)
            
            # Set up Chrome service
            service = Service()
            
            # Create WebDriver with service and options
            driver = webdriver.Chrome(service=service, options=options)
            
            # Add anti-detection JavaScript
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = {
                        runtime: {},
                        loadTimes: () => {},
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                '''
            })
            
            try:
                # Load the page
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # Wait for dynamic content
                time.sleep(latency)
                
                # Additional wait for specific elements (common in telecom sites)
                try:
                    WebDriverWait(driver, timeout).until(
                        lambda d: len(d.execute_script(
                            'return document.body.textContent'
                        )) > 0
                    )
                except:
                    pass  # Continue if timeout, we might still have content
                
                # Get page content
                title = driver.title
                html = driver.page_source
                
                # Extract text content with enhanced error handling
                try:
                    text_content = driver.execute_script("""
                        function extractText(element) {
                            try {
                                if (!element) return '';
                                if (element.tagName === 'SCRIPT' || element.tagName === 'STYLE') return '';
                                
                                let text = '';
                                for (let node of element.childNodes) {
                                    if (node.nodeType === 3) {  // Text node
                                        text += node.textContent + ' ';
                                    }
                                }
                                return text.trim();
                            } catch (e) {
                                return '';
                            }
                        }
                        
                        try {
                            let texts = [];
                            let elements = document.body.getElementsByTagName('*');
                            
                            for (let i = 0; i < elements.length; i++) {
                                let text = extractText(elements[i]);
                                if (text) texts.push(text);
                            }
                            
                            return texts.join('\\n');
                        } catch (e) {
                            return document.body.innerText || '';
                        }
                    """)
                except Exception as e:
                    # Fallback to simpler extraction
                    text_content = driver.find_element(By.TAG_NAME, "body").text
                
                # Extract links with enhanced error handling
                try:
                    links = driver.execute_script("""
                        try {
                            let links = [];
                            let elements = document.getElementsByTagName('a');
                            
                            for (let i = 0; i < elements.length; i++) {
                                try {
                                    let link = elements[i];
                                    links.push({
                                        href: link.href || '',
                                        text: (link.textContent || '').trim()
                                    });
                                } catch (e) {
                                    continue;
                                }
                            }
                            
                            return links;
                        } catch (e) {
                            return [];
                        }
                    """)
                except:
                    links = []
                
                return {
                    "url": url,
                    "title": title,
                    "html": html,
                    "text_content": text_content,
                    "links": links,
                    "extracted_at": datetime.now().isoformat()
                }
                
            except TimeoutException:
                raise Exception("Page load timed out")
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                "url": url,
                "error": str(e)
            }
    
    def extract_urls(self, urls: List[str], max_workers: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Extract content from multiple URLs concurrently.
        
        Args:
            urls: List of URLs to extract content from.
            max_workers: Maximum number of concurrent workers. If None, uses settings.
            
        Returns:
            Dictionary mapping URLs to their extracted content.
        """
        # Get scraping settings
        scraping_settings = self.settings.get("scraping", {})
        cache_timeout_hours = scraping_settings.get("cache_timeout_hours", 24)
        
        if max_workers is None:
            max_workers = scraping_settings.get("max_concurrent_tasks", 3)
        
        results = {}
        urls_to_extract = []
        
        # Check cache first
        for url in urls:
            cached_content = get_from_cache(url, cache_timeout_hours)
            if cached_content:
                results[url] = cached_content
            else:
                urls_to_extract.append(url)
        
        if not urls_to_extract:
            logger.info("All URLs found in cache, no extraction needed")
            return results
        
        logger.info(f"Extracting {len(urls_to_extract)} URLs with {max_workers} workers")
        
        # Use ThreadPoolExecutor for concurrent extraction
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map URLs to extraction function
            extraction_results = executor.map(self.extract_url, urls_to_extract)
            
            # Process results
            for result in extraction_results:
                if result and "url" in result:
                    results[result["url"]] = result
        
        return results
    
    def process_with_openai(self, content: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        Process content with OpenAI.
        
        Args:
            content: Content to process.
            prompt: Prompt to use for processing.
            
        Returns:
            Dictionary containing processing results.
        """
        if not openai.api_key:
            raise ValueError("OpenAI API key not found")
        
        # Get LLM settings
        llm_settings = self.settings.get("llm", {}).get("openai", {})
        model = llm_settings.get("model", "gpt-4")
        temperature = llm_settings.get("temperature", 0.0)
        max_tokens = llm_settings.get("max_tokens", 1000)
        
        # Construct system message with prompt
        system_message = prompt
        
        # Construct user message with content
        user_message = f"""
        URL: {content.get('url', 'Unknown')}
        Title: {content.get('title', 'Unknown')}
        
        Content:
        {content.get('text_content', '')}
        """
        
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = {
                "url": content.get("url"),
                "title": content.get("title"),
                "processed_at": datetime.now().isoformat(),
                "model": model,
                "response": response.choices[0].message.content
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing with OpenAI: {e}")
            return {
                "url": content.get("url"),
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def process_with_google(self, content: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        Process content with Google Gemini.
        
        Args:
            content: Content to process.
            prompt: Prompt to use for processing.
            
        Returns:
            Dictionary containing processing results.
        """
        if not self.google_api_key:
            raise ValueError("Google API key not found")
        
        # Get LLM settings
        llm_settings = self.settings.get("llm", {}).get("google", {})
        temperature = llm_settings.get("temperature", 0.0)
        max_tokens = llm_settings.get("max_tokens", 1000)
        
        # Construct prompt with content
        full_prompt = f"""
        {prompt}
        
        URL: {content.get('url', 'Unknown')}
        Title: {content.get('title', 'Unknown')}
        
        Content:
        {content.get('text_content', '')}
        """
        
        try:
            # Generate response using the initialized model
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            result = {
                "url": content.get("url"),
                "title": content.get("title"),
                "processed_at": datetime.now().isoformat(),
                "model": "gemini-2.0-flash",
                "response": response.text
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing with Google Gemini: {e}")
            return {
                "url": content.get("url"),
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def process_content(self, url: str, prompt: str, provider: str = "openai") -> Dict[str, Any]:
        """
        Process content from a URL with an LLM.
        
        Args:
            url: URL of the content to process.
            prompt: Prompt to use for processing.
            provider: LLM provider to use ("openai" or "google").
            
        Returns:
            Dictionary containing processing results.
        """
        # Get scraping settings
        scraping_settings = self.settings.get("scraping", {})
        cache_timeout_hours = scraping_settings.get("cache_timeout_hours", 24)
        
        # Get content from cache or extract
        content = get_from_cache(url, cache_timeout_hours)
        if not content:
            content = self.extract_url(url)
        
        # Check for errors in content
        if content and "error" in content:
            return {
                "url": url,
                "error": f"Error in content extraction: {content['error']}",
                "processed_at": datetime.now().isoformat()
            }
        
        # Process with selected provider
        if provider.lower() == "openai":
            return self.process_with_openai(content, prompt)
        elif provider.lower() == "google":
            return self.process_with_google(content, prompt)
        else:
            return {
                "url": url,
                "error": f"Invalid provider: {provider}",
                "processed_at": datetime.now().isoformat()
            }
    
    def process_urls(self, urls: List[str], prompt: str, provider: str = "openai", 
                     max_workers: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Process multiple URLs concurrently.
        
        Args:
            urls: List of URLs to process.
            prompt: Prompt to use for processing.
            provider: LLM provider to use ("openai" or "google").
            max_workers: Maximum number of concurrent workers. If None, uses settings.
            
        Returns:
            Dictionary mapping URLs to their processing results.
        """
        if max_workers is None:
            max_workers = self.settings.get("scraping", {}).get("max_concurrent_tasks", 3)
        
        results = {}
        
        # Define a worker function for ThreadPoolExecutor
        def process_url(url):
            return url, self.process_content(url, prompt, provider)
        
        logger.info(f"Processing {len(urls)} URLs with {max_workers} workers using {provider}")
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks and get futures
            futures = {executor.submit(process_url, url): url for url in urls}
            
            # Process results as they complete
            for future in futures:
                try:
                    url, result = future.result()
                    results[url] = result
                except Exception as e:
                    url = futures[future]
                    logger.error(f"Error processing {url}: {e}")
                    results[url] = {
                        "url": url,
                        "error": str(e),
                        "processed_at": datetime.now().isoformat()
                    }
        
        return results
    
    def check_url_cache_status(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Check which URLs are cached and which need extraction.
        
        Args:
            urls: List of URLs to check.
            
        Returns:
            Tuple of (cached_urls, uncached_urls).
        """
        # Get scraping settings
        scraping_settings = self.settings.get("scraping", {})
        cache_timeout_hours = scraping_settings.get("cache_timeout_hours", 24)
        
        cached_urls = []
        uncached_urls = []
        
        for url in urls:
            cached_content = get_from_cache(url, cache_timeout_hours)
            if cached_content:
                cached_urls.append(url)
            else:
                uncached_urls.append(url)
        
        return cached_urls, uncached_urls 