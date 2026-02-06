from typing import TypedDict, Any, Dict, List
from langgraph.graph import StateGraph, END
from agents.log_agent import LogAgent
from agents.metrics_agent import MetricsAgent
from agents.deploy_agent import DeployAgent
from agents.investigation_agent import InvestigationAgent

# Define the State
class AgentState(TypedDict):
    log_payload: Dict[str, Any]
    log_analysis: Dict[str, Any]
    metrics_analysis: Dict[str, Any]
    deployment_analysis: Dict[str, Any]
    final_diagnosis: Dict[str, Any]

# Instantiate Agents
log_agent = LogAgent()
metrics_agent = MetricsAgent()
deploy_agent = DeployAgent()
investigation_agent = InvestigationAgent()

# Define Nodes
def run_log_agent(state: AgentState) -> Dict[str, Any]:
    payload = state.get("log_payload", {})
    return {"log_analysis": log_agent.analyze(payload)}

def run_metrics_agent(state: AgentState) -> Dict[str, Any]:
    payload = state.get("log_payload", {})
    return {"metrics_analysis": metrics_agent.analyze(payload)}

def run_deploy_agent(state: AgentState) -> Dict[str, Any]:
    # Deploy agent creates its own context from files, doesn't strictly need payload but we keep signature consistent
    return {"deployment_analysis": deploy_agent.analyze()}

def run_investigation_agent(state: AgentState) -> Dict[str, Any]:
    """
    The Investigation Agent synthesizes findings from all specialized agents
    and produces a comprehensive final investigation report.
    """
    log_analysis = state.get("log_analysis", {})
    metrics_analysis = state.get("metrics_analysis", {})
    deployment_analysis = state.get("deployment_analysis", {})
    
    # Use the LLM-powered Investigation Agent for intelligent synthesis
    final_report = investigation_agent.synthesize(
        log_analysis=log_analysis,
        metrics_analysis=metrics_analysis,
        deployment_analysis=deployment_analysis
    )
    
    return {"final_diagnosis": final_report}

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("log_agent", run_log_agent)
workflow.add_node("metrics_agent", run_metrics_agent)
workflow.add_node("deploy_agent", run_deploy_agent)
workflow.add_node("investigation_agent", run_investigation_agent)

# Set Entry Point with fan-out pattern for parallel execution
def start_node(state: AgentState):
    return state

workflow.add_node("start", start_node)
workflow.set_entry_point("start")

# Fan-out: Start branches to all 3 specialized agents in parallel
workflow.add_edge("start", "log_agent")
workflow.add_edge("start", "metrics_agent")
workflow.add_edge("start", "deploy_agent")

# Fan-in: All specialized agents converge to the Investigation Agent
workflow.add_edge("log_agent", "investigation_agent")
workflow.add_edge("metrics_agent", "investigation_agent")
workflow.add_edge("deploy_agent", "investigation_agent")

# Investigation Agent produces final report and ends
workflow.add_edge("investigation_agent", END)

# Compile
app = workflow.compile()

