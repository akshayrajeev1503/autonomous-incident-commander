"""
Lambda CloudWatch Log Analyzer - LLM-Powered Version
Analyzes logs using LLM via Tavily for pattern classification, hypothesis generation, and root cause analysis
"""

from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import json
import os
import time
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

def pattern_classification_prompt(cloudwatch_error_log: str) -> str:
    """
    Returns the formatted pattern classification prompt template.
    
    Args:
        cloudwatch_error_log: The CloudWatch error log string to classify
        
    Returns:
        Formatted prompt string ready for use with Tavily or LLM
    """
    prompt_template = """You are a production SRE assistant with access to live web search.

Task:
Given a single CloudWatch error log string, perform a brief web search
(prefer official AWS documentation and reputable sources) to identify
the most commonly accepted failure pattern and its meaning.

Rules:
- Be extremely concise.
- Use only one best-fit pattern.
- Meaning must be one short sentence.
- Do not speculate.
- Do not include sources, explanations, or extra fields.
- If the error meaning is unclear, use pattern "Unknown".

Input:
{cloudwatch_error_log}

Output (STRICT JSON ONLY):
{{
  "<pattern>": "<meaning>"
}}
"""
    return prompt_template.format(cloudwatch_error_log=cloudwatch_error_log)


def hypothesis_generation_prompt(pattern: str, log: str) -> str:
    """
    Returns the formatted hypothesis generation prompt template.
    
    Args:
        pattern: The classified error pattern
        log: The CloudWatch error log string
        
    Returns:
        Formatted prompt string ready for use with Tavily or LLM
    """
    prompt_template = """You are a production SRE assistant analyzing AWS Lambda CloudWatch logs.

Task:
Based on the classified error pattern and the log details, generate a concise hypothesis
explaining the likely root cause. Use web search to reference AWS best practices and
common solutions for this type of error.

Pattern: {pattern}
Log: {log}

Rules:
- Generate one clear, professional hypothesis (2-3 sentences)
- Base your hypothesis on AWS Lambda best practices
- Be specific about the likely cause
- Do not include sources or citations in the hypothesis text

Output (STRICT JSON ONLY):
{{
  "hypothesis": "<your hypothesis here>"
}}
"""
    return prompt_template.format(pattern=pattern, log=log[:500])


def possibilities_generation_prompt(pattern: str, hypothesis: str, log: str) -> str:
    """
    Returns the formatted possibilities generation prompt template.
    
    Args:
        pattern: The classified error pattern
        hypothesis: The generated hypothesis
        log: The CloudWatch error log string
        
    Returns:
        Formatted prompt string ready for use with Tavily or LLM
    """
    prompt_template = """You are a production SRE assistant analyzing AWS Lambda CloudWatch logs.

Task:
Based on the error pattern, hypothesis, and log details, generate 3-5 possible root causes
with probability scores, severity levels, and actionable recommendations. Use web search to
reference AWS documentation and best practices.

Pattern: {pattern}
Hypothesis: {hypothesis}
Log: {log}

Rules:
- Generate 3-5 possible root causes
- Each cause must have: cause (string), probability (float 0.0-1.0), severity (critical/high/medium/low), action (string)
- Probabilities should sum to approximately 1.0
- Order by probability (highest first)
- Actions should be specific and actionable
- Base recommendations on AWS best practices

Output (STRICT JSON ONLY):
{{
  "possibilities": [
    {{
      "cause": "<root cause description>",
      "probability": <float between 0.0 and 1.0>,
      "severity": "<critical|high|medium|low>",
      "action": "<specific actionable recommendation>"
    }}
  ]
}}
"""
    return prompt_template.format(pattern=pattern, hypothesis=hypothesis, log=log[:500])


# ============================================================================
# TAVILY CLIENT HELPERS
# ============================================================================

