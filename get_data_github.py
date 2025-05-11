import os
import ast
import json
from collections import defaultdict
from git import Repo
from typing import List, Dict, Set, Tuple
from pathlib import Path

# Hàm chung để clone và thu thập file (đã có từ trước)
def _clone_and_collect_files(url: str, local_dirs: str = './repo') -> Tuple[str, List[Dict]]:
    """
    Clone a repository and collect file information.

    Args:
        url (str): Git repository URL.
        local_dirs (str): Directory to store the repo.

    Returns:
        Tuple[str, List[Dict]]: Local path and list of file metadata.
    """
    repo_name = url.split('/')[-1].split('.')[0]
    local_path = os.path.join(local_dirs, repo_name)

    if not os.path.exists(local_path):
        print(f"Cloning repository from {url} to {local_path}...")
        Repo.clone_from(url, local_path, depth=1)
    else:
        print(f"Repository already exists at {local_path}, skipping clone.")

    allowed_extensions = ['py', 'cpp', 'html', 'js']
    file_metadata = []

    for root, _, files in os.walk(local_path):
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext in allowed_extensions or file in ['requirements.txt', 'package.json', '.env', 'Dockerfile', '.gitignore']:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, local_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except (UnicodeDecodeError, IOError) as e:
                    print(f"Skipping {file_path} due to error: {e}")
                    continue

                file_metadata.append({
                    "path": file_path,
                    "rel_path": rel_path,
                    "extension": ext if ext in allowed_extensions else file,
                    "content": content
                })

    return local_path, file_metadata

