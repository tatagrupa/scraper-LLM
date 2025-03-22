# LLM Web Scraper and Processor

A Python application that integrates Tavily search, Selenium web scraping, and LLM processing to extract and analyze data from websites.

## Features

- **Prompt Management**: Create, edit, and store LLM prompts
- **Tavily Search Integration**: Search the web with customizable parameters
- **URL List Management**: Organize and manage URL lists for scraping
- **Web Scraping with Selenium**: Extract content from URLs with caching
- **LLM Processing**: Process scraped content with OpenAI or Google Gemini
- **Settings Management**: Configure application behavior

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   # Create a .env file with:
   TAVILY_API_KEY=your_tavily_api_key
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```
4. Run the application:
   ```
   streamlit run src/app.py
   ```

## Project Structure

- `src/`: Source code
- `data/`: JSON data files (prompts, URL lists, settings)
- `cache/`: Cached URL content
- `tests/`: Unit tests

## License

This project is licensed under the MIT License - see the LICENSE file for details. 