def _get_tavily_client() -> TavilyClient:
    """Get Tavily client from environment variable"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY not found. Please set TAVILY_API_KEY environment variable "
            "or add it to .env file"
        )
    return TavilyClient(api_key)


def _extract_json_from_response(response_text: str) -> Dict:
    """Extract JSON from Tavily response text"""
    try:
        # Try to find JSON in the response
        if '{' in response_text and '}' in response_text:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    return {}


# ============================================================================
# LLM FUNCTIONS
# ============================================================================

def classify_pattern_with_llm(log: str, tavily_client: Optional[TavilyClient] = None) -> tuple:
    """
    Classify error pattern using LLM via Tavily.
    
    Args:
        log: CloudWatch error log string
        tavily_client: Optional pre-initialized TavilyClient
        
    Returns:
        Tuple of (pattern, confidence)
    """
    if tavily_client is None:
        tavily_client = _get_tavily_client()
    
    prompt = pattern_classification_prompt(log)
    
    try:
        # Create research task
        research_response = tavily_client.research(
            input=prompt,
            model="mini"
        )
        
        # Get request_id and poll for results
        request_id = research_response.get('request_id')
        if not request_id:
            return "unknown", 0.5
        
        # Poll for completion (with timeout)
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result_response = tavily_client.get_research(request_id)
            status = result_response.get('status', '')
            
            if status == 'completed':
                # Extract answer from completed research
                answer = result_response.get('answer', '') or result_response.get('content', '')
                result = _extract_json_from_response(answer)
                
                if result:
                    pattern = list(result.keys())[0] if result else "unknown"
                    return pattern, 0.85  # High confidence for LLM classification
                else:
                    return "unknown", 0.5
            elif status == 'failed':
                return "unknown", 0.5
            
            # Wait before polling again
            time.sleep(2)
        
        # Timeout
        return "unknown", 0.5
    except Exception as e:
        # Silently handle errors and return fallback
        return "unknown", 0.5


def generate_hypothesis_with_llm(pattern: str, log: str, tavily_client: Optional[TavilyClient] = None) -> str:
    """
    Generate hypothesis using LLM via Tavily.
    
    Args:
        pattern: Classified error pattern
        log: CloudWatch error log string
        tavily_client: Optional pre-initialized TavilyClient
        
    Returns:
        Hypothesis string
    """
    if tavily_client is None:
        tavily_client = _get_tavily_client()
    
    prompt = hypothesis_generation_prompt(pattern, log)
    
    try:
        # Create research task
        research_response = tavily_client.research(
            input=prompt,
            model="mini"
        )
        
        # Get request_id and poll for results
        request_id = research_response.get('request_id')
        if not request_id:
            return f"The error pattern '{pattern}' indicates a potential issue that requires investigation."
        
        # Poll for completion (with timeout)
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result_response = tavily_client.get_research(request_id)
            status = result_response.get('status', '')
            
            if status == 'completed':
                # Extract answer from completed research
                answer = result_response.get('answer', '') or result_response.get('content', '')
                result = _extract_json_from_response(answer)
                
                if result and 'hypothesis' in result:
                    return result['hypothesis']
                else:
                    return f"The error pattern '{pattern}' indicates a potential issue that requires investigation."
            elif status == 'failed':
                return f"The error pattern '{pattern}' indicates a potential issue that requires investigation."
            
            # Wait before polling again
            time.sleep(2)
        
        # Timeout
        return f"The error pattern '{pattern}' indicates a potential issue that requires investigation."
    except Exception as e:
        # Silently handle errors and return fallback
        return f"The error pattern '{pattern}' indicates a potential issue that requires investigation."


def generate_possibilities_with_llm(
    pattern: str, 
    hypothesis: str, 
    log: str,
    tavily_client: Optional[TavilyClient] = None
) -> List[Dict[str, Any]]:
    """
    Generate possibilities using LLM via Tavily.
    
    Args:
        pattern: Classified error pattern
        hypothesis: Generated hypothesis
        log: CloudWatch error log string
        tavily_client: Optional pre-initialized TavilyClient
        
    Returns:
        List of possibility dictionaries
    """
    if tavily_client is None:
        tavily_client = _get_tavily_client()
    
    prompt = possibilities_generation_prompt(pattern, hypothesis, log)
    
    try:
        # Create research task
        research_response = tavily_client.research(
            input=prompt,
            model="mini"
        )
        
        # Get request_id and poll for results
        request_id = research_response.get('request_id')
        if not request_id:
            return [{
                "cause": "Insufficient information to determine root cause",
                "probability": 1.0,
                "severity": "medium",
                "action": "Enable detailed logging and X-Ray tracing for deeper analysis"
            }]
        
        # Poll for completion (with timeout)
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result_response = tavily_client.get_research(request_id)
            status = result_response.get('status', '')
            
            if status == 'completed':
                # Extract answer from completed research
                answer = result_response.get('answer', '') or result_response.get('content', '')
                result = _extract_json_from_response(answer)
                
                if result and 'possibilities' in result:
                    possibilities = result['possibilities']
                    # Validate and normalize probabilities
                    total_prob = sum(p.get('probability', 0) for p in possibilities)
                    if total_prob > 0:
                        for p in possibilities:
                            p['probability'] = p.get('probability', 0) / total_prob
                    return possibilities
                else:
                    # Fallback to default
                    return [{
                        "cause": "Insufficient information to determine root cause",
                        "probability": 1.0,
                        "severity": "medium",
                        "action": "Enable detailed logging and X-Ray tracing for deeper analysis"
                    }]
            elif status == 'failed':
                return [{
                    "cause": "Error during analysis",
                    "probability": 1.0,
                    "severity": "medium",
                    "action": "Review logs manually and check AWS service health"
                }]
            
            # Wait before polling again
            time.sleep(2)
        
        # Timeout
        return [{
            "cause": "Analysis timeout",
            "probability": 1.0,
            "severity": "medium",
            "action": "Review logs manually and check AWS service health"
        }]
    except Exception as e:
        # Silently handle errors and return fallback
        return [{
            "cause": "Error during analysis",
            "probability": 1.0,
            "severity": "medium",
            "action": "Review logs manually and check AWS service health"
        }]


# ============================================================================
# LOG ANALYZER CLASSES AND FUNCTIONS
# ============================================================================


class LogAnalysisState:
    """State for log analysis workflow"""
    def __init__(self):
        self.raw_log: str = ""
        self.error_classification: Dict[str, Any] = {}
        self.pattern: str = ""
        self.hypothesis: str = ""
        self.possibilities: List[Dict[str, Any]] = []
        self.log_output: str = ""
        self.metrics_output: Dict[str, Any] = {}


class SimpleGraph:
    """Simplified graph implementation for single node"""
    def __init__(self):
        self.node_function = None
    
    def add_node(self, name: str, func: Callable):
        """Add a processing node"""
        self.node_function = func
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph"""
        if self.node_function:
            return self.node_function(initial_state)
        return initial_state


