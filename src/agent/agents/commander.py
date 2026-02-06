import logging
from .log_agent import LogAgent
from .metrics_agent import MetricsAgent
from .deploy_agent import DeployAgent

logger = logging.getLogger()

class CommanderAgent:
    def __init__(self):
        self.log_agent = LogAgent()
        self.metrics_agent = MetricsAgent()
        self.deploy_agent = DeployAgent()

    def investigate(self, log_payload):
        """
        Orchestrates the investigation process.
        """
        logger.info("Commander Agent: Starting investigation...")
        
        # 1. Gather Intelligence
        log_analysis = self.log_agent.analyze(log_payload)
        metrics_analysis = self.metrics_agent.analyze(log_payload)
        deployment_analysis = self.deploy_agent.analyze()

        # 2. Synthesize Findings
        findings = {
            "log_analysis": log_analysis,
            "metrics_analysis": metrics_analysis,
            "deployment_analysis": deployment_analysis
        }
        
        # 3. Formulate Diagnosis
        diagnosis = "Unknown Issue"
        if "out of memory" in log_analysis.get("issues", []) or "MemoryUsed" in metrics_analysis.get("alerts", []):
             diagnosis = "Potential Memory Exhaustion"
             if "memory_size" in deployment_analysis.get("changes", {}):
                  diagnosis += " likely caused by recent configuration change (memory reduction)."

        return {
            "status": "Investigation Complete",
            "diagnosis": diagnosis,
            "details": findings
        }
