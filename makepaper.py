#!/usr/bin/env python3
"""
Paper Generation Module for Paper with Mermaid Diagrams

This script creates a complete research paper document based on code analysis results,
generating text content, Mermaid diagrams, and formatting the final document.
"""
#(Phai dang nhap huggingface moi xai duoc) huggingface-cli login
#pip install guardrails-ai
#guardrails configure
#N + Y
#API key cua guardrails: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfDEwODIyMTg5NDY4MDg1OTc4MDM2MSIsImFwaUtleUlkIjoiN2M2OGI4ZTQtMmNjZi00MWVkLWJhYzAtNjAwODliYjc3ZGE0Iiwic2NvcGUiOiJyZWFkOnBhY2thZ2VzIiwicGVybWlzc2lvbnMiOltdLCJpYXQiOjE3NDY2MTU0OTksImV4cCI6NDkwMDIxNTQ5OX0.p_XQ7JAMC9qRhYKG0bXsgtBSN0d3sXyD6HZmUWPrdR0
#guardrails hub install hub://guardrails/toxic_language
#guardrails hub install hub://guardrails/profanity_free
#guardrails hub install hub://guardrails/gibberish_text
#guardrails hub install hub://guardrails/detect_pii
#guardrails hub install hub://tryolabs/restricttotopic

import argparse
import json
import subprocess
import os
import math
import re
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import networkx as nx
import openai
import asyncio
import nest_asyncio
nest_asyncio.apply()
from utils import (
    load_json, save_json, create_directory,
    format_markdown, generate_tex_preamble, generate_tex_closing,
    extract_metrics_summary, extract_complexity_summary
)
from mermaid_utils import (
    generate_architecture_diagram, generate_class_diagram, generate_component_flow_diagram
)

from guardrails import Guard
from guardrails.hub import (
    ToxicLanguage,
    ProfanityFree,
    GibberishText,
    DetectPII,
    RestrictToTopic 
)
import os
api_key = os.getenv("OPENAI_API_KEY")

