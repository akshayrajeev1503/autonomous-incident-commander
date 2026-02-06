from typing import TypedDict, Any, Dict, List
from langgraph.graph import StateGraph, END
from agents.log_agent import LogAgent
from agents.metrics_agent import MetricsAgent
from agents.deploy_agent import DeployAgent

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

def reconcile_findings(state: AgentState) -> Dict[str, Any]:
    log_analysis = state.get("log_analysis", {})
    metrics_analysis = state.get("metrics_analysis", {})
    deployment_analysis = state.get("deployment_analysis", {})
    
    # Synthesis Logic (replicated from original CommanderAgent)
    diagnosis = "Unknown Issue"
    if "out of memory" in log_analysis.get("issues", []) or "MemoryUsed" in metrics_analysis.get("alerts", []):
            diagnosis = "Potential Memory Exhaustion"
            if "memory_size" in deployment_analysis.get("changes", {}):
                diagnosis += " likely caused by recent configuration change (memory reduction)."
    
    final_diagnosis = {
        "status": "Investigation Complete",
        "diagnosis": diagnosis,
        "details": {
            "log_analysis": log_analysis,
            "metrics_analysis": metrics_analysis,
            "deployment_analysis": deployment_analysis
        }
    }
    return {"final_diagnosis": final_diagnosis}

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("log_agent", run_log_agent)
workflow.add_node("metrics_agent", run_metrics_agent)
workflow.add_node("deploy_agent", run_deploy_agent)
workflow.add_node("reconciler", reconcile_findings)

# Set Entry Point
# We branch to all 3 agents immediately. 
# Note: LangGraph doesn't have a "broadcast" primitive exactly like this in valid start nodes,
# but we can have a dummy start node that edges to all three, or just set entry point to one and parallelize.
# OR cleaner: Use a fan-out node.
# Let's use a dummy 'start' node that just passes state through to be explicit, but actually
# we can just add edges from a virtual start.
# For true parallel execution in the graph structure:
# We can make them all available from start.
workflow.set_entry_point("log_agent") # This would be sequential if we just chain.
# To run parallel, we need a common starting node that branches.

def start_node(state: AgentState):
    return state

workflow.add_node("start", start_node)
workflow.set_entry_point("start")

workflow.add_edge("start", "log_agent")
workflow.add_edge("start", "metrics_agent")
workflow.add_edge("start", "deploy_agent")

# All agents point to reconciler
workflow.add_edge("log_agent", "reconciler")
workflow.add_edge("metrics_agent", "reconciler")
workflow.add_edge("deploy_agent", "reconciler")

# Reconciler ends
workflow.add_edge("reconciler", END)

# Compile
app = workflow.compile()
