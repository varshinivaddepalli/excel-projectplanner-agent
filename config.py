"""
Configuration for Azure OpenAI and project settings
"""
import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_llm() -> AzureChatOpenAI:
    """
    Initialize and return Azure OpenAI LLM instance.
    
    Returns:
        AzureChatOpenAI: Configured LLM instance
    """
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_GPT_ENDPOINT")
    azure_deployment = os.environ.get("AZURE_OPENAI_GPT_DEPLOYMENT", "gpt-4o-mini")
    
    if not api_key or not azure_endpoint:
        raise ValueError(
            "Missing Azure OpenAI credentials. "
            "Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_GPT_ENDPOINT in .env file"
        )
    
    llm = AzureChatOpenAI(
        azure_deployment=azure_deployment,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version="2024-02-15-preview",
        temperature=0.2
    )
    
    return llm


# Project constants
PROJECT_TYPES = [
    "Highrise",
    "Standalone Building",
    "Villa",
    "Commercial",
    "Infrastructure"
]

PLAN_LEVELS = [
    "High-level Plan",
    "Detailed Plan"
]

START_DATE_OPTIONS = [
    "Immediate",
    "Within 1 Month",
    "Custom Date"
]

# High-level plan columns
HIGH_LEVEL_COLUMNS = [
    "Phase Name",
    "Activity Name",
    "Task Name",
    "Task Category",
    "Task Duration"
]

# Detailed plan columns
DETAILED_COLUMNS = [
    "Phase Name",
    "Activity Name",
    "Task Name",
    "Task Category",
    "Task Start Date",
    "Task End Date",
    "Work Quantity",
    "Work Rate",
    "Work UOM",
    "Task Description",
    "Priority",
    "Predecessor",
    "Dependency Type",
    "Successor"
]

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# Prompts directory
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

