import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from readmegen_gemini import generate_readme_from_github_url, generate_class_diagram
import streamlit_mermaid as stmd
from get_data_github import get_repo_data, get_repo_class

# Load API key từ .env
load_dotenv()
GEMINI_API = os.getenv('GEMINI_API')
genai.configure(api_key=GEMINI_API)

st.title("GitHub README Generator")
st.write("Enter a GitHub repository URL to generate a README.")

url_input = st.text_area("GitHub URL", height=68, value="", key="url_input")

col1, col2 = st.columns(2)

with col1:
    generate_readme_button = st.button("Generate README from URL")

with col2:
    generate_class_diagram_button = st.button("Generate Class Diagram")

if generate_readme_button:
    if url_input.strip():
        try:
            all_code_content = get_repo_data(url_input)
            read_me_all = generate_readme_from_github_url(all_code_content)
            st.session_state.github_output = read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")

if generate_class_diagram_button:
    if url_input.strip():
        try:
            all_code_content = get_repo_class(url_input)
            class_content = generate_class_diagram(all_code_content)
            st.session_state.class_output = (class_content)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")


if "github_output" in st.session_state:
    st.subheader("Generated README:")
    st.markdown(st.session_state.github_output)

if "class_output" in st.session_state:
    st.subheader("Generated class diagram: ")
    print(st.session_state.class_output)
    stmd.st_mermaid(st.session_state.class_output, height="1000px")
