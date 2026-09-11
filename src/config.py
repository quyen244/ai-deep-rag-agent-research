from dotenv import load_dotenv
import os 

load_dotenv()

class Config:
    # API KEY
    OPENROUTER_API_KEY = os.getenv('OPPENROUTER_API_KEY' , "sh-")
    MODEL_NAME = os.getenv('MODEL_NAME' , 'nemotrion-flash')
    temperature = 0.3
    top_p = 0.9


    # LangSmith config
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "default")
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

    if LANGCHAIN_TRACING_V2:
        print(f"🔍 LangSmith Tracing ENABLED - Project: {LANGCHAIN_PROJECT}")
    else:
        print("⚠️ LangSmith Tracing DISABLED")

    