# Hàm get_repo_data (giữ nguyên từ code trước)
def get_repo_data(url: str, local_dirs: str = './repo') -> str:
    """
    Collect all code content from a repository.

    Args:
        url (str): Git repository URL.
        local_dirs (str): Directory to store the repo.

    Returns:
        str: Concatenated code content with file markers.
    """
    local_path, file_metadata = _clone_and_collect_files(url, local_dirs)

    content = ""
    for file in file_metadata:
        content += f'BEGINFILE {file["rel_path"]}\n{file["content"]}ENDFILE\n'

    output_file = os.path.join(local_dirs, 'code.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Code content saved to {output_file}")

    return content

# Hàm get_repo_class (giữ nguyên từ code trước)
def get_repo_class(url: str, local_dirs: str = './repo') -> List[Dict]:
    """
    Extract all classes and their dependencies from Python files in a Git repository.

    Args:
        url (str): Git repository URL.
        local_dirs (str): Directory to store the repo.

    Returns:
        List[Dict]: List of dictionaries containing class details.
    """
    local_path, file_metadata = _clone_and_collect_files(url, local_dirs)

    list_of_classes = []
    class_names = set()
    imported_classes = defaultdict(set)

    for file in file_metadata:
        if file["extension"] != 'py':
            continue

        rel_path = file["rel_path"]
        try:
            tree = ast.parse(file["content"], filename=rel_path)
        except SyntaxError as e:
            print(f"Skipping {rel_path} due to error: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    imported_classes[rel_path].add(name.name)

    for file in file_metadata:
        if file["extension"] != 'py':
            continue

        rel_path = file["rel_path"]
        try:
            tree = ast.parse(file["content"], filename=rel_path)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                inherits = [base.id for base in node.bases if isinstance(base, ast.Name)]
                methods = []
                attributes = set()
                dependencies = set()

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = item.name
                        methods.append(method_name)

                        for arg in ast.walk(item):
                            if isinstance(arg, ast.Name) and arg.id in class_names and arg.id != class_name:
                                dependencies.add(arg.id)

                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        for stmt in item.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if (isinstance(target, ast.Attribute) and
                                        isinstance(target.value, ast.Name) and
                                        target.value.id == 'self'):
                                        attributes.add(target.attr)

                                        if isinstance(stmt.value, ast.Call):
                                            func = stmt.value.func
                                            if isinstance(func, ast.Name) and func.id in class_names:
                                                dependencies.add(func.id)
                                            elif isinstance(func, ast.Attribute):
                                                if func.attr in class_names:
                                                    dependencies.add(func.attr)

                dependencies.update(imported_classes[rel_path])
                dependencies.discard(class_name)

                list_of_classes.append({
                    "name": class_name,
                    "inherits": inherits,
                    "attributes": list(attributes),
                    "methods": methods,
                    "dependencies": list(dependencies)
                })

    output_file = os.path.join(local_dirs, 'class_list_enhanced.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list_of_classes, f, indent=2)
    print(f"Class list saved to {output_file}")

    return list_of_classes

# Hàm extract_code_structure (giữ nguyên từ code trước)
def extract_code_structure(url: str, local_dirs: str = './repo') -> Dict:
    """
    Extract code structure from Python files in a repository.

    Args:
        url (str): Git repository URL.
        local_dirs (str): Directory to store the repo.

    Returns:
        Dict: Code structure with classes and functions.
    """
    local_path, file_metadata = _clone_and_collect_files(url, local_dirs)

    code_summary = defaultdict(lambda: {"classes": {}, "functions": []})

    for file in file_metadata:
        if file["extension"] != 'py':
            continue

        rel_path = file["rel_path"]
        try:
            tree = ast.parse(file["content"], filename=rel_path)
        except SyntaxError:
            continue

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                method_names = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                code_summary[rel_path]["classes"][node.name] = {"methods": method_names}
            elif isinstance(node, ast.FunctionDef):
                code_summary[rel_path]["functions"].append(node.name)

    output_file = os.path.join(local_dirs, 'repo_summary.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(code_summary, f, indent=2)
    print(f"Code structure saved to {output_file}")

    return code_summary

# Hàm mới để lấy thông tin cho README
def extract_for_readme(url: str, local_dirs: str = './repo') -> Dict:
    """
    Extract information from a repository for generating a README.

    Args:
        url (str): Git repository URL.
        local_dirs (str): Directory to store the repo.

    Returns:
        Dict: Code structure with classes, functions, and additional metadata for README.
    """
    local_path, file_metadata = _clone_and_collect_files(url, local_dirs)

    # Output chính (giữ giống extract_code_structure)
    code_summary = defaultdict(lambda: {"classes": {}, "functions": []})

    # Thông tin bổ sung cho README
    config_files = {}
    docstrings = defaultdict(list)
    directory_structure = defaultdict(list)
    file_types = defaultdict(int)
    dependencies = defaultdict(list)

    for file in file_metadata:
        rel_path = file["rel_path"]
        ext = file["extension"]
        content = file["content"]

        # Thu thập cấu trúc thư mục
        dir_name = os.path.dirname(rel_path)
        directory_structure[dir_name].append(rel_path)

        # Đếm loại file
        file_types[ext] += 1

        # Xử lý file Python
        if ext == 'py':
            try:
                tree = ast.parse(content, filename=rel_path)
            except SyntaxError:
                continue

            # Thu thập classes và functions (giống extract_code_structure)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    method_names = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    code_summary[rel_path]["classes"][node.name] = {"methods": method_names}
                elif isinstance(node, ast.FunctionDef):
                    code_summary[rel_path]["functions"].append(node.name)

            # Thu thập docstrings
            for node in ast.walk(tree):
                if (isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)) and
                        node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Str)):
                    docstrings[rel_path].append({
                        "name": node.name if hasattr(node, 'name') else "module",
                        "docstring": node.body[0].value.s.strip()
                    })

        # Xử lý file config
        if ext in ['requirements.txt', 'package.json', '.env', 'Dockerfile', '.gitignore']:
            config_files[rel_path] = content

            # Phân tích dependencies từ file config
            if ext == 'requirements.txt':
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies['python'].append(line.split('==')[0] if '==' in line else line)
            elif ext == 'package.json':
                try:
                    package_data = json.loads(content)
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    dependencies['javascript'].extend(list(deps.keys()))
                    dependencies['javascript'].extend(list(dev_deps.keys()))
                except json.JSONDecodeError:
                    print(f"Skipping {rel_path} due to invalid JSON")

    # Lưu thông tin bổ sung vào file riêng (không thêm vào output chính)
    readme_metadata = {
        "config_files": config_files,
        "docstrings": dict(docstrings),
        "directory_structure": dict(directory_structure),
        "file_types": dict(file_types),
        "dependencies": dict(dependencies)
    }
    output_file = os.path.join(local_dirs, 'readme_metadata.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(readme_metadata, f, indent=2)
    print(f"README metadata saved to {output_file}")

    # Output chính chỉ chứa classes và functions
    output_file = os.path.join(local_dirs, 'readme_summary.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(code_summary, f, indent=2)
    print(f"Code structure for README saved to {output_file}")

    return readme_metadata
