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

    Generate a **Deployment Diagram** using **PlantUML**, using only built-in syntax (`node`, `component`, `database`, `artifact`). 
    Avoid any syntax errors or broken references.

    Rules:
    - Wrap each deployment unit (server, client) in a `node`
    - Use unique identifiers for each component (e.g., `dbPostgreSQL`, `webApp`)
    - Do **NOT** create a component or database inside a node and reference it from outside by a different name
    - Use `-->` to link nodes/components with descriptive labels (e.g., `: uses`)

    Use this skin setting:
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

    Here is the system summary in JSON format:
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
    

def generate_sad(summary: str, usecase_url: str, deploy_url: str, class_url: str) -> str:
    prompt = f'''
You are a software architect assistant.

Given the following **JSON summary of a Python codebase**, generate a **Software Architecture Document (SAD)** in **pure markdown**, based on the following structure (from a real-world software architecture PDF):

---

## 1. Introduction
- **1.1 Purpose**
- **1.2 Scope**
- **1.3 Definitions, Acronyms, Abbreviations**
- **1.4 Overview**

## 2. Architectural Goals and Constraints

## 3. Use-Case Model
- High-level use-case overview
Insert the use-case diagram image using this markdown:
![Use Case Diagram]({usecase_url})

## 4. Logical View
-- System components and responsibilities
- For each major component:
    Insert the class diagram here:
    ![Class Diagram]({class_url})
    - Description of key classes, attributes, methods

## 5. Deployment View
- 5.1 Client-side components
- 5.2 Server-side components
- 5.3 External services
Show the deployment diagram:
![Deployment Diagram]({deploy_url})
- Summary of infrastructure

## 6. Implementation View
- Structure of source code: packages/modules
- Build and run instructions if available
- Technologies, frameworks used
---

**Rules**:
- Markdown only, no PlantUML code
- Just insert images using markdown `![alt](url)`
- Write structured, clean, and concise

System summary:
{summary}
'''
    try:
        response = model.generate_content(prompt)
        sad_markdown = response.text.strip().strip('"').strip("'")
        sad_markdown = clean_readme_output(sad_markdown)
        return f'{sad_markdown}'
    except Exception as e:
        return f'[ERROR generating SAD: {str(e)}]'