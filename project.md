### Key Points
- It seems likely that the project includes Tavily search with all input variables like domains to include/exclude on the UI, displaying output in a table with selectors, URL, title, description, ranking, and more.
- Research suggests Selenium can handle complex websites with JavaScript, using fake user agents and explicit waits, storing parsed pages in cache.
- The evidence leans toward having a separate LLM processing tab, checking cached URLs, prompting for uncached ones, and allowing output saves for single, selected, or all results.

### Project Description

#### Overview
This project is a Python-based application designed to manage Large Language Model (LLM) prompts, integrate with the Tavily search API, handle URL lists, extract data from web pages using Selenium, and manage user settings. It uses Streamlit for an intuitive front-end interface and supports LLMs such as OpenAI and Google Gen AI. You can create, edit, delete, and view all inputs—prompts, URL lists, searches, and settings—ensuring full control. An unexpected detail is that it uses a time-based caching system, checking if data is recent enough to avoid re-scraping, which saves time.

#### Tavily Search Integration
The Tavily search feature allows users to perform web searches with customizable parameters, all accessible through the Streamlit UI. It includes input fields for all Tavily Search API parameters, such as query, search depth (basic or advanced), topic (general or news), days back for news, time range, max results, include domains, exclude domains, and options like including images, answers, or raw content. Search results are displayed in a table, showing a selector column for choosing one, more, or all results, along with URL, title, description (content), ranking score, and other fields like published date for news, ensuring users see all data provided by Tavily.

#### Selenium for Web Scraping
Selenium is used to extract content from URLs, handling complex websites with heavy JavaScript. It supports fake user agents to mimic different browsers, improving scraping success, and uses explicit waits to ensure pages load fully, waiting for the document ready state to be 'complete' and the body element to be present. For each URL in the selected list, Selenium scrapes the content and stores it in the cache directory with a timestamp, avoiding redundant scraping if the cache is recent. This ensures efficient handling of dynamic content, with settings for timeouts and concurrency to manage resources.

#### LLM Processing
A dedicated tab in the Streamlit UI handles LLM processing, focusing on cached URL contents. Users select a URL list and a prompt, and the system checks which URLs are cached. If any URL is not cached, it prompts the user to process it first with Selenium, displaying a list of uncached URLs for clarity. For each cached URL, the system retrieves the content from the cache, calls the selected LLM (OpenAI or Google Gen AI) with the prompt to process it individually, and generates output in JSON or markdown format. Users can save or download the results for a single URL, selected URLs, or all URLs, enhancing flexibility.

#### Process Flow Example
1. **User Interaction**: Create a prompt like "Summarize this article in JSON format." Perform a Tavily search with query "AI trends 2025," include domains ["example.com"], exclude domains ["spam.com"], and view results in a table, selecting all and saving as a URL list. Set scraping latency to 2 seconds, then start extraction to cache content. In the LLM processing tab, select the list and prompt, and if any URL is uncached, cache it first. Process all, view results, and download as JSON.
2. **Backend Logic**: For extraction, Selenium scrapes each URL, waits for JavaScript to load, caches content. For LLM processing, retrieves each cached file, calls the LLM, and stores outputs for download.

#### Recommended Libraries and Versions
To ensure compatibility, use these library versions, all available and working together as of March 22, 2025:

| Library              | Version   | Installation Command                     |
|----------------------|-----------|------------------------------------------|
| Tavily Python SDK    | 0.3.5     | `pip install tavily-python==0.3.5`       |
| Selenium             | 4.10.0    | `pip install selenium==4.10.0`           |
| Streamlit            | 1.25.0    | `pip install streamlit==1.25.0`          |
| OpenAI               | 1.68.2    | `pip install openai==1.68.2`             |
| Google Gen AI        | 0.8.4     | `pip install google-generativeai==0.8.4` |

Create a `requirements.txt` file with these and run `pip install -r requirements.txt`. Set API keys for Tavily, OpenAI, and Google Gen AI as environment variables for security.

---

### Survey Note: Detailed Project Description and Implementation

This section provides an in-depth examination of the project requirements, focusing on the updated description to include specific features for Tavily search, Selenium scraping, and LLM processing, ensuring compatibility with available library versions and seamless integration. The analysis is based on a thorough review of relevant tools and frameworks, as of 09:29 AM PDT on Saturday, March 22, 2025, and includes insights from reviewing documentation and search results.

