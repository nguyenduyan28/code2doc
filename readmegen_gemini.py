import google.generativeai as genai
# import os
# import re
genai.configure(api_key="")
import json
model = genai.GenerativeModel("gemini-2.0-flash-lite")

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

def generate_readme_from_github_url(code : str) -> str:
    # with open(filename, "r") as f:
    #     code = f.read()

    prompt = f'''
You are a technical writer. Given this JSON summary of a Python codebase, generate a clean and professional `README.md` file.


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

def generate_class_diagram(code):
    with open('class_list_enhanced.json', 'r') as f:
        data = json.load(f)
    prompt = f'''
I have a list of Python classes in JSON format. Each class includes:
- "name": class name
- "attributes": list of attribute names
- "methods": list of method names
- "inherits": list of base classes (optional)
- "dependencies": list of classes used (optional)

Please generate a PlantUML class diagram using the following rules:
- Use `class` blocks to define classes.
- Show attributes as `-attrName: type` if known.
- Show methods as `+methodName(params): returnType` if known.
- Use `A <|-- B` to show inheritance (B inherits A)
- Use `A ..> B` for dependencies (A uses B)
- Use `A --> B` for composition (A has B as member)
- Only return PlantUML code inside `@startuml` to `@enduml`, no explanations.

Here is the JSON:
```json
{data}
    '''
    try:
        response = model.generate_content(prompt)
        mermaid_class_code = response.text.strip().strip('"').strip("'")
        mermaid_class_code = clean_readme_output(mermaid_class_code)
        mermaid_class_code = mermaid_class_code.rstrip('\n```')
        return f'{mermaid_class_code}'
    except Exception as e:
        return f'"""[ERROR generating docstring: {str(e)}]"""'


def generate_usecase_diagram(code : str) -> str:
    # with open(filename, "r") as f:
    #     code = f.read()

    prompt = f'''
You are a software architect assistant.

Given this JSON summary of a Python codebase, Generate the use case diagram.

1. Extract **use cases** from class methods and top-level functions.
2. Group them by modules or logical domains.
3. Assume the actor interacting with user-facing functionality is "User" and with admin/internal features is "Admin" or "System".
4. Only return PlantUML code inside `@startuml` to `@enduml`, no explanations.

Here is the JSON summary of the codebase:
{code}

    '''
    try:
        response = model.generate_content(prompt)
        usecase_code= response.text.strip().strip('"').strip("'")
        usecase_code= clean_readme_output(usecase_code)
        usecase_code=usecase_code.rstrip('\n```')
        return f'{usecase_code}'
    except Exception as e:
        return f'"""[ERROR generating docstring: {str(e)}]"""'


def generate_dependency_graph_diagram(code : str) -> str:
    # with open(filename, "r") as f:
    #     code = f.read()

    prompt = f'''
You are a software architecture assistant.

Given the following summary of a software system (including modules, services, or technologies involved), generate a **Deployment Diagram** using **PlantUML** syntax.

- Identify the main components.
- Show how these components are deployed across nodes.
- Use `@startuml` and `@enduml`.
- Use `node`, `component`, and `database` to represent the system properly.
Do not use any `!include` directives from the PlantUML standard library.

Use only built-in PlantUML syntax like `node`, `component`, and `database`. 

Avoid cloud-specific icons or libraries like `<cloud_service/amazon_s3>`.
- Use the following skin settings for better design:

```plantuml
skinparam backgroundColor #f9f9f9
skinparam node {{
  BackgroundColor #ffffff
  BorderColor #999999
  FontColor #333333
}}
skinparam artifact {{
  BackgroundColor #ffffff
  BorderColor #aaaaaa
}}
skinparam database {{
  BackgroundColor #e1f5fe
  BorderColor #0288d1
  FontColor #01579b
}}

Here is the system summary in JSON format (modules, classes, functions):
{code}

    '''
    try:
        response = model.generate_content(prompt)
        usecase_code= response.text.strip().strip('"').strip("'")
        usecase_code= clean_readme_output(usecase_code)
        usecase_code=usecase_code.rstrip('\n```')
        return f'{usecase_code}'
    except Exception as e:
        return f'"""[ERROR generating docstring: {str(e)}]"""'