class PaperGenerator:
    """Generates a complete research paper from code analysis."""
    
    def __init__(self, output_dir: str, paper_plan: Dict, analysis_result: Dict, gpt_version: str = "gpt-3.5-turbo"):
        self.output_dir = output_dir
        self.figures_dir = os.path.join(output_dir, "figures")
        create_directory(self.figures_dir)
        
        self.paper_plan = paper_plan
        self.analysis_result = analysis_result
        self.gpt_version = gpt_version
        self.openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        paper_name = self.paper_plan.get("paper_name", "Unknown Paper")
        self.safety_guard = Guard().use_many(
            ToxicLanguage(validation_method="full", on_fail="exception", threshold=0.5),
            ProfanityFree(validation_method="full", on_fail="exception", threshold=0.5),
            #GibberishText(validation_method="full", on_fail="exception", threshold=0.5),
            DetectPII(["EMAIL_ADDRESS", "PHONE_NUMBER"], "exception"),
            RestrictToTopic(valid_topics=[paper_name], disable_classifier=True, disable_llm=False, on_fail="exception")
        )
    def generate_valid_text(self, generate_func, outline, max_retries=5):
        """Check generated text validity with truncation for long outputs."""
        for attempt in range(max_retries):
            text = generate_func(outline)
            if len(text.split()) > 400:
                text = " ".join(text.split()[:400])
                print(f"Truncated text to 400 words on attempt {attempt+1}")
            try:
                self.safety_guard.validate(text)
                return text
            except Exception as e:
                print(f"Failed on attempt {attempt+1}: {e}")
                if attempt == max_retries - 1:
                    print("Max retries reached, returning unvalidated text")
                    return text
        print("Failed to generate valid text after max retries, returning last attempt")
        return text
    def generate_figures(self) -> Dict[str, str]:
        """Generate all figures for the paper as PNG using Mermaid diagrams."""
        figure_paths = {}
        
        architecture_path = os.path.join(self.figures_dir, "architecture_diagram")
        print(f"Generating architecture diagram at: {architecture_path}.png")
        generate_architecture_diagram(
            self.analysis_result["complexity"]["classes"],
            architecture_path + ".png",
            self.openai_client,
            self.gpt_version
        )
        figure_paths["architecture"] = architecture_path + ".mmd"
        
        class_diagram_path = os.path.join(self.figures_dir, "class_diagram")
        print(f"Generating class diagram at: {class_diagram_path}.png")
        generate_class_diagram(
            self.analysis_result["complexity"]["classes"],
            self.analysis_result["dependencies"],
            class_diagram_path + ".png",
            self.openai_client,
            self.gpt_version
        )
        figure_paths["class_diagram"] = class_diagram_path + ".mmd"
        
        component_flow_path = os.path.join(self.figures_dir, "component_flow")
        print(f"Generating component flow diagram at: {component_flow_path}.png")
        generate_component_flow_diagram(
            self.analysis_result["data_flow"],
            component_flow_path + ".png",
            self.openai_client,
            self.gpt_version
        )
        figure_paths["component_flow"] = component_flow_path + ".mmd"
        
        return figure_paths
    
    def generate_abstract(self, outline_section: Dict = None) -> str:
        """
        Generate paper abstract using GPT, incorporating outline key points.
        """
        metrics = extract_metrics_summary(self.analysis_result["metrics"])
        complexity = extract_complexity_summary(self.analysis_result["complexity"])
        paper_name = self.paper_plan["paper_name"]
        
        # Add key points from outline if available
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points in the abstract:\n{key_points}"
        
        prompt = f"""
        Write an abstract for a research paper analyzing the implementation of {paper_name}.
        The code has the following characteristics:
        
        {metrics}
        {complexity}
        
        IMPORTANT: Avoid **bias**
        
        The paper analyzes the architecture, implementation details, and code quality.{key_points}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an expert AI researcher who writes clear, concise academic abstracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=512
            )
            
            abstract = response.choices[0].message.content.strip()
            return abstract
            
        except Exception as e:
            print(f"Error generating abstract: {e}")
            return "Abstract generation failed. Please check your code analysis results and try again."
    
    def generate_introduction(self, outline_section: Dict = None) -> str:
        """
        Generate introduction section using GPT.
        """
        paper_name = self.paper_plan["paper_name"]
        
        # Add key points from outline if available
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points in the abstract:\n{key_points}"

        prompt = f"""
        Write an introduction section for a research paper analyzing the implementation of {paper_name}.
        
        Include:
        1. Background and importance of {paper_name}
        2. Motivation for analyzing this particular implementation
        3. Overview of the paper structure
        4. Main contributions
        
        Keep it academic, concise, and focused on code analysis rather than the model's performance.{key_points}
        
        IMPORTANT: Do not use any markdown formatting like **bold** or *italic* in your response as this will be directly inserted into a LaTeX document. Do not write conclusion and title here. Avoid **bias**
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an expert AI researcher who writes clear, academic papers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=512
            )
            
            introduction = response.choices[0].message.content.strip()
            return introduction
            
        except Exception as e:
            print(f"Error generating introduction: {e}")
            return "Introduction generation failed. Please check your code analysis results and try again."
    
    def generate_related_work_section(self, outline_section: Dict = None) -> str:
        """
        Generate related work section using GPT with optimized prompt.
        """
        paper_name = self.paper_plan["paper_name"]
        
        # Giới hạn số classes và info để tránh prompt quá dài
        classes = list(self.analysis_result["complexity"]["classes"].keys())[:5]  # Chỉ lấy 5 classes đầu
        neural_network_info = self.analysis_result["algorithms"]["neural_network"]
        attention_info = self.analysis_result["algorithms"]["attention_mechanism"]

        # Add key points từ outline nếu có
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points:\n{key_points}"

        # Prompt ngắn gọn hơn
        prompt = f"""
        Write a related work section for a research paper analyzing {paper_name}.
        Focus on:
        - Previous works influencing this implementation
        - Key classes: {classes}
        - Neural network: {neural_network_info if any(neural_network_info.values()) else 'None'}
        - Attention: {attention_info if any(attention_info.values()) else 'None'}
        {key_points}
        Be concise, scholarly, and avoid markdown formatting.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an AI researcher writing concise literature reviews."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400  # Giảm max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating related work section: {e}")
            return "Related work section generation failed."
    def generate_architecture_section(self, outline_section: Dict = None) -> str:
        """Generate architecture section using GPT."""
        paper_name = self.paper_plan.get("paper_name", "Unknown Paper")
        classes = list(self.analysis_result["complexity"]["classes"].keys())[:5]
        data_flow = self.analysis_result["data_flow"]
        
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points:\n{key_points}"

        prompt = f"""
        Write an architecture section for a research paper analyzing the implementation of {paper_name}.
        Focus on:
        - Key classes: {classes}
        - Data flow: {data_flow}
        - Overall system architecture
        Be concise, scholarly, and avoid markdown formatting.
        {key_points}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an AI researcher writing clear architecture descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating architecture section: {e}")
            return "Architecture section generation failed."