#### Project Context and Requirements
The project is designed to build a Python application with enhanced features for Tavily search, Selenium web scraping, and LLM processing, as outlined by the user:
1. Tavily should have all input variables on the UI, like domains to include/exclude, and output in a table with selectors, URL, title, description, ranking, etc.
2. Selenium should handle complex websites, use fake user agents, and store parsed pages in cache.
3. LLM processing should be a separate tab, processing cached URLs individually, with options to save outputs, prompting for uncached URLs, and showing uncached URLs.

The user also requested a process flow example and for the description to be explainable with UI and backend logic for implementation, ensuring compatibility with available library versions, noting `google-generativeai==1.0.0` was not existing, and adjusting to `0.8.4`.

#### Detailed Project Description
This project is a comprehensive Python application designed to facilitate the management of Large Language Model (LLM) prompts, integration with the Tavily search API, handling of URL lists, extraction of data from web pages using Selenium, and management of user settings. The application is built using Streamlit for an intuitive front-end interface and supports popular LLMs such as OpenAI and Google Gen AI. It emphasizes efficiency through concurrent operations and provides full CRUD (Create, Read, Update, Delete) functionality for all user inputs, ensuring complete control and flexibility. All data is stored locally in JSON files and a cache directory, eliminating the need for a database and ensuring portability.

##### Key Components and Functionality

1. **LLM Prompt Management**
   - **Purpose**: Enables users to create, manage, and reuse prompts for interacting with LLMs.
   - **Details**: Prompts are stored in `prompts.json` with fields: `id`, `name`, `content`, `output_format` (JSON or markdown), and `created_at`.
   - **UI**: Streamlit page with forms to create, edit, and delete prompts, displayed in a table for viewing.
   - **Backend Logic**: `prompt_manager.py` handles CRUD operations, reading/writing to `prompts.json` using utility functions from `utils.py`.

