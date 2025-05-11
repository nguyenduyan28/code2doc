import streamlit as st
import tempfile
from pathlib import Path
import os
import re

from pipeline_module import CodeToDocPipeline
from dotenv import load_dotenv
load_dotenv()


st.set_page_config(page_title="Code Analyzer", layout="wide")
st.title("🧠 Code-to-Document Analyzer")
st.write("Upload a Python script to analyze and generate a technical report.")

uploaded_file = st.file_uploader("📤 Upload your Python file", type=["py"])

if uploaded_file:
    paper_name = uploaded_file.name.replace(".py", "")
    gpt_version = st.selectbox("🧠 Select GPT Version", ["gpt-3.5-turbo", "gpt-4"], index=0)

    if st.button("🚀 Run Analysis Pipeline"):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_input = Path(tmpdir) / f"{paper_name}.py"
            output_dir = Path(tmpdir) / "outputs"
            tmp_input.write_bytes(uploaded_file.read())

            try:
                pipeline = CodeToDocPipeline(
                    input_file=str(tmp_input),
                    output_dir=str(output_dir),
                    paper_name=paper_name,
                    gpt_version=gpt_version
                )
                pipeline.run_all()

                st.success("✅ Report generated successfully!")

                paper_md = output_dir / "paper.md"
                if paper_md.exists():
                     paper_md = output_dir / "paper.md"
                if paper_md.exists():
                    st.subheader("📄 Generated Markdown Report")
                    markdown_content = paper_md.read_text()
                    lines = markdown_content.split('\n')
                    for line in lines:
                        if line.startswith('![Architecture Diagram') or line.startswith('![Class Diagram') or line.startswith('![Component Flow Diagram'):
                            img_match = re.search(r'\((.*?)\)', line)
                            if img_match:
                                img_rel_path = img_match.group(1)
                                img_path = output_dir / img_rel_path
                                if img_path.exists():
                                    caption = line[line.find('[')+1:line.find(']')]
                                    st.image(str(img_path), caption=caption, width=400)
                                else:
                                    st.warning(f"Image {img_path} not found. Check if PNG was generated.")
                                    st.markdown(line)  # Hiển thị dòng Markdown nếu không có hình
                        else:
                            st.markdown(line)
                    
                pdf_file = output_dir / "paper.pdf"
                if pdf_file.exists():
                    with open(pdf_file, "rb") as f:
                        st.download_button("📄 Download PDF", f, file_name="report.pdf")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