# Sửa các hàm generate khác tương tự
    def generate_abstract(self, outline_section: Dict = None) -> str:
        # Tương tự, giảm max_tokens và tối ưu prompt
        metrics = extract_metrics_summary(self.analysis_result["metrics"])
        complexity = extract_complexity_summary(self.analysis_result["complexity"])
        paper_name = self.paper_plan["paper_name"]
        
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points:\n{key_points}"

        prompt = f"""
        Write a concise abstract for a research paper analyzing {paper_name}.
        Code characteristics:
        {metrics}
        {complexity}
        {key_points}
        Avoid bias and markdown formatting.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an AI researcher writing clear abstracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400  # Giảm max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating abstract: {e}")
            return "Abstract generation failed."
        
    def generate_code_quality_section(self, outline_section: Dict = None) -> str:
        """
        Generate code quality analysis section using GPT.
        """
        code_quality = self.analysis_result["code_quality"]
        paper_name = self.paper_plan["paper_name"]
        
        # Format the quality metrics
        quality_metrics = "\n".join([
            f"- Docstring coverage: {code_quality.get('docstring_coverage', 0):.2f}",
            f"- Naming consistency: {code_quality.get('naming_consistency', 0):.2f}",
            f"- Average function length: {code_quality.get('average_function_length', 0):.1f} lines",
            f"- Complexity ratio: {code_quality.get('complexity_ratio', 0):.1f}",
            f"- Overall quality score: {code_quality.get('overall_quality', 0):.2f}"
        ])
        
        # Add key points from outline if available
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points in the abstract:\n{key_points}"

        prompt = f"""
        Write a code quality analysis section for a research paper evaluating implementation of {paper_name}.
        The code quality metrics are:
        
        {quality_metrics}
        
        The dominant naming convention is {code_quality.get('dominant_naming_convention', 'unknown')}.
        
        Focus on:
        1. Code readability and maintainability
        2. Documentation quality
        3. Adherence to Python best practices
        4. Areas for potential improvement
        {key_points}
        Be analytical and provide concrete suggestions for improvement.
        
        IMPORTANT: Do not use any markdown formatting like **bold** or *italic* in your response as this will be directly inserted into a LaTeX document. Do not write conclusion or title for this part. Avoid **bias**
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer who specializes in code quality analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=512
            )
            
            code_quality_section = response.choices[0].message.content.strip()
            return code_quality_section
            
        except Exception as e:
            print(f"Error generating code quality section: {e}")
            return "Code quality section generation failed. Please check your code analysis results and try again."
    
    def generate_conclusion(self, outline_section: Dict = None) -> str:
        """
        Generate conclusion section using GPT.
        """
        # Extract key metrics for the conclusion
        metrics = self.analysis_result["metrics"]
        code_quality = self.analysis_result["code_quality"]
        paper_name = self.paper_plan["paper_name"]
        
        # Add key points from outline if available
        key_points = ""
        if outline_section and "key_points" in outline_section:
            key_points = "\n".join([f"- {point}" for point in outline_section["key_points"]])
            key_points = f"\nIncorporate these key points in the abstract:\n{key_points}"

        prompt = f"""
        Write a conclusion section for a research paper analyzing the implementation of {paper_name}.
        
        The codebase has:
        - {metrics.get('class_count', 0)} classes
        - {metrics.get('function_count', 0)} functions
        - Overall quality score of {code_quality.get('overall_quality', 0):.2f}/1.0
        
        Include:
        1. Summary of key findings from the architecture and code quality analysis
        2. Strengths and weaknesses of the implementation
        3. Recommendations for improvement
        4. Final thoughts on the implementation's suitability for production or research
        {key_points}
        Keep it concise, balanced, and provide meaningful insights.
        
        IMPORTANT: Do not use any markdown formatting like **bold** or *italic* in your response as this will be directly inserted into a LaTeX document. Avoid **bias**
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_version,
                messages=[
                    {"role": "system", "content": "You are an expert AI researcher who writes impactful paper conclusions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=512
            )
            
            conclusion = response.choices[0].message.content.strip()
            return conclusion
            
        except Exception as e:
            print(f"Error generating conclusion: {e}")
            return "Conclusion generation failed. Please check your code analysis results and try again."
    
    def generate_paper(self) -> Dict[str, str]:
        """Generate the complete paper with all sections."""
        paper_name = self.paper_plan.get("paper_name", "Unknown Paper")
        outline = self.paper_plan.get("outline", {})
        
        print("Generating diagrams...")
        figure_paths = self.generate_figures()
        
        print("Generating abstract...")
        abstract_outline = outline.get("section_1", {})
        abstract = self.generate_valid_text(self.generate_abstract, abstract_outline)
        
        print("Generating introduction...")
        intro_outline = outline.get("section_2", {})
        introduction = self.generate_valid_text(self.generate_introduction, intro_outline)

        print("Generating related work section...")
        related_outline = outline.get("section_3", {})
        related_work_section = self.generate_valid_text(self.generate_related_work_section, related_outline)

        print("Generating architecture section...")
        arch_outline = outline.get("section_4", {})
        architecture_section = self.generate_valid_text(self.generate_architecture_section, arch_outline)

        print("Generating code quality section...")
        quality_outline = outline.get("section_5", {})
        code_quality_section = self.generate_valid_text(self.generate_code_quality_section, quality_outline)

        print("Generating conclusion...")
        conclusion_outline = outline.get("section_6", {})
        conclusion = self.generate_valid_text(self.generate_conclusion, conclusion_outline)
        
        paper = {
            "title": f"Analysis of {paper_name} Implementation",
            "abstract": abstract,
            "introduction": introduction,
            "related_work": related_work_section,
            "architecture": architecture_section,
            "code_quality": code_quality_section,
            "conclusion": conclusion,
            "figures": figure_paths
        }
        
        return paper
    
    def save_paper_markdown(self, paper: Dict[str, str]) -> str:
        """Save the paper in Markdown format with embedded PNG images, matching SAD structure."""
        markdown_path = os.path.join(self.output_dir, "paper.md")
        
        architecture_png = os.path.join("figures", "architecture_diagram.png")
        class_diagram_png = os.path.join("figures", "class_diagram.png")
        component_flow_png = os.path.join("figures", "component_flow.png")
        
        architecture_png = architecture_png if os.path.exists(os.path.join(self.output_dir, architecture_png)) else "figures/placeholder.png"
        class_diagram_png = class_diagram_png if os.path.exists(os.path.join(self.output_dir, class_diagram_png)) else "figures/placeholder.png"
        component_flow_png = component_flow_png if os.path.exists(os.path.join(self.output_dir, component_flow_png)) else "figures/placeholder.png"
        
        paper_name = self.paper_plan.get("paper_name", "Unknown Paper")
        title = paper.get('title', 'Analysis of Transformer Implementation')
        
        markdown_content = f"""# {title}