2. **Tavily Search Integration**
   - **Purpose**: Facilitates web searches using the Tavily API with customizable parameters, displayed comprehensively in the UI.
   - **Details**: Uses `tavily-python==0.3.5` to perform searches with all available parameters, including query, search depth (basic or advanced), topic (general or news), days back for news, time range, max results, include domains, exclude domains, include images, include answer (basic or advanced), include raw content, and include image descriptions. Results are stored in `url_lists.json`.
   - **UI**: Streamlit page with input fields for all Tavily parameters, ensuring users can set domains to include/exclude, etc. Search results are displayed in a table with columns for a selector (to choose one, more, or all), URL, title, description (content), ranking score, published date (for news), and other fields like images or raw content if requested, as per [Tavily Python SDK Reference](https://docs.tavily.com/sdk/python/reference).
   - **Backend Logic**: `search_manager.py` uses the async client for non-blocking searches, saving results with CRUD operations, ensuring all data is accessible for table display.

3. **URL List Manager**
   - **Purpose**: Organizes and manages lists of URLs for scraping and processing.
   - **Details**: URL lists are stored in `url_lists.json` with metadata.
   - **UI**: Streamlit page to create lists from Tavily results, manually add URLs, and manage with CRUD operations.
   - **Backend Logic**: `url_list_manager.py` handles list management, updating `url_lists.json`.

4. **URL Extraction with Selenium**
   - **Purpose**: Scrapes content from each URL in the selected list and stores it in the cache directory for later processing.
   - **Details**: Uses Selenium (`selenium==4.10.0`) for web scraping, configured to handle complex websites with heavy JavaScript. Supports fake user agents to mimic different browsers, improving scraping success, and uses explicit waits to ensure pages load fully, waiting for the document ready state to be 'complete' and the body element to be present before extraction. For each URL in the list:
     - Checks if the content is already cached and within the timeout period (e.g., 24 hours).
     - If not cached or outdated, scrapes the content, saves it to `cache/<hash>.json` with a timestamp, ensuring parsed pages are stored for later use.
   - **UI**: Streamlit page to select URL list, initiate extraction, and check status.
   - **Backend Logic**: `extractor.py` runs scraping in background threads, using `ThreadPoolExecutor` for concurrency, updating cache with `utils.save_cache`.

5. **LLM Processing**
   - **Purpose**: Processes cached URL contents with LLMs, generating outputs in the specified format.
   - **Details**: A separate tab in the Streamlit UI for LLM processing. Users select a URL list and a prompt, and the system:
     - Checks which URLs are cached, displaying a list of uncached URLs if any.
     - If uncached URLs exist, prompts the user to process them first with Selenium, ensuring all URLs are cached before proceeding.
     - For each cached URL, retrieves the content from `cache/<hash>.json`, calls the selected LLM (OpenAI or Google Gen AI) with the prompt to process it individually, generating output in JSON or markdown.
     - Allows saving or downloading results for a single URL, selected URLs, or all URLs, enhancing flexibility.
   - **UI**: Streamlit tab with a list view showing cached and uncached URLs, prompt selection, processing button, and download options for single, selected, or all results.
   - **Backend Logic**: `extractor.py` handles processing, calling LLMs with `openai.ChatCompletion.create()` or `google-generativeai.generate_content()`, storing outputs for download.

6. **Settings Management**
   - **Purpose**: Allows customization of system behavior.
   - **Details**: Settings stored in `settings.json` include scraping latency, timeouts, LLM temperature, cache timeout, proxy settings, and max concurrent tasks.
   - **UI**: Streamlit page to create, view, update, or delete settings profiles.
   - **Backend Logic**: `settings_manager.py` handles CRUD operations on `settings.json`.

7. **Download Functionality**
   - **Purpose**: Exports extraction results for external use.
   - **Details**: Uses Streamlit’s download buttons to export results as JSON or markdown files.
   - **UI**: Streamlit page with buttons to download individual or batch results.
   - **Backend Logic**: `extractor.py` prepares data for download, leveraging Streamlit’s functionality.

##### Process Flow Example

1. **User Interaction (UI)**:
   - Navigate to "Prompt Management," create a prompt like "Summarize this article in JSON format," and save it.
   - Go to "Search Management," input "AI trends 2025," set include domains ["example.com"], exclude domains ["spam.com"], click search, view results in a table (selector, URL, title, description, score, etc.), select all, and save as a URL list.
   - In "Settings," set scraping latency to 2 seconds, cache timeout to 24 hours, and save.
   - On "Extraction," select the URL list, click "Start Extraction" to cache content, and check status.
   - Go to "LLM Processing" tab, select the URL list and prompt. If any URL is uncached, the system prompts to cache first, showing a list like "URL1, URL2 not cached." After caching, process all, view results, and download as JSON for all.

2. **Backend Logic**:
   - For extraction:
     - Check cache for each URL using `utils.check_cache`.
     - If not cached or outdated, use Selenium:
       - Set user agent if configured, launch browser, navigate, wait for document ready state, extract content, save to cache.
   - For LLM processing:
     - Retrieve cached content for each URL, call LLM with prompt, generate output, and store for download.

##### Recommended Libraries and Versions

To ensure compatibility and proper functionality, use the following library versions, all available and working together as of March 22, 2025:

| Library              | Version   | Installation Command                     |
|----------------------|-----------|------------------------------------------|
| Tavily Python SDK    | 0.3.5     | `pip install tavily-python==0.3.5`       |
| Selenium             | 4.10.0    | `pip install selenium==4.10.0`           |
| Streamlit            | 1.25.0    | `pip install streamlit==1.25.0`          |
| OpenAI               | 1.68.2    | `pip install openai==1.68.2`             |
| Google Gen AI        | 0.8.4     | `pip install google-generativeai==0.8.4` |

Create a `requirements.txt` file with these specifications and run `pip install -r requirements.txt` to install all dependencies. Set API keys for Tavily, OpenAI, and Google Gen AI as environment variables for security.

##### Setting Up Selenium for Java-Heavy Pages

- **Installation**: Install Selenium with `pip install selenium==4.10.0`. Selenium 4 includes Selenium Manager, handling WebDriver binaries automatically.
- **Configuration**: Use `webdriver.Chrome()` with headless mode, set timeouts, and configure user agents for scraping, ensuring compatibility with complex sites.
- **Scraping**: Use explicit waits for document ready state and body presence, handling JavaScript-heavy pages effectively, storing content in cache.

##### Code Organization

- **Modular Structure**: Organize code into `app.py` for UI, `prompt_manager.py` for prompts, `search_manager.py` for searches, `url_list_manager.py` for URL lists, `extractor.py` for scraping and processing, `settings_manager.py` for settings, and `utils.py` for utilities.
- **Class-Based Design**: Use classes like `PromptManager` for CRUD, `Extractor` for scraping and LLM processing, ensuring encapsulation.
- **Background Tasks**: Run long tasks in threads to prevent UI blocking, updating session state for status checks.

This description ensures clarity on extraction and LLM processing, with detailed UI and backend logic for implementation, and compatible library versions for a seamless build.

Below is a suggested structure of files and directories for your project, designed to ensure clarity, modularity, and maintainability while aligning with the requirements outlined in your project description. This structure separates the Streamlit UI, backend logic, configuration, data storage, and utilities into distinct directories and files, making it easy to implement and extend.

---

### Suggested Structure of Files and Directories

```
project_root/
│
├── cache/                    # Directory to store cached URL content files
│   ├── <hash1>.json          # Example cached file for URL content (e.g., SHA-256 hash of URL)
│   ├── <hash2>.json          # Another cached file
│   └── ...
│
├── data/                     # Directory for JSON data files
│   ├── prompts.json          # Stores LLM prompts with fields: id, name, content, output_format, created_at
│   ├── url_lists.json        # Stores URL lists with metadata and Tavily search responses
│   └── settings.json         # Stores user settings (scraping latency, timeout, etc.)
│
├── src/                      # Source code directory
│   ├── __init__.py           # Makes src a Python package
│   ├── app.py                # Main Streamlit application for UI navigation and orchestration
│   ├── prompt_manager.py     # Module for managing LLM prompts (CRUD operations)
│   ├── search_manager.py     # Module for Tavily search integration (async client, CRUD)
│   ├── url_list_manager.py   # Module for managing URL lists (CRUD operations)
│   ├── extractor.py          # Module for URL extraction with Selenium and LLM processing
│   ├── settings_manager.py   # Module for managing user settings (CRUD operations)
│   └── utils.py              # Utility functions (JSON handling, caching, etc.)
│
├── tests/                    # Directory for unit tests
│   ├── __init__.py           # Makes tests a Python package
│   ├── test_prompt_manager.py  # Unit tests for prompt_manager.py
│   ├── test_search_manager.py  # Unit tests for search_manager.py
│   ├── test_url_list_manager.py # Unit tests for url_list_manager.py
│   ├── test_extractor.py      # Unit tests for extractor.py
│   ├── test_settings_manager.py # Unit tests for settings_manager.py
│   └── test_utils.py          # Unit tests for utils.py
│
├── requirements.txt          # List of Python dependencies with versions
├── README.md                 # Project documentation (setup, usage, etc.)
└── .gitignore                # Git ignore file (e.g., cache/, __pycache__/, *.pyc)
```

---

### Explanation of Structure

#### Root Directory (`project_root/`)
- **Purpose**: The top-level directory contains all project files and subdirectories, providing a clear entry point for development and deployment.
- **Key Files**:
  - `requirements.txt`: Lists dependencies with versions for easy setup (e.g., `tavily-python==0.3.5`, `selenium==4.10.0`, etc.).
  - `README.md`: Provides setup instructions (e.g., `pip install -r requirements.txt`, `streamlit run src/app.py`), usage guide, and project overview.
  - `.gitignore`: Excludes unnecessary files from version control (e.g., `cache/`, `__pycache__/`, `*.pyc`, `.env`).

#### Cache Directory (`cache/`)
- **Purpose**: Stores scraped content from URLs as JSON files, used for caching to avoid redundant scraping.
- **Structure**: Each file is named with a SHA-256 hash of the URL (e.g., `<hash>.json`) and contains the scraped content and a timestamp.
- **Role**: Managed by `extractor.py` for saving scraped content and checking cache freshness, ensuring the LLM processes cached data efficiently.

#### Data Directory (`data/`)
- **Purpose**: Stores persistent JSON data files for prompts, URL lists, and settings, keeping data separate from code for organization and portability.
- **Files**:
  - `prompts.json`: Stores prompt data with fields like `id`, `name`, `content`, `output_format`, and `created_at`.
  - `url_lists.json`: Stores URL lists with metadata and Tavily search responses, including fields like `id`, `name`, `urls`, `search_response`, and `created_at`.
  - `settings.json`: Stores settings profiles with parameters like scraping latency, timeout, LLM temperature, cache timeout, proxy settings, and max concurrent tasks.
- **Role**: Accessed by `prompt_manager.py`, `search_manager.py`, `url_list_manager.py`, and `settings_manager.py` for CRUD operations.

#### Source Directory (`src/`)
- **Purpose**: Contains all source code, organized as a Python package for modularity and maintainability.
- **Files**:
  - **`__init__.py`**: Marks `src/` as a Python package, enabling imports like `from src.prompt_manager import PromptManager`.
  - **`app.py`**: Main Streamlit application, defining UI pages for Prompt Management, Search Management, URL List Management, Settings, Extraction, LLM Processing, and Download. Orchestrates calls to other modules and manages `st.session_state` for state persistence.
  - **`prompt_manager.py`**: Implements `PromptManager` class with methods like `create_prompt`, `get_prompts`, `update_prompt`, and `delete_prompt`, handling CRUD operations on `prompts.json`.
  - **`search_manager.py`**: Implements `SearchManager` class with methods like `perform_search`, `get_searches`, `update_search`, and `delete_search`, using Tavily’s async client and managing `url_lists.json`.
  - **`url_list_manager.py`**: Implements `UrlListManager` class with methods like `create_list`, `get_lists`, `update_list`, and `delete_list`, managing URL lists in `url_lists.json`.
  - **`extractor.py`**: Implements `Extractor` class with methods like `extract_urls` for Selenium scraping and `process_llm` for LLM processing, caching content in `cache/` and running in background threads.
  - **`settings_manager.py`**: Implements `SettingsManager` class with methods like `create_settings`, `get_settings`, `update_settings`, and `delete_settings`, managing `settings.json`.
  - **`utils.py`**: Provides utility functions like `load_json`, `save_json`, `hash_url`, and `check_cache`, used across modules for common tasks.
- **Role**: Separates concerns, with `app.py` as the UI entry point and other modules handling backend logic, ensuring a clean structure.

#### Tests Directory (`tests/`)
- **Purpose**: Contains unit tests for each module to ensure functionality and reliability.
- **Files**:
  - **`__init__.py`**: Marks `tests/` as a Python package.
  - **`test_prompt_manager.py`**: Tests CRUD operations in `prompt_manager.py`.
  - **`test_search_manager.py`**: Tests Tavily search and CRUD in `search_manager.py`.
  - **`test_url_list_manager.py`**: Tests URL list management in `url_list_manager.py`.
  - **`test_extractor.py`**: Tests Selenium scraping and LLM processing in `extractor.py`.
  - **`test_settings_manager.py`**: Tests settings management in `settings_manager.py`.
  - **`test_utils.py`**: Tests utility functions in `utils.py`.
- **Role**: Ensures code quality and catches regressions, supporting maintainability.

#### Compatibility and Implementation Notes
- **Library Versions**: The structure aligns with `requirements.txt` (e.g., `selenium==4.10.0`, `streamlit==1.25.0`, `google-generativeai==0.8.4`), ensuring compatibility with Python 3.10+.
- **Directory Setup**: On project initialization, create `cache/` and `data/` directories if they don’t exist, using `os.makedirs` in `utils.py` or module initialization.
- **File Access**: Modules use relative paths from `src/` to access `../data/` and `../cache/`, ensuring consistent file handling.
- **Execution**: Run the app with `streamlit run src/app.py` from the project root, leveraging the modular structure.

#### Example Usage
- **Setup**: Clone the repository, run `pip install -r requirements.txt`, and set environment variables for API keys.
- **Run**: Execute `streamlit run src/app.py` to launch the UI, where users can navigate pages, manage prompts, perform searches, and process URLs.
- **Data Flow**: User creates a prompt, searches with Tavily, caches URLs with Selenium, processes with LLM, and downloads results, all managed by respective modules.

This structure ensures a clear separation of concerns, aligns with the project’s requirements for Tavily UI inputs, Selenium caching, and separate LLM processing, and provides a robust foundation for implementation with Cursor AI.

**Key Citations:**
- [Selenium Python Documentation](https://selenium-python.readthedocs.io/)
- [Tavily Python SDK](https://docs.tavily.com/sdk/python)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Python Official Documentation](https://docs.python.org/3/)
- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)