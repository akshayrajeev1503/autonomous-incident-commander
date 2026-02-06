import os
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from secrets_manager import get_secret

logger = logging.getLogger()

class LogAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="openai/gpt-oss-20b",
            api_key=get_secret()
        )

    def analyze(self, log_payload):
        logger.info("Log Agent: Analyzing logs with LLM...")
        
        log_events = log_payload.get('logEvents', [])
        logs_text = "\n".join([f"{e.get('timestamp')}: {e.get('message')}" for e in log_events])

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Log Analyst. Analyze the following logs and return a JSON object with 'issues' (list of strings describing specific errors found) and 'summary' (brief text). If no errors, 'issues' should be empty."),
            ("human", "{logs}")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"logs": logs_text})
            # Naive parsing, in production use JsonOutputParser
            content = response.content
            # Try to find JSON in the response if it's wrapped in backticks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return {"error": str(e), "issues": []}
