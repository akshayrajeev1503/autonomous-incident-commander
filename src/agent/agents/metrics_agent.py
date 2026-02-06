import json
from groq import Groq

def classify_cloudwatch_logs_groq(log_json):

    client = Groq()  # uses GROQ_API_KEY
    results = []

    system_prompt = (
        "You are an expert SRE log classification agent.\n"
        "For the given CloudWatch log message, classify it into:\n"
        "- severity: INFO, WARNING, ERROR, CRITICAL\n"
        "- category: APPLICATION, INFRA, SECURITY, BUSINESS, UNKNOWN\n"
        "- action_required: IGNORE, MONITOR, INVESTIGATE, IMMEDIATE_ACTION\n"
        "- confidence: number between 0.0 and 1.0\n"
        "- reason: short operational explanation\n\n"
        "Rules:\n"
        "- Respond ONLY with valid JSON\n"
        "- No markdown\n"
        "- No extra text\n"
        "- Be deterministic and concise"
    )

    for log in log_json.get("logs", []):
        user_prompt = f'CloudWatch log message:\n"{log.get("message", "")}"'

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw = response.choices[0].message.content

        try:
            classification = json.loads(raw)
        except Exception:
            classification = {
                "severity": "UNKNOWN",
                "category": "UNKNOWN",
                "action_required": "INVESTIGATE",
                "confidence": 0.0,
                "reason": "Failed to parse Groq response"
            }

        results.append({
            "timestamp": log.get("timestamp"),
            "message": log.get("message"),
            "classification": classification
        })

    return results
