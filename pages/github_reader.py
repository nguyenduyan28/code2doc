import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from readmegen_gemini import generate_readme_from_github_url, generate_class_diagram, generate_usecase_diagram, generate_dependency_graph_diagram, generate_sad
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

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    generate_readme_button = st.button("Generate README")

with col2:
    generate_class_diagram_button = st.button("Generate Class Diagram")

with col3:
    generate_usecase_diagram_button = st.button("Generate Use Case Diagram")

with col4:
   generate_dependency_graph_diagram_button = st.button("Generate Deployment Diagram") 


with col5:
    generate_sad_docs = st.button("Generate Software Architecture Document")


@st.cache_resource()
def get_uml_diagram_svg(uml_code):
    logger.info("Getting diagram from remote")
    url = PlantUML(url="http://www.plantuml.com/plantuml/img/")
    return url.get_url(uml_code)


def clear_screen(key_name):
    keys_to_keep = {"url_input", key_name}
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]

if generate_readme_button:
    if url_input.strip():
        try:
            clear_screen("github_output")
            all_code_content = extract_code_structure(url_input)
            read_me_all = generate_readme_from_github_url(all_code_content)
            st.session_state.github_output = read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")

if generate_class_diagram_button:
    if url_input.strip():
        try:
            clear_screen("class_output")
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
            clear_screen("usecase_output")
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
            clear_screen("graph_output")
            all_code_content = extract_code_structure(url_input)
            read_me_all = generate_dependency_graph_diagram(all_code_content)
            st.session_state.graph_output= read_me_all
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid GitHub URL.")
    
if generate_sad_docs:
    if url_input.strip():
        try:
            clear_screen("sad_output")
            summary = extract_code_structure(url_input)
            usecase_code = generate_usecase_diagram(summary)
            deploy_code = generate_dependency_graph_diagram(summary)
            class_code = generate_class_diagram(get_repo_class(url_input))

            usecase_url = get_uml_diagram_svg(usecase_code)
            deploy_url = get_uml_diagram_svg(deploy_code)
            class_url = get_uml_diagram_svg(class_code)

            sad_doc = generate_sad(summary, usecase_url, deploy_url, class_url)

            st.session_state.sad_output = sad_doc

        except Exception as e:
            st.error(f"Error: {str(e)}")




if "github_output" in st.session_state:
    st.subheader("Generated README:")
    st.markdown(st.session_state.github_output)

if "class_output" in st.session_state:
    st.subheader("Generated class diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.class_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='class_diagram.png')

if "usecase_output" in st.session_state:
    st.subheader("Generated use case diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.usecase_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='usecase.png')

if "graph_output" in st.session_state:
    st.subheader("Generated deployment diagram: ")
    img_url = get_uml_diagram_svg(st.session_state.graph_output)
    img_response = requests.get(img_url)
    st.image(img_response.content)
    st.download_button('Download Image', img_response.content, file_name='dependency_graph.png')

if "sad_output" in st.session_state:
    st.subheader("Generated SAD:")
    st.markdown(st.session_state.sad_output)

    st.subheader("Use Case Diagram")
    img_url = get_uml_diagram_svg(st.session_state.sad_usecase)
    st.image(requests.get(img_url).content)

    st.subheader("Deployment Diagram")
    img_url = get_uml_diagram_svg(st.session_state.sad_deploy)
    st.image(requests.get(img_url).content)

    st.subheader("Class Diagram")
    img_url = get_uml_diagram_svg(st.session_state.sad_class)
    st.image(requests.get(img_url).content)