import os
import logging
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger()


class InvestigationAgent:
    """
    The Investigation Agent synthesizes findings from all specialized agents
    (LogAgent, MetricsAgent, DeployAgent) and produces a comprehensive
    final investigation report with root cause analysis and recommendations.
    """

    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY")
        )

    def synthesize(self, log_analysis: dict, metrics_analysis: dict, deployment_analysis: dict) -> dict:
        """
        Synthesizes findings from all agents into a final investigation report.
        
        Args:
            log_analysis: Analysis results from LogAgent
            metrics_analysis: Analysis results from MetricsAgent
            deployment_analysis: Analysis results from DeployAgent
            
        Returns:
            A comprehensive investigation report with diagnosis, root cause, 
            severity, and recommendations.
        """
        logger.info("Investigation Agent: Synthesizing findings from all agents...")

        # Prepare the combined findings for the LLM
        combined_findings = {
            "log_analysis": log_analysis,
            "metrics_analysis": metrics_analysis,
            "deployment_analysis": deployment_analysis
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Site Reliability Engineer (SRE) and Incident Commander. 
Your task is to analyze the investigation findings from multiple specialized agents and produce a comprehensive incident report.

You will receive:
1. Log Analysis: Errors and issues found in application logs
2. Metrics Analysis: System health metrics and alerts
3. Deployment Analysis: Recent infrastructure/deployment changes and their risks

Based on these findings, produce a JSON report with the following structure:
{{
    "status": "Investigation Complete",
    "severity": "Critical/High/Medium/Low",
    "root_cause": "A clear, concise statement of the root cause",
    "diagnosis": "Detailed explanation of what went wrong",
    "correlation": "How the different findings are connected",
    "timeline": "Reconstructed sequence of events if determinable",
    "affected_components": ["list", "of", "affected", "systems"],
    "recommendations": [
        {{
            "priority": "Immediate/Short-term/Long-term",
            "action": "Specific action to take",
            "rationale": "Why this action is recommended"
        }}
    ],
    "confidence_level": "High/Medium/Low",
    "additional_investigation_needed": ["list of areas needing more investigation, if any"]
}}

Be thorough but concise. Focus on actionable insights."""),
            ("human", """Here are the investigation findings:

**Log Analysis:**
{log_analysis}

**Metrics Analysis:**
{metrics_analysis}

**Deployment Analysis:**
{deployment_analysis}

Please synthesize these findings into a comprehensive incident report.""")
        ])

        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "log_analysis": json.dumps(log_analysis, indent=2, default=str),
                "metrics_analysis": json.dumps(metrics_analysis, indent=2, default=str),
                "deployment_analysis": json.dumps(deployment_analysis, indent=2, default=str)
            })

            # Parse the LLM response
            content = response.content
            
            # Handle JSON wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            report = json.loads(content.strip())
            
            # Add the raw findings as supporting evidence
            report["supporting_evidence"] = {
                "log_analysis": log_analysis,
                "metrics_analysis": metrics_analysis,
                "deployment_analysis": deployment_analysis
            }
            
            logger.info(f"Investigation Agent: Report generated with severity={report.get('severity', 'Unknown')}")
            return report

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Return a structured fallback response
            return self._fallback_synthesis(log_analysis, metrics_analysis, deployment_analysis, str(e))
        except Exception as e:
            logger.error(f"Investigation Agent synthesis failed: {e}")
            return self._fallback_synthesis(log_analysis, metrics_analysis, deployment_analysis, str(e))

    def _fallback_synthesis(self, log_analysis: dict, metrics_analysis: dict, 
                           deployment_analysis: dict, error: str) -> dict:
        """
        Provides a rule-based fallback synthesis when LLM fails.
        """
        logger.info("Investigation Agent: Using fallback rule-based synthesis...")
        
        # Simple rule-based diagnosis
        issues = []
        severity = "Low"
        
        # Check log issues
        log_issues = log_analysis.get("issues", [])
        if log_issues:
            issues.extend(log_issues)
            if any("memory" in str(issue).lower() or "error" in str(issue).lower() 
                   for issue in log_issues):
                severity = "High"
        
        # Check metrics alerts
        metrics_alerts = metrics_analysis.get("alerts", [])
        if metrics_alerts:
            issues.extend([f"Metric Alert: {alert}" for alert in metrics_alerts])
            if metrics_analysis.get("status") == "critical":
                severity = "Critical"
            elif metrics_analysis.get("status") == "degraded" and severity != "Critical":
                severity = "High"
        
        # Check deployment risks
        deploy_risk = deployment_analysis.get("risk_level", "Low")
        deploy_changes = deployment_analysis.get("changes", {})
        if deploy_risk in ["High", "Medium"]:
            if severity == "Low":
                severity = "Medium"
            issues.append(f"Recent deployment changes with {deploy_risk} risk")
        
        # Correlate memory issues
        root_cause = "Unable to determine root cause - manual investigation required"
        if any("memory" in str(issue).lower() for issue in issues):
            if "memory_size" in deploy_changes:
                root_cause = "Memory exhaustion likely caused by recent memory_size reduction in deployment"
            else:
                root_cause = "Memory exhaustion detected - check for memory leaks or increased load"
        
        return {
            "status": "Investigation Complete (Fallback Mode)",
            "severity": severity,
            "root_cause": root_cause,
            "diagnosis": f"Detected {len(issues)} issue(s) across log, metrics, and deployment analysis",
            "correlation": "Automated correlation failed - manual review recommended",
            "affected_components": ["Unknown - requires manual investigation"],
            "recommendations": [
                {
                    "priority": "Immediate",
                    "action": "Review the raw findings in supporting_evidence",
                    "rationale": "LLM synthesis failed, manual analysis needed"
                }
            ],
            "confidence_level": "Low",
            "additional_investigation_needed": ["Full manual review required"],
            "fallback_reason": error,
            "supporting_evidence": {
                "log_analysis": log_analysis,
                "metrics_analysis": metrics_analysis,
                "deployment_analysis": deployment_analysis
            }
        }