## Abstract

{paper['abstract']}

## 1. Introduction

{paper['introduction']}

## 2. Related Work
{paper['related_work']}

## 3. Architecture and Implementation

{paper['architecture']}

### 3.1 Architecture Diagram
![Architecture Diagram]({architecture_png})

*Figure 1: Architecture diagram of the {paper_name} implementation*

### 3.2 Class Diagram
![Class Diagram]({class_diagram_png})

*Figure 2: Class diagram showing relationships between components*

### 3.3 Component Flow Diagram
![Component Flow Diagram]({component_flow_png})

*Figure 3: Component flow diagram illustrating data processing pipeline*

## 4. Code Quality Analysis
{paper['code_quality']}

## 5. Conclusion
{paper['conclusion']}
"""
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Paper saved as markdown at {markdown_path}")
        return markdown_path
    def clean_markdown_for_latex(self, text: str) -> str:
        """Cleans markdown formatting and converts to LaTeX formatting."""
        text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)
        text = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', text)
        text = re.sub(r'^#\s+(.+)$', r'\\section{\1}', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'\\subsection{\1}', text, flags=re.MULTILINE)
        text = re.sub(r'^###\s+(.+)$', r'\\subsubsection{\1}', text, flags=re.MULTILINE)
        text = re.sub(r'^-\s+(.+)$', r'\\item \1', text, flags=re.MULTILINE)
        text = text.replace('%', r'\%').replace('&', r'\&').replace('#', r'\#').replace('_', r'\_')
        return text
    def save_paper_tex(self, paper: Dict[str, str]) -> str:
        """Save the paper in LaTeX format with embedded PNG images."""
        tex_path = os.path.join(self.output_dir, "paper.tex")
        
        clean_introduction = self.clean_markdown_for_latex(paper['introduction'])
        clean_related_work = self.clean_markdown_for_latex(paper['related_work'])
        clean_architecture = self.clean_markdown_for_latex(paper['architecture'])
        clean_code_quality = self.clean_markdown_for_latex(paper['code_quality'])
        clean_conclusion = self.clean_markdown_for_latex(paper['conclusion'])
        clean_abstract = self.clean_markdown_for_latex(paper['abstract'])
        
        title = paper.get('title', 'Analysis of Transformer Implementation')
        if not title:
            title = 'Analysis of Transformer Implementation'
        
        tex_content = generate_tex_preamble(title)
        paper_name = self.paper_plan.get("paper_name", "Unknown Paper")
        tex_content += f"""
