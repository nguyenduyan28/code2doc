import google.generativeai as genai

genai.configure(api_key="")

model = genai.GenerativeModel("gemini-2.0-flash")

def generate_docstring_gemini(code: str) -> str:
    prompt = f"""
You are a helpful assistant that writes high-quality Python docstrings for functions.

Write a concise and complete docstring for the following Python function:
{code}
"""
    try:
        response = model.generate_content(prompt)
        docstring = response.text.strip().strip('"').strip("'")
        if docstring.startswith("```python"):
            docstring = docstring.replace("```python", "", 1)
        if docstring.endswith("```"):
            docstring = docstring.replace("```", "", 1)
        return f'{docstring}'
    except Exception as e:
        return f'"""[ERROR generating docstring: {str(e)}]"""'
