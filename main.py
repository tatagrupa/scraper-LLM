"""
LLM Web Scraper and Processor - Main entry point.
"""

import os
import sys
from pathlib import Path

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create cache and data directories if they don't exist
os.makedirs("cache", exist_ok=True)
os.makedirs("data", exist_ok=True)

import streamlit as st

# Initialize session state explicitly before importing app
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Prompt Management"

if "background_tasks" not in st.session_state:
    st.session_state["background_tasks"] = {}

if "extraction_results" not in st.session_state:
    st.session_state["extraction_results"] = {}

if "processing_results" not in st.session_state:
    st.session_state["processing_results"] = {}

# Import app after session state initialization
from src.app import main

if __name__ == "__main__":
    main() 