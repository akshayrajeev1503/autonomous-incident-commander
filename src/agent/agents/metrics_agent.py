import os
import logging
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger()

class MetricsAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0, 
            model_name="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY")
        )

    def analyze(self, log_payload):
        logger.info("Metrics Agent: Fetching system metrics and analyzing with LLM...")
        
        # Mocking the data fetch still, but using LLM to interpret it
        mock_metrics = {
            "cpu_utilization": "10%",
            "memory_utilization": "95%",
            "disk_io": "normal"
        }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Systems Engineer. Analyze the provided system metrics and return a JSON object with 'status' (healthy/degraded/critical) and 'alerts' (list of specific concerns)."),
            ("human", "{metrics}")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"metrics": json.dumps(mock_metrics)})
             # Naive parsing
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return {"error": str(e), "alerts": ["High MemoryUsed detected (Fallback)"]}
