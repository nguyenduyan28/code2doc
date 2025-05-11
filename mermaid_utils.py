#!/usr/bin/env python3
"""
Mermaid Diagram Generation Utilities

This module replaces matplotlib-based diagram generation with OpenAI-powered Mermaid diagrams,
producing more accurate and detailed visualizations.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional
import openai
import base64
from io import BytesIO
import re
from PIL import Image
import math
import requests

def generate_mermaid_architecture_diagram(classes: Dict[str, Any], openai_client, gpt_version: str) -> str:
    """
    Generate a Mermaid architecture diagram using OpenAI.
    
    Args:
        classes: Dictionary of class information with methods and properties
        openai_client: OpenAI client instance
        gpt_version: GPT model version to use
        
    Returns:
        Mermaid diagram code
    """
    # Extract class information for the prompt
    class_info = []
    for class_name, info in classes.items():
        methods = [m.get("name", "") for m in info.get("methods", [])]
        attributes = [a.get("name", "") for a in info.get("attributes", [])]
        inherits = info.get("inherits_from", [])
        
        class_info.append({
            "name": class_name,
            "methods": methods[:5],  # Limit to 5 methods for clarity
            "attributes": attributes[:5],  # Limit to 5 attributes for clarity
            "inherits_from": inherits
        })
    
    # Create prompt for GPT
    prompt = f"""
    Generate a Mermaid class diagram that represents the architecture of a system with the following classes.
    For each class, I'll provide its name, key methods, attributes, and inheritance relationships.
    
    Class Information:
    {json.dumps(class_info, indent=2)}
    
    Please create a Mermaid class diagram using the classDiagram syntax. Include:
    1. All classes with their methods and attributes
    2. Inheritance relationships using <|-- notation
    3. Reasonable assumptions about relationships between classes based on naming patterns
    
    The diagram should be well-organized and easy to read. Use appropriate Mermaid syntax to represent the architecture clearly.
    Only return the Mermaid code without any explanation or additional text or any additional color.
    Begin your response with "```mermaid" and end with "```".
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=gpt_version,
            messages=[
                {"role": "system", "content": "You are an expert software architect who creates clear, accurate Mermaid diagrams."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.1
        )
        
        # Extract Mermaid code from response
        mermaid_code = response.choices[0].message.content.strip()
        
        # Clean up the code to ensure proper mermaid format
        mermaid_code = extract_mermaid_code(mermaid_code)
        
        return mermaid_code
        
    except Exception as e:
        print(f"Error generating architecture diagram: {e}")
        # Return fallback simple diagram
        return """classDiagram
            class MainClass {
                +process()
                +initialize()
            }
            class Helper {
                +support()
            }
            MainClass --> Helper"""

def generate_mermaid_class_diagram(classes: Dict[str, Any], dependencies: Dict[str, Any], 
                                   openai_client, gpt_version: str) -> str:
    """
    Generate a more detailed Mermaid class diagram using OpenAI.
    
    Args:
        classes: Dictionary of class information
        dependencies: Dictionary of dependency information
        openai_client: OpenAI client instance
        gpt_version: GPT model version to use
        
    Returns:
        Mermaid diagram code
    """
    # Extract relevant dependency information
    class_dependencies = []
    for name, dep_info in dependencies.items():
        if dep_info.get("type") == "class" and name in classes:
            depends_on = [dep for dep in dep_info.get("depends_on", []) if dep in classes]
            if depends_on:
                class_dependencies.append({
                    "class": name,
                    "depends_on": depends_on
                })
    
    # Create prompt for GPT
    prompt = f"""
    Generate a detailed Mermaid class diagram that shows both class structures and their relationships.
    
    Class Information:
    {json.dumps([{"name": name, "methods": [m.get("name") for m in info.get("methods", [])[:5]], 
                 "attributes": [a.get("name") for a in info.get("attributes", [])[:3]],
                 "inherits_from": info.get("inherits_from", [])} 
                for name, info in classes.items()], indent=2)}
    
    Dependencies:
    {json.dumps(class_dependencies, indent=2)}
    
    Please create a comprehensive Mermaid class diagram that shows:
    1. Classes with their key methods and attributes
    2. Inheritance relationships with <|-- notation
    3. Dependencies between classes with --> notation
    4. Use appropriate relationship types (aggregation, composition, etc.) when they can be inferred
    
    Make the diagram as clear and organized as possible. Group related classes together visually.
    Only return the Mermaid code without any explanation or additional text or any additional color.
    Begin your response with "```mermaid" and end with "```".
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=gpt_version,
            messages=[
                {"role": "system", "content": "You are an expert software architect who creates detailed, accurate Mermaid class diagrams."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.1            
        )
        
        # Extract Mermaid code from response
        mermaid_code = response.choices[0].message.content.strip()
        mermaid_code = extract_mermaid_code(mermaid_code)
        
        return mermaid_code
        
    except Exception as e:
        print(f"Error generating class diagram: {e}")
        # Return fallback simple diagram
        return """classDiagram
            class Class1 {
                +method1()
                +method2()
            }
            class Class2 {
                +method1()
            }
            Class1 --> Class2"""

def generate_mermaid_component_flow_diagram(data_flow: Dict[str, Any], 
                                           openai_client, gpt_version: str) -> str:
    """
    Generate a Mermaid component flow diagram using OpenAI.
    
    Args:
        data_flow: Dictionary of data flow information
        openai_client: OpenAI client instance
        gpt_version: GPT model version to use
        
    Returns:
        Mermaid diagram code
    """
    # Extract data paths
    data_paths = data_flow.get("data_paths", [])
    
    prompt = f"""
    Generate a Mermaid flowchart diagram that shows the flow of data between components.
    
    Data Flow Paths:
    {json.dumps(data_paths, indent=2)}
    
    Please create a Mermaid flowchart diagram that:
    1. Shows each component as a node with a unique ID (use camelCase for node IDs, e.g., inputData, processData).
    2. Shows data flow between components with directional arrows (`-->`) from source to destination.
    3. Labels the arrows with data types (e.g., `|int|` or `|string|`) if available in the data; if not, leave the arrow unlabeled.
    4. Uses appropriate Mermaid node shapes to represent different types of components:
       - Use `()` for input/output components (e.g., `(inputData)`).
       - Use `[]` for processing components (e.g., `[processData]`).
       - Use `{{}}` for storage/database components (e.g., `{{storage}}`).
    5. Organizes the flow logically from inputs (left) to outputs (right).
    6. If a component name contains spaces, wrap it in double quotes (e.g., `["Input Data"]` or `("Input Data")`).
    
    The diagram should clearly illustrate the processing pipeline and component interactions.
    Only return the Mermaid code without any explanation or additional text or any additional color.
    Begin your response with "```mermaid" and end with "```".
    Use the following Mermaid flowchart syntax:
    - Start with: `flowchart LR`
    - Define nodes with shapes: e.g., `nodeId[Node Name]` or `nodeId("Node Name")`
    - Define flows: e.g., `nodeId1 --> |dataType| nodeId2`
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=gpt_version,
            messages=[
                {"role": "system", "content": "You are an expert software architect who creates clear, accurate Mermaid flowchart diagrams."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.1
        )
        
        # Extract Mermaid code from response
        mermaid_code = response.choices[0].message.content.strip()
        mermaid_code = extract_mermaid_code(mermaid_code)
        
        return mermaid_code
        
    except Exception as e:
        print(f"Error generating component flow diagram: {e}")
        # Return fallback simple diagram
        return """flowchart TD
            A[Input] --> B[Process]
            B --> C[Output]"""

def extract_mermaid_code(text: str) -> str:
    """
    Extract Mermaid code from text that might contain markdown formatting.
    
    Args:
        text: Text that might contain Mermaid code in markdown format
        
    Returns:
        Clean Mermaid code
    """
    # Look for mermaid code block
    mermaid_pattern = r"```mermaid\s*([\s\S]*?)\s*```"
    match = re.search(mermaid_pattern, text)
    
    if match:
        # Return just the mermaid code without the backticks
        mermaid_code = match.group(1).strip()
        return mermaid_code
    else:
        # If no proper code block is found, try to extract anything that looks like mermaid code
        if "classDiagram" in text or "flowchart" in text:
            # Remove any markdown formatting and extract what looks like diagram code
            lines = text.split('\n')
            mermaid_lines = []
            in_diagram = False
            
            for line in lines:
                if "classDiagram" in line or "flowchart" in line:
                    in_diagram = True
                    mermaid_lines.append(line)
                elif in_diagram and line.strip() and not line.startswith("```"):
                    mermaid_lines.append(line)
                elif in_diagram and line.startswith("```"):
                    in_diagram = False
            
            return "\n".join(mermaid_lines)
        else:
            # Return the whole text as a fallback, cleaning any markdown formatting
            return text.replace("```mermaid", "").replace("```", "").strip()

# def render_mermaid_to_png(mermaid_code: str, output_file: str) -> bool:
#     """
#     Render Mermaid diagram to PNG using the Mermaid CLI (if installed) or Mermaid.ink API.
    
#     Args:
#         mermaid_code: Mermaid diagram code
#         output_file: Path to save the PNG file
        
#     Returns:
#         Boolean indicating success
#     """
#     # First attempt: Try using mermaid-cli if installed
#     try:
#         with tempfile.NamedTemporaryFile(suffix='.mmd', mode='w', delete=False) as temp_file:
#             temp_file.write(mermaid_code)
#             temp_file_path = temp_file.name
        
#         # Try to use mmdc (Mermaid CLI) command if installed
#         result = subprocess.run(
#             ['mmdc', '-i', temp_file_path, '-o', output_file, '-b', 'transparent'],
#             capture_output=True,
#             text=True,
#             check=False
#         )
        
#         os.unlink(temp_file_path)
        
#         if result.returncode == 0:
#             print(f"Successfully generated PNG using Mermaid CLI: {output_file}")
#             return True
            
#     except (subprocess.SubprocessError, FileNotFoundError) as e:
#         print(f"Mermaid CLI not available or failed: {e}")
        
#     # Second attempt: Try using the Mermaid.ink online service
#     try:
#         # Base64 encode the Mermaid code for the URL
#         encoded_mermaid = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
#         mermaid_url = f"https://mermaid.ink/img/{encoded_mermaid}"
        
#         # Request the image
#         response = requests.get(mermaid_url, timeout=15)
#         if response.status_code == 200:
#             # Save the image
#             with open(output_file, 'wb') as f:
#                 f.write(response.content)
#             print(f"Successfully generated PNG using Mermaid.ink: {output_file}")
#             return True
#         else:
#             print(f"Mermaid.ink API request failed: {response.status_code}")
#     except Exception as e:
#         print(f"Failed to use Mermaid.ink API: {e}")
    
#     # Third attempt: Try using puppeteer-mermaid if available
#     try:
#         with tempfile.NamedTemporaryFile(suffix='.mmd', mode='w', delete=False) as temp_file:
#             temp_file.write(mermaid_code)
#             temp_file_path = temp_file.name
        
#         # Try puppeteer-mermaid if installed
#         result = subprocess.run(
#             ['puppeteer-mermaid', '-i', temp_file_path, '-o', output_file],
#             capture_output=True,
#             text=True,
#             check=False
#         )
        
#         os.unlink(temp_file_path)
        
#         if result.returncode == 0:
#             print(f"Successfully generated PNG using puppeteer-mermaid: {output_file}")
#             return True
#     except (subprocess.SubprocessError, FileNotFoundError) as e:
#         print(f"puppeteer-mermaid not available or failed: {e}")
    
#     # Create a fallback empty image with text if everything else fails
#     try:
#         from PIL import Image, ImageDraw, ImageFont
        
#         # Create a blank image with text saying "Mermaid rendering failed"
#         img = Image.new('RGB', (800, 600), color=(255, 255, 255))
#         d = ImageDraw.Draw(img)
        
#         # Try to get a font, use default if not available
#         try:
#             font = ImageFont.truetype("arial.ttf", 20)
#         except:
#             font = ImageFont.load_default()
        
#         # Add text with diagram code
#         d.text((10, 10), "Mermaid rendering failed. Diagram code:", fill=(0, 0, 0), font=font)
        
#         # Add the mermaid code
#         wrapped_text = "\n".join([mermaid_code[i:i+80] for i in range(0, len(mermaid_code), 80)])
#         d.text((10, 50), wrapped_text, fill=(0, 0, 0), font=font)
        
#         # Save the image
#         img.save(output_file)
#         print(f"Created fallback image with code: {output_file}")
#         return True
#     except Exception as e:
#         print(f"Failed to create fallback image: {e}")
#         return False

import shutil

import subprocess
import shutil
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont

def render_mermaid_to_png(mermaid_code: str, output_file: str) -> bool:
    """
    Render Mermaid diagram to PNG using Mermaid CLI or Puppeteer (local rendering).
    
    Args:
        mermaid_code: Mermaid diagram code
        output_file: Path to save the PNG file
        
    Returns:
        Boolean indicating success
    """
    # First attempt: Try using Mermaid CLI (mmdc) if installed
    if shutil.which('mmdc'):
        try:
            with tempfile.NamedTemporaryFile(suffix='.mmd', mode='w', delete=False) as temp_file:
                temp_file.write(mermaid_code)
                temp_file_path = temp_file.name
            
            print(f"Attempting to render PNG with Mermaid CLI: {output_file}")
            result = subprocess.run(
                ['mmdc', '-i', temp_file_path, '-o', output_file, '-b', 'transparent', '--scale', '2'],
                capture_output=True,
                text=True,
                check=False
            )
            
            os.unlink(temp_file_path)
            
            if result.returncode == 0 and os.path.exists(output_file):
                print(f"Successfully generated PNG using Mermaid CLI: {output_file}")
                return True
            else:
                print(f"Mermaid CLI failed: {result.stderr}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Mermaid CLI rendering failed: {e}")
    
    # Second attempt: Use Puppeteer to render locally via a Node.js script
    try:
        print(f"Attempting to render PNG with Puppeteer: {output_file}")
        # Create a temporary Node.js script to render Mermaid using Puppeteer
        node_script = """
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });
    await page.goto('https://mermaid-js.github.io/mermaid-live-editor');
    
    // Inject Mermaid code
    const mermaidCode = `%s`;
    await page.evaluate((code) => {
        document.querySelector('#code').value = code;
        document.querySelector('#code').dispatchEvent(new Event('input'));
    }, mermaidCode);
    
    // Wait for rendering
    await page.waitForTimeout(2000);
    
    // Take screenshot
    const diagram = await page.$('#container svg');
    await diagram.screenshot({ path: '%s', type: 'png', omitBackground: true });
    
    await browser.close();
})();
"""
        # Replace placeholders with actual values
        node_script = node_script % (mermaid_code.replace('\n', '\\n'), output_file)
        
        # Save the Node.js script to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as temp_script:
            temp_script.write(node_script)
            temp_script_path = temp_script.name
        
        # Run the Node.js script
        result = subprocess.run(
            ['node', temp_script_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        os.unlink(temp_script_path)
        
        if result.returncode == 0 and os.path.exists(output_file):
            print(f"Successfully generated PNG using Puppeteer: {output_file}")
            return True
        else:
            print(f"Puppeteer rendering failed: {result.stderr}")
    except Exception as e:
        print(f"Failed to render with Puppeteer: {e}")
    
    # Final fallback: Create a simple image with the Mermaid code
    try:
        print(f"Creating fallback image for: {output_file}")
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        d.text((10, 10), "Mermaid rendering failed. Diagram code:", fill=(0, 0, 0), font=font)
        wrapped_text = "\n".join([mermaid_code[i:i+80] for i in range(0, len(mermaid_code), 80)])
        d.text((10, 50), wrapped_text, fill=(0, 0, 0), font=font)
        
        img.save(output_file)
        print(f"Created fallback image with code: {output_file}")
        return True
    except Exception as e:
        print(f"Failed to create fallback image: {e}")
        return False
def render_mermaid_to_svg(mermaid_code: str, output_file: str) -> bool:
    """Render Mermaid diagram to SVG using Mermaid CLI or Mermaid.ink API."""
    if shutil.which('mmdc'):
        try:
            with tempfile.NamedTemporaryFile(suffix='.mmd', mode='w', delete=False) as temp_file:
                temp_file.write(mermaid_code)
                temp_file_path = temp_file.name
            
            result = subprocess.run(
                ['mmdc', '-i', temp_file_path, '-o', output_file, '-e', 'svg', '-b', 'transparent'],
                capture_output=True,
                text=True,
                check=False
            )
            
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                print(f"Successfully generated SVG using Mermaid CLI: {output_file}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Mermaid CLI failed for SVG: {e}")
    
    try:
        encoded_mermaid = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        mermaid_url = f"https://mermaid.ink/svg/{encoded_mermaid}"
        response = requests.get(mermaid_url, timeout=15)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"Successfully generated SVG using Mermaid.ink: {output_file}")
            return True
        else:
            print(f"Mermaid.ink API request failed: {response.status_code}")
    except Exception as e:
        print(f"Failed to use Mermaid.ink API for SVG: {e}")
    
    print(f"Failed to render SVG: {output_file}")
    return False
def generate_architecture_diagram(classes: Dict[str, Any], output_file: str, 
                                 openai_client=None, gpt_version: str = "gpt-3.5-turbo") -> None:
    """Generate an architecture diagram and save it as PNG."""
    mermaid_code = generate_mermaid_architecture_diagram(classes, openai_client, gpt_version)
    
    mmd_file = output_file.replace('.png', '.mmd')
    with open(mmd_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_code)
    
    print(f"Architecture diagram mermaid code saved to {mmd_file}")
    print(f"Attempting to render PNG to {output_file}")
    
    if render_mermaid_to_png(mermaid_code, output_file):
        print(f"Architecture diagram saved as PNG: {output_file}")
    else:
        print(f"Failed to render architecture diagram as PNG: {output_file}")

def generate_class_diagram(classes: Dict[str, Any], dependencies: Dict[str, Any],
                          output_file: str, openai_client=None, 
                          gpt_version: str = "gpt-3.5-turbo") -> None:
    """Generate a class diagram and save it as PNG."""
    mermaid_code = generate_mermaid_class_diagram(classes, dependencies, openai_client, gpt_version)
    
    mmd_file = output_file.replace('.png', '.mmd')
    with open(mmd_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_code)
    
    print(f"Class diagram mermaid code saved to {mmd_file}")
    print(f"Attempting to render PNG to {output_file}")
    
    if render_mermaid_to_png(mermaid_code, output_file):
        print(f"Class diagram saved as PNG: {output_file}")
    else:
        print(f"Failed to render class diagram as PNG: {output_file}")

def generate_component_flow_diagram(data_flow: Dict[str, Any], output_file: str,
                                   openai_client=None, gpt_version: str = "gpt-3.5-turbo") -> None:
    """Generate a component flow diagram and save it as PNG."""
    mermaid_code = generate_mermaid_component_flow_diagram(data_flow, openai_client, gpt_version)
    
    mmd_file = output_file.replace('.png', '.mmd')
    with open(mmd_file, 'w', encoding='utf-8') as f:
        f.write(mermaid_code)
    
    print(f"Component flow diagram mermaid code saved to {mmd_file}")
    print(f"Attempting to render PNG to {output_file}")
    
    if render_mermaid_to_png(mermaid_code, output_file):
        print(f"Component flow diagram saved as PNG: {output_file}")
    else:
        print(f"Failed to render component flow diagram as PNG: {output_file}")