# test_wrapper.py
import os
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from src.config import Config

# 1. Tạo OpenAI client (dùng OpenRouter base_url)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=Config.OPENROUTER_API_KEY,
    timeout=120,
    max_retries=3,
)

# 2. Wrap với LangSmith (nếu bật tracing)
if Config.LANGCHAIN_TRACING_V2:
    client = wrap_openai(client)
    print("✅ OpenAI client wrapped with LangSmith")

# 3. Test với @traceable
@traceable(name="test_openai_wrapper", run_type="llm")
def test_openai_wrapper():
    """Test OpenAI wrapper với LangSmith tracing"""
    
    print("🔄 Testing OpenAI wrapper...")
    print(f"Model: {Config.MODEL_NAME}")
    
    try:
        response = client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello World' in Vietnamese"}
            ],
            temperature=Config.temperature,
            max_tokens=100,
        )
        
        result = response.choices[0].message.content
        print(f"✅ Response: {result}")
        
        # In thông tin trace
        if Config.LANGCHAIN_TRACING_V2:
            print("\n🔗 Check LangSmith for trace details!")
            
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

test_openai_wrapper()