\\begin{{abstract}}
{clean_abstract}
\\end{{abstract}}

\\section{{Introduction}}
{clean_introduction}

\\section{{Related Work}}
{clean_related_work}

\\section{{Architecture and Implementation}}
{clean_architecture}

\\subsection{{Architecture Diagram}}
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.9\\textwidth,keepaspectratio]{{figures/architecture_diagram.png}}
\\caption{{Architecture diagram of the {paper_name} implementation}}
\\label{{fig:architecture}}
\\end{{figure}}

\\subsection{{Class Diagram}}
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.9\\textwidth,keepaspectratio]{{figures/class_diagram.png}}
\\caption{{Class diagram showing relationships between components}}
\\label{{fig:class_diagram}}
\\end{{figure}}

\\subsection{{Component Flow Diagram}}
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.9\\textwidth,keepaspectratio]{{figures/component_flow.png}}
\\caption{{Component flow diagram illustrating data processing pipeline}}
\\label{{fig:component_flow}}
\\end{{figure}}

\\section{{Code Quality Analysis}}
{clean_code_quality}

\\section{{Conclusion}}
{clean_conclusion}

{generate_tex_closing()}
"""
        
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        print(f"Paper saved as LaTeX at {tex_path}")
        return tex_path
    def save_paper_pdf(self, tex_path: str) -> str:
        """Convert LaTeX to PDF using pdflatex with PNG support."""
        pdf_path = os.path.join(self.output_dir, "paper.pdf")
        try:
            original_dir = os.getcwd()
            os.chdir(self.output_dir)
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', os.path.basename(tex_path)],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                print(f"pdflatex first run failed: {result.stderr}")
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', os.path.basename(tex_path)],
                capture_output=True,
                text=True,
                check=False
            )
            os.chdir(original_dir)
            if os.path.exists(pdf_path):
                print(f"Paper saved as PDF at {pdf_path}")
                return pdf_path
            else:
                print(f"PDF generation failed: Output file not found. Check {os.path.join(self.output_dir, 'paper.log')}")
                return None
        except Exception as e:
            print(f"Error generating PDF: {e}")
            print("PDF generation failed. Please compile the LaTeX file manually with 'pdflatex paper.tex'")
            return None
def main():
    parser = argparse.ArgumentParser(description="Generate a research paper from code analysis results.")
    parser.add_argument("--output_dir", required=True, help="Directory with analysis results and for output")
    parser.add_argument("--gpt_version", default="gpt-3.5-turbo", help="GPT model version to use")
    args = parser.parse_args()
    
    paper_plan_path = os.path.join(args.output_dir, "paper_plan.json")
    analysis_result_path = os.path.join(args.output_dir, "analysis_result.json")
    
    try:
        paper_plan = load_json(paper_plan_path)
    except FileNotFoundError:
        print(f"Error: paper_plan.json not found in {args.output_dir}")
        paper_plan = {"paper_name": "Unknown Paper", "outline": {}}
    
    try:
        analysis_result = load_json(analysis_result_path)
    except FileNotFoundError:
        print(f"Error: analysis_result.json not found in {args.output_dir}")
        analysis_result = {
            "metrics": {}, "complexity": {"classes": {}}, "algorithms": {"neural_network": {}, "attention_mechanism": {}},
            "code_quality": {}, "data_flow": {}, "dependencies": {}
        }
    
    generator = PaperGenerator(
        output_dir=args.output_dir,
        paper_plan=paper_plan,
        analysis_result=analysis_result,
        gpt_version=args.gpt_version
    )
    
    paper = generator.generate_paper()
    markdown_path = generator.save_paper_markdown(paper)
    tex_path = generator.save_paper_tex(paper)
    generator.save_paper_pdf(tex_path)
    
    print("Paper generation completed successfully!")

if __name__ == "__main__":
    main()