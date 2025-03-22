# LLM Web Scraper and Processor

A powerful Python application that integrates Tavily search, advanced Selenium web scraping, and LLM processing to extract and analyze data from websites, including JavaScript-heavy pages like telecom sites.

## Key Features

### 1. Advanced Web Scraping
- **Dynamic Content Handling**: Specialized support for JavaScript-heavy pages
- **Anti-Detection Measures**: Advanced browser fingerprinting evasion
- **Proxy Support**: Format: `ip:port:username:password`
- **Caching System**: Efficient content storage with configurable timeout
- **Concurrent Processing**: Multi-threaded URL processing
- **Error Handling**: Robust fallback mechanisms for content extraction

### 2. LLM Integration
- **Multiple Providers**:
  - OpenAI (GPT-4)
  - Google Gemini (2.0 Flash)
- **Customizable Processing**: Temperature and token limit settings
- **Prompt Management**: Create and store reusable prompts
- **Batch Processing**: Process multiple URLs concurrently

### 3. Search Capabilities
- **Tavily Integration**: Advanced web search functionality
- **URL List Management**: Organize and manage URL collections
- **Search Parameters**: Customizable domain inclusion/exclusion

### 4. User Interface
- **Streamlit-Based**: Clean, modern web interface
- **Real-Time Status**: Live extraction and processing updates
- **Settings Management**: Configurable application parameters
- **Results Export**: Download processed data in JSON format

## Project Structure

```
project_root/
├── src/                     # Source code
│   ├── app.py              # Main Streamlit application
│   ├── extractor.py        # Web scraping and LLM processing
│   ├── prompt_manager.py   # Prompt CRUD operations
│   ├── search_manager.py   # Tavily search integration
│   ├── url_list_manager.py # URL list management
│   ├── settings_manager.py # Settings management
│   └── utils.py           # Utility functions
├── data/                   # JSON data storage
│   ├── prompts.json       # Stored prompts
│   ├── url_lists.json     # URL collections
│   └── settings.json      # Application settings
├── cache/                  # Cached URL content
├── logs/                   # Application logs
└── tests/                  # Unit tests
```

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`:
   ```env
   # API Keys
   TAVILY_API_KEY=your_tavily_api_key
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key

   # Default Model Settings
   DEFAULT_OPENAI_MODEL=gpt-4
   DEFAULT_GEMINI_MODEL=gemini-2.0-flash

   # Selenium Settings
   SELENIUM_HEADLESS=True
   SELENIUM_TIMEOUT=30
   SELENIUM_PAGE_LOAD_TIMEOUT=30

   # Scraping Settings
   MAX_CONCURRENT_SCRAPES=5
   SCRAPING_DELAY=5
   CACHE_TIMEOUT_HOURS=24

   # Optional Configuration
   LOG_LEVEL=INFO
   ```

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage Guide

### 1. Prompt Management
- Navigate to "Prompt Management"
- Create prompts for content analysis
- Support for both structured (JSON) and unstructured outputs

### 2. URL Management
- Use "Search Management" to find URLs via Tavily
- Create and manage URL lists
- Import URLs from CSV files

### 3. Content Extraction
- Select URL list and start extraction
- Monitor progress in real-time
- View cached vs. uncached status

### 4. LLM Processing
- Choose between OpenAI and Google Gemini
- Select prompt and processing parameters
- Process individual or batch URLs
- Export results in JSON format

## Advanced Features

### Proxy Configuration
```python
settings["scraping"]["proxy"] = "ip:port:username:password"
settings["scraping"]["rotate_proxies"] = True
settings["scraping"]["proxy_list"] = ["proxy1", "proxy2", ...]
```

### JavaScript Handling
- Enhanced browser fingerprinting evasion
- Dynamic content wait conditions
- Multiple content extraction fallbacks
- Anti-bot detection measures

### Performance Optimization
- Concurrent URL processing
- Efficient caching system
- Memory usage optimization
- Request rate limiting

## Error Handling

The application includes comprehensive error handling for:
- Network issues
- API rate limits
- JavaScript execution
- Dynamic content loading
- Invalid URLs/content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Google for Gemini API
- Tavily for search API
- Selenium for web automation
- Streamlit for UI framework 