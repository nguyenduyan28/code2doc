import os
import json
from code_process import preprocess_code
from planning import PaperPlanner
from analyzing import CodeAnalyzer
from makepaper import PaperGenerator

class CodeToDocPipeline:
    def __init__(self, input_file: str, output_dir: str, paper_name: str, gpt_version: str = "gpt-3.5-turbo"):
        self.input_file = input_file
        self.output_dir = output_dir
        self.cleaned_file = os.path.join(output_dir, f"{paper_name}_cleaned.py")
        self.analysis_file = os.path.join(output_dir, "analysis_result.json")
        self.paper_name = paper_name
        self.gpt_version = gpt_version

        os.makedirs(self.output_dir, exist_ok=True)

    def preprocess(self):
        print("[*] Preprocessing code...")
        preprocess_code(self.input_file, self.cleaned_file)

    def plan(self):
        print("[*] Planning paper structure...")
        planner = PaperPlanner(self.paper_name, self.gpt_version)
        planner.plan_paper(self.cleaned_file, self.output_dir)

    def analyze(self):
        print("[*] Analyzing code quality & complexity...")
        analyzer = CodeAnalyzer()
        results = analyzer.analyze_file(self.cleaned_file)

        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

    def generate_paper(self):
        print("[*] Generating paper...")
        # Load paper_plan and analysis_result from files
        paper_plan_path = os.path.join(self.output_dir, "paper_plan.json")
        analysis_result_path = os.path.join(self.output_dir, "analysis_result.json")
        
        try:
            with open(paper_plan_path, 'r', encoding='utf-8') as f:
                paper_plan = json.load(f)
        except FileNotFoundError:
            print(f"Error: paper_plan.json not found in {self.output_dir}")
            paper_plan = {"paper_name": self.paper_name, "outline": {}}
        
        try:
            with open(analysis_result_path, 'r', encoding='utf-8') as f:
                analysis_result = json.load(f)
        except FileNotFoundError:
            print(f"Error: analysis_result.json not found in {self.output_dir}")
            analysis_result = {
                "metrics": {}, "complexity": {"classes": {}},
                "algorithms": {"neural_network": {}, "attention_mechanism": {}},
                "code_quality": {}, "data_flow": {}, "dependencies": {}
            }
        
        generator = PaperGenerator(
            output_dir=self.output_dir,
            paper_plan=paper_plan,
            analysis_result=analysis_result,
            gpt_version=self.gpt_version
        )
        paper = generator.generate_paper()
        markdown_path = generator.save_paper_markdown(paper)
        tex_path = generator.save_paper_tex(paper)
        generator.save_paper_pdf(tex_path)
        print(f"[+] Paper saved at: {markdown_path}")

    def run_all(self):
        self.preprocess()
        self.plan()
        self.analyze()
        self.generate_paper()
