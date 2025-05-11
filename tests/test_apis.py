import os
import pytest
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Fetch API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API")
GPT_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# API URL for GPT-3.5 Turbo
GPT_API_URL = "https://api.openai.com/v1/chat/completions"

# Test function to check Gemini API
def test_gemini_api():
    # Use genai to make a request to Gemini
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("test query")
        assert response, "No response from Gemini API"
        assert response.text, "No text content found in Gemini response"
    except Exception as e:
        pytest.fail(f"Gemini API test failed: {e}")

# Test function to check GPT-3.5 Turbo API
def test_gpt_3_5_api():
    headers = {
        "Authorization": f"Bearer {GPT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Request payload for GPT-3.5 Turbo
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."}, 
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50
    }
    
    # Send a sample request to the GPT-3.5 Turbo API
    response = requests.post(GPT_API_URL, json=payload, headers=headers)
    
    assert response.status_code == 200, f"GPT API failed with status code {response.status_code}"
    assert "choices" in response.json(), "No choices found in GPT response"

# Run the tests
if __name__ == "__main__":
    pytest.main()