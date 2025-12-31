import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables (using the names from your .env file)
api_key = os.environ.get("AZURE_OPENAI_API_KEY")
azure_endpoint = os.environ.get("AZURE_OPENAI_GPT_ENDPOINT")
azure_deployment = os.environ.get("AZURE_OPENAI_GPT_DEPLOYMENT", "gpt-4o-mini")

llm = AzureChatOpenAI(
    azure_deployment=azure_deployment,
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version="2024-02-15-preview",
    temperature=0.2
)

result = llm.invoke("what is machine learning")
print(result.content)