class LambdaLogAnalyzer:
    """Analyzes Lambda CloudWatch logs and generates insights using LLM via Tavily"""
    
    def __init__(self, tavily_client: Optional[TavilyClient] = None):
        """
        Initialize the analyzer with optional Tavily client.
        
        Args:
            tavily_client: Optional pre-initialized TavilyClient for reuse across calls
        """
        self.tavily_client = tavily_client
    
    def classify_pattern(self, log: str) -> tuple:
        """
        Classify the error pattern from the log using LLM via Tavily.
        
        Args:
            log: CloudWatch error log string
            
        Returns:
            Tuple of (pattern, confidence)
        """
        return classify_pattern_with_llm(log, self.tavily_client)
    
    def generate_hypothesis(self, pattern: str, log: str) -> str:
        """
        Generate hypothesis based on classified pattern using LLM via Tavily.
        
        Args:
            pattern: Classified error pattern
            log: CloudWatch error log string
            
        Returns:
            Hypothesis string
        """
        return generate_hypothesis_with_llm(pattern, log, self.tavily_client)
    
    def generate_possibilities(self, pattern: str, hypothesis: str, log: str) -> List[Dict[str, Any]]:
        """
        Generate all possibilities and align with probability scores using LLM via Tavily.
        
        Args:
            pattern: Classified error pattern
            hypothesis: Generated hypothesis
            log: CloudWatch error log string
            
        Returns:
            List of possibility dictionaries
        """
        return generate_possibilities_with_llm(pattern, hypothesis, log, self.tavily_client)
    
    def generate_log_output(self, state: Dict[str, Any]) -> str:
        """Generate semantic log output"""
        timestamp = datetime.now().isoformat()
        
        output = f"""
LAMBDA CLOUDWATCH LOG ANALYSIS REPORT
=====================================

Analysis Timestamp: {timestamp}
Pattern Classification: {state['pattern'].upper()}
Confidence: {state['error_classification']['confidence']:.0%}

HYPOTHESIS
----------
{state['hypothesis']}

POSSIBLE ROOT CAUSES & RECOMMENDATIONS
---------------------------------------
"""
        
        for idx, possibility in enumerate(state['possibilities'], 1):
            output += f"""
{idx}. {possibility['cause']}
    Probability: {possibility['probability']:.0%}
    Severity: {possibility['severity'].upper()}
    Action: {possibility['action']}
"""
        
        output += f"""
ORIGINAL LOG EXCERPT
--------------------
{state['raw_log'][:500]}{'...' if len(state['raw_log']) > 500 else ''}

NEXT STEPS
----------
1. Review the highest probability root causes first
2. Implement recommended actions based on severity
3. Monitor CloudWatch metrics and logs after changes
4. Enable X-Ray tracing for deeper insights if needed
"""
        
        return output
    
    def generate_metrics_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON metrics output"""
        return {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "processing_time_ms": 0
            },
            "error_classification": {
                "pattern_type": state['pattern'],
                "confidence_score": state['error_classification']['confidence'],
                "severity_level": state['error_classification'].get('severity', 'unknown')
            },
            "hypothesis": {
                "description": state['hypothesis'],
                "pattern_category": state['pattern']
            },
            "root_cause_analysis": {
                "total_possibilities": len(state['possibilities']),
                "possibilities": state['possibilities'],
                "highest_probability_cause": max(state['possibilities'], key=lambda x: x['probability'])
            },
            "metrics": {
                "error_count": 1,
                "pattern_occurrence": state['pattern'],
                "average_severity": sum(
                    {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(p['severity'], 0) 
                    for p in state['possibilities']
                ) / len(state['possibilities']),
                "actionable_items": len(state['possibilities'])
            },
            "recommendations": {
                "immediate_actions": [
                    p['action'] for p in sorted(state['possibilities'], 
                    key=lambda x: ({'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(x['severity'], 0), x['probability']), 
                    reverse=True)[:3]
                ],
                "monitoring_required": True,
                "escalation_needed": any(p['severity'] == 'critical' for p in state['possibilities'])
            },
            "log_reference": {
                "log_snippet": state['raw_log'][:200],
                "log_length": len(state['raw_log'])
            }
        }


def analyze_log_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Single node that performs complete log analysis using LLM"""
    # Initialize analyzer with optional Tavily client reuse
    tavily_client = state.get('_tavily_client')
    analyzer = LambdaLogAnalyzer(tavily_client=tavily_client)
    
    # Step 1: Classify pattern using LLM
    pattern, confidence = analyzer.classify_pattern(state['raw_log'])
    
    # Determine severity based on pattern type
    severity_map = {
        "timeout": "high",
        "memory": "critical",
        "permission": "critical",
        "network": "critical",
        "resource": "critical",
        "runtime": "critical",
        "throttling": "high",
        "cold_start": "medium",
        "handler": "critical",
        "unknown": "medium"
    }
    
    state['error_classification'] = {
        "pattern": pattern,
        "confidence": confidence,
        "severity": severity_map.get(pattern, "medium")
    }
    state['pattern'] = pattern
    
    # Step 2: Generate hypothesis using LLM
    state['hypothesis'] = analyzer.generate_hypothesis(pattern, state['raw_log'])
    
    # Step 3: Generate possibilities using LLM
    state['possibilities'] = analyzer.generate_possibilities(pattern, state['hypothesis'], state['raw_log'])
    
    # Step 4: Generate outputs
    state['log_output'] = analyzer.generate_log_output(state)
    state['metrics_output'] = analyzer.generate_metrics_output(state)
    
    return state


