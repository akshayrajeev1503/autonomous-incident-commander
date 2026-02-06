import logging
import os
import difflib
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger()

class DeployAgent:
    def __init__(self):
        # Assuming data is in ../data relative to this file
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama3-70b-8192", 
            api_key=os.getenv("GROQ_API_KEY")
        )

    def analyze(self):
        logger.info("Deploy Agent: Analyzing deployment history with LLM...")
        
        changes_text = ""
        # Compare Terraform files
        try:
            with open(os.path.join(self.data_path, 'main_prev.tf'), 'r') as f:
                prev_tf = f.readlines()
            with open(os.path.join(self.data_path, 'main_current.tf'), 'r') as f:
                curr_tf = f.readlines()
            
            diff = difflib.unified_diff(prev_tf, curr_tf, fromfile='main_prev.tf', tofile='main_current.tf')
            changes_text = ''.join(diff)
                
        except Exception as e:
            logger.error(f"Failed to compare terraform files: {e}")
            return {"error": str(e)}

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an Expert DevOps Engineer. Analyze the following Terraform diff. Identify any changes that could negatively impact system stability (e.g., reducing resources, removing env vars). Return a JSON object with 'changes' (a dictionary where keys are the changed parameters and values are brief explanations of the risk) and 'risk_level' (Low/Medium/High)."),
            ("human", "{diff}")
        ])

        chain = prompt | self.llm

        try:
            response = chain.invoke({"diff": changes_text})
            # Naive parsing
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
        except Exception as e:
            return {"error": str(e), "changes": {}}
