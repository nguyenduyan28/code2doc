import requests
import os
from dotenv import load_dotenv

def get_repo_data(url, prefix=""):
    try:
        headers = {"Authorization": f"token {os.getenv('ACCESS_TOKEN')}"}
        user, repo = url.split('/')[-2], url.split('/')[-1]
        repo_url = f"https://api.github.com/repos/{user}/{repo}/contents{prefix}"
        response = requests.get(repo_url, headers=headers)
        files = response.json()
        
        if not isinstance(files, list):
            return "Error: Unable to fetch repo contents, please check the URL or rate limits"
    except Exception as e:
        return f"Error: Invalid URL or request failed - {str(e)}"

    content = ""
    # Các định dạng file cần lấy
    allowed_extensions = ['html', 'css', 'js', 'cpp', 'c', 'py']

    for file in files:
        if file["type"] == "file":
            # Lấy phần mở rộng của file
            file_extension = file['name'].split('.')[-1]
            if file_extension in allowed_extensions:
                content += 'BEGINFILE ' + file['path'] + '\n'  # Dùng file['path'] để hiển thị đường dẫn đầy đủ
                content += requests.get(file["download_url"]).text
                content += '\nENDFILE\n'
        elif file["type"] == "dir":
            # Nếu là thư mục, gọi đệ quy với đường dẫn mới
            subdir_content = get_repo_data(url, prefix="/" + file["path"])
            content += subdir_content

    return content
