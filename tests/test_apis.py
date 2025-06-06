import os
import pytest
import requests
import google.generativeai as genai
import openai

# Fetch API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Ensure variable name matches the workflow secret
GPT_API_KEY = os.getenv("OPENAI_API_KEY")  # Ensure variable name matches the workflow secret

# Configure Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Test function to check Gemini API
def test_gemini_api():
    # Use genai to make a request to Gemini
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say Hello")
        assert "hello" in response.text.lower(), f"Expected 'hello' in response, got: {response.text}"
    except Exception as e:
        pytest.fail(f"Gemini API test failed: {e}")

def test_gpt_3_5_api():
    try:
        response = openai.OpenAI(api_key=GPT_API_KEY).chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": "Say hello"}
            ]
        )
        content = response.choices[0].message.content.strip().lower()
        assert "hello" in content, f"Unexpected response content: {content}"

    except Exception as e:
        pytest.fail(f"GPT-3.5 API test failed: {e}")

# Run the tests
if __name__ == "__main__":
    pytest.main()
