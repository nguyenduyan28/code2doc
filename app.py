import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from readmegen_gemini import generate_readme_from_code

# Load API key từ .env
load_dotenv()
GEMINI_API = os.getenv('GEMINI_API')
genai.configure(api_key=GEMINI_API)
model = genai.GenerativeModel("gemini-2.0-flash")

# Hàm tạo docstring
def generate_docstring(code):
    prompt = f"""
    Given the following Python function, generate a detailed docstring in Google style:
    {code}
    just give docstring right after def and then the exactly code from {code}, not fix code or plus any information. 
    Return only function and docstring, does not return in markdown or anything else.
    """
    response = model.generate_content(prompt)
    return response.text

# Hàm dịch code
def convert_code(code, lang_trans):
    prompt = f"""
    Given the following Python code, generate code translated into {lang_trans} language:
    {code}
    Return only the translated code in plain text, does not return in markdown or anything else.
    """
    response = model.generate_content(prompt)
    return response.text

# Giao diện chính
st.title("AI-Powered Code Tools")
st.write("Enter a Python function below to use the tools.")

function_input = st.text_area("Python Function", height=200, value="def add(a, b):\n    return a + b", key="input_box")

with st.sidebar:
    # Nút Generate Docstring
    if st.button("Generate Docstring"):
        if function_input.strip():
            try:
                docstring = generate_docstring(function_input)
                docstring = (docstring.rstrip('```'))
                docstring = docstring.lstrip(f'```"python"')
                st.session_state.output_content = docstring
                st.session_state.output_language = "python"
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a Python function.")

    # if st.button("Translate Code"):
    #     st.session_state.show_selectbox = True  # Hiển thị selectbox
    if st.button("Readme generator"):
        if function_input.strip():
            try:
                read_me_content = generate_readme_from_code(function_input)
                st.session_state.output_content = read_me_content
                st.session_state.output_language = "markdown"
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a Python function.")

    if "show_selectbox" not in st.session_state:
        st.session_state.show_selectbox = False
    with st.form("Language"):
        st.write("Translated Code")
        lang_trans = st.selectbox("Select language", ["C", "C++", "Javascript"], label_visibility="collapsed")
        submitted = st.form_submit_button("Submit")
        language_map = {"C": "c", "C++": "cpp", "Javascript": "javascript", "python": "python"}
        if submitted:
            if function_input.strip():
                try:
                    code_translated = convert_code(function_input, lang_trans)
                    code_translated = code_translated.rstrip('```')
                    code_translated = code_translated.lstrip(f'```{language_map[lang_trans]}')
                    st.session_state.output_content = code_translated
                    st.session_state.output_language = lang_trans
                    st.session_state.show_selectbox = False  # Ẩn selectbox sau khi dịch
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a Python function.")

# Phần chính: Box output (nằm dưới box input)
if "output_content" not in st.session_state:
    content = '''

def add(a, b):
    """Adds two numbers together.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of a and b.
    """
    return a + b

'''
    st.session_state.output_content = content
if "output_language" not in st.session_state:
    st.session_state.output_language = "python"

#if st.session_state.output_content:
st.subheader("Result:")
language_map = {"C": "c", "C++": "cpp", "Javascript": "javascript", "python": "python"}
st.code(st.session_state.output_content, language=language_map.get(st.session_state.output_language, "python"))