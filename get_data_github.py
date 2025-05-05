import requests
import os
from git import Repo
from dotenv import load_dotenv
import timeit
import ast
import json
from collections import defaultdict
import ast
import os
import json
from collections import defaultdict
from git import Repo
def get_repo_data(url, local_dirs = './repo'):
    local_dirs = './' + url.split('/')[-1].split('.')[0]
    allowed_list = ['py', 'cpp', 'html', 'js']
    content = ""
    if (not os.path.exists(local_dirs)):
        Repo.clone_from(url, local_dirs, depth = 1)
        with open('code.txt', 'w') as f:
            f.write('-1')
        for root, dirs, files in os.walk(local_dirs):
            for file in files:
                if file.split('.')[-1] in allowed_list and not file.startswith('__'):
                    filename = os.path.join(root, file)
                    with open(filename, 'r') as f:
                        content += f'BEGINFILE f{filename}\n{f.read()}ENDFILE\n' 
        with open('code.txt', 'w') as f:
            f.write(content)
    else: 
        with open('code.txt', 'r') as f:
            content = f.read()
    return content




def get_repo_class(url, local_dirs='./repo'):
    local_dirs = './' + url.split('/')[-1].split('.')[0]
    allowed_list = ['py']
    list_of_classes = []
    class_names = set()

    if not os.path.exists(local_dirs): 
        Repo.clone_from(url, local_dirs, depth=1)

    for root, dirs, files in os.walk(local_dirs):
        for file in files:
            if file.split('.')[-1] in allowed_list and not file.startswith('__'):
                filename = os.path.join(root, file)
                with open(filename, 'r') as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        class_names.add(class_name)

    for root, dirs, files in os.walk(local_dirs):
        for file in files:
            if file.split('.')[-1] in allowed_list and not file.startswith('__'):
                filename = os.path.join(root, file)
                with open(filename, 'r') as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        inherits = [base.id for base in node.bases if isinstance(base, ast.Name)]
                        methods = []
                        attributes = set()
                        dependencies = set()

                        for n in node.body:
                            if isinstance(n, ast.FunctionDef):
                                method_name = n.name
                                methods.append(method_name)

                                for arg in ast.walk(n):
                                    if isinstance(arg, ast.Name) and arg.id in class_names and arg.id != class_name:
                                        dependencies.add(arg.id)

                            if isinstance(n, ast.FunctionDef) and n.name == '__init__':
                                for stmt in n.body:
                                    if isinstance(stmt, ast.Assign):
                                        for target in stmt.targets:
                                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                                attributes.add(target.attr)

                                                # Check if value is instantiating another class
                                                if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                                                    if stmt.value.func.id in class_names:
                                                        dependencies.add(stmt.value.func.id)

                        list_of_classes.append({
                            "name": class_name,
                            "inherits": inherits,
                            "attributes": list(attributes),
                            "methods": methods,
                            "dependencies": list(dependencies)
                        })

    with open('class_list_enhanced.json', 'w') as f:
        json.dump(list_of_classes, f, indent=2)

    return list_of_classes


def extract_code_structure(url, repo_path="./repo"):
    repo_path = './' + url.split('/')[-1].split('.')[0]
    code_summary = defaultdict(lambda: {"classes": {}, "functions": []})
    if (not os.path.exists(repo_path)):
        Repo.clone_from(url, repo_path, depth = 1)

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)

                with open(full_path, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=rel_path)
                    except SyntaxError:
                        continue  # skip invalid Python files

                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef):
                        method_names = [
                            n.name for n in node.body if isinstance(n, ast.FunctionDef)
                        ]
                        code_summary[rel_path]["classes"][node.name] = {
                            "methods": method_names
                        }
                    elif isinstance(node, ast.FunctionDef):
                        code_summary[rel_path]["functions"].append(node.name)
    with open('repo_summary.json', 'w') as f:
        json.dump(code_summary, f, indent=2)
    return code_summary


 


    



    