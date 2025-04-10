import google.generativeai as genai
# import os
# import re
genai.configure(api_key="")
model = genai.GenerativeModel("gemini-2.0-flash")

def clean_readme_output(text: str) -> str:
    lines = text.strip().splitlines()
    if lines:
        lines = lines[1:]

    if lines and '"""' in lines[-1]:
        lines = lines[:-1]

    return '\n'.join(lines).strip()


def clean_markdown_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and '"""```markdown' or '```markdown' in lines[0]:
        lines = lines[1:]  # Bỏ dòng đầu
    if lines and lines[-1].strip().endswith('```"""') or '```"""' in lines[-1]:
        lines[-1] = lines[-1].replace('```"""', '').strip()
    return '\n'.join(lines).strip()

def generate_readme_from_code(code : str) -> str:
    # with open(filename, "r") as f:
    #     code = f.read()

    prompt = f'''
You are a technical writer. Given the following Python code, generate a clean and professional `README.md` file.

Output requirements:
- Start with a clear project title and short description.
- Include a **Table of Contents** with links to sections (using markdown anchor links).
- Add sections such as: `Installation`, `Usage`, `Functions` (with explanations and examples), and `License`.
- Use appropriate markdown headers (`#`, `##`, `###`).
- Write in pure markdown — **do NOT** use triple quotes (`"""`) or markdown code fences like ```markdown.
- Only return the markdown content. No extra explanation.

Here is the code:
{code}
'''
    try:
        response = model.generate_content(prompt)
        docstring = response.text.strip().strip('"').strip("'")
        docstring = clean_readme_output(docstring)
        return f'{docstring}'
    except Exception as e:
        return f'"""[ERROR generating docstring: {str(e)}]"""'