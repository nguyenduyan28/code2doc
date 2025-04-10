import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from readmegen_gemini import generate_readme_from_github_url
from get_data_github import get_repo_data

# Load API key từ .env
load_dotenv()
GEMINI_API = os.getenv('GEMINI_API')
genai.configure(api_key=GEMINI_API)

# Giao diện trang GitHub Reader
st.title("GitHub README Generator")
st.write("Enter a GitHub repository URL to generate a README.")

# Box input URL
url_input = st.text_area("GitHub URL", height=68, value="", key="url_input")

# Nút Read URL
if st.button("Generate README from URL"):
    if url_input.strip():
        try:
            all_code_content = get_repo_data(url_input)
            read_me_all = generate_readme_from_github_url(all_code_content)
            st.session_state.github_output = read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")

if "github_output" in st.session_state:
    st.subheader("Generated README:")
    st.markdown(st.session_state.github_output)