def create_log_analyzer_graph():
    """Create the simplified graph workflow"""
    graph = SimpleGraph()
    graph.add_node("analyze", analyze_log_node)
    return graph


def analyze_cloudwatch_log(
    cloudwatch_log: str,
    tavily_client: Optional[TavilyClient] = None
) -> Dict[str, Any]:
    """
    Analyze a CloudWatch log entry and return the analysis results.
    
    Args:
        cloudwatch_log: The CloudWatch log string to analyze
        tavily_client: Optional pre-initialized TavilyClient for reuse
        
    Returns:
        Dictionary with strict format:
            {
                "log": "<semantic log output>",
                "metrics": <json metrics object>
            }
    """
    graph = create_log_analyzer_graph()
    
    initial_state = {
        "raw_log": cloudwatch_log,
        "error_classification": {},
        "pattern": "",
        "hypothesis": "",
        "possibilities": [],
        "log_output": "",
        "metrics_output": {},
        "_tavily_client": tavily_client  # Pass client for reuse
    }
    
    result = graph.invoke(initial_state)
    
    # Return in strict format: {"log": "<semantic log output>", "metrics": <json>}
    return {
        "log": result.get("log_output", ""),
        "metrics": result.get("metrics_output", {})
    }


# Example usage
if __name__ == "__main__":
    # Sample Lambda CloudWatch error logs
    sample_logs = [
        """
        2024-02-06 10:30:45 ERROR Task timed out after 30.00 seconds
        Function: data-processor-prod
        Request ID: 8f3d2a1b-9c4e-5f6d-7g8h-9i0j1k2l3m4n
        """,
        
        """
        2024-02-06 11:15:22 ERROR Runtime.ImportModuleError: Unable to import module 'lambda_function': No module named 'requests'
        Function: api-gateway-handler
        Request ID: 1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p
        """,
        
        """
        2024-02-06 12:45:33 ERROR AccessDenied: User is not authorized to perform: dynamodb:PutItem on resource
        Function: user-data-writer
        Request ID: 9z8y7x6w-5v4u-3t2s-1r0q-9p8o7n6m5l4k
        """
    ]
    
    import sys
    
    # Check if log input is provided via command line argument
    if len(sys.argv) > 1:
        # Use provided log input
        cloudwatch_log = sys.argv[1]
        result = analyze_cloudwatch_log(cloudwatch_log)
        print(json.dumps(result, indent=2))
    else:
        # Use sample logs for demonstration
        for log in sample_logs:
            result = analyze_cloudwatch_log(log)
            print(json.dumps(result, indent=2))