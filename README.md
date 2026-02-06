# 🚨 Autonomous Incident Commander

An AI-powered system that automatically investigates production incidents when they happen. When your Lambda function crashes, this system analyzes logs, metrics, and recent deployments to tell you **what went wrong** and **how to fix it**.

---

## 💡 The Problem

When production breaks at 2 AM:
- You scramble to check CloudWatch logs
- You dig through recent deployments
- You try to correlate metrics with errors
- You waste precious time on manual investigation

## ✨ The Solution

**Autonomous Incident Commander** does this automatically:

1. **Detects** the incident via CloudWatch log subscription
2. **Investigates** using specialized AI agents running in parallel
3. **Synthesizes** findings into a root cause analysis
4. **Reports** via a live dashboard you can access anytime

---

## 🏗️ Architecture

![Architecture](architecture.png)

---

## 🤖 AI Agents

| Agent | What it does |
|-------|--------------|
| **Log Agent** | Reads error logs and identifies issues |
| **Metrics Agent** | Checks CPU, memory, and system health |
| **Deploy Agent** | Compares recent deployment changes |
| **Investigation Agent** | Combines everything into a diagnosis |

All agents use LLMs (via Groq) to intelligently analyze data rather than simple pattern matching.

---

## 📊 Output

The system produces a comprehensive incident report:

- **Severity** (Critical / High / Medium / Low)
- **Root Cause** (e.g., "Memory reduced from 512MB to 128MB")
- **Diagnosis** (Detailed explanation)
- **Recommendations** (Prioritized action items)
- **Confidence Level** (How sure the system is)

Access it via the Lambda Function URL as a live HTML dashboard.

---

## 🛠️ Tech Stack

- **LangGraph** – Agent orchestration
- **Groq** – Fast LLM inference
- **AWS Lambda** – Serverless execution
- **Amazon S3** – Report persistence
- **CloudWatch** – Log ingestion

---

## 🚀 Quick Start

```bash
# 1. Set your API key
export GROQ_API_KEY=your-key

# 2. Run locally
cd src/agent
pip install -r requirements.txt
python test_decoding.py

# 3. View the report
open output/report.html
```

---

## 📄 License

MIT