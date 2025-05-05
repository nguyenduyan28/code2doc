import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from readmegen_gemini import generate_readme_from_github_url, generate_class_diagram, generate_usecase_diagram, generate_dependency_graph_diagram
from logzero import logger
import streamlit_mermaid as stmd
import requests
from get_data_github import get_repo_data, get_repo_class, extract_code_structure
from plantuml import PlantUML

# Load API key từ .env
load_dotenv()
GEMINI_API = os.getenv('GEMINI_API')
genai.configure(api_key=GEMINI_API)

st.title("GitHub README Generator")
st.write("Enter a GitHub repository URL to generate a README.")

url_input = st.text_area("GitHub URL", height=68, value="", key="url_input")

col1, col2, col3, col4 = st.columns(4)

with col1:
    generate_readme_button = st.button("Generate README")

with col2:
    generate_class_diagram_button = st.button("Generate Class Diagram")

with col3:
    generate_usecase_diagram_button = st.button("Generate Use Case Diagram")

with col4:
   generate_dependency_graph_diagram_button = st.button("Generate Deployment Diagram") 

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

if generate_usecase_diagram_button:
    if url_input.strip():
        try:
            all_code_content = extract_code_structure(url_input)
            read_me_all = generate_usecase_diagram(all_code_content)
            st.session_state.usecase_output= read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")

if generate_dependency_graph_diagram_button:
    if url_input.strip():
        try:
            all_code_content = extract_code_structure(url_input)
            read_me_all = generate_dependency_graph_diagram(all_code_content)
            st.session_state.graph_output= read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")

@st.cache_resource()
def get_uml_diagram_svg(uml_code):
    logger.info("Getting diagram from remote")
    url = PlantUML(url="http://www.plantuml.com/plantuml/img/")
    return url.get_url(uml_code)


def clear_screen(key_name):
    # for key in st.session_state.keys():
    #     print(key)
    #     if (key != key_name and key != 'url_input'):
    #         del st.session_state[key]
    pass

if "github_output" in st.session_state:
    clear_screen("github_output")
    st.subheader("Generated README:")
    st.markdown(st.session_state.github_output)

if "class_output" in st.session_state:
    clear_screen("class_output")
    st.subheader("Generated class diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.class_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='class_diagram.png')

if "usecase_output" in st.session_state:
    clear_screen("usecase_output")
    st.subheader("Generated use case diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.usecase_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='usecase.png')

if "graph_output" in st.session_state:
    clear_screen("graph_output")
    st.subheader("Generated deployment diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.graph_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='dependency_graph.png')