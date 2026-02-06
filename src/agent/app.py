import gzip
import json
import base64
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from graph import app as workflow_app

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Agent Lambda that ingests CloudWatch Logs.
    Orchestrates investigation via LangGraph.
    """
    try:
        # 1. Decode and Decompress
        encoded_data = event['awslogs']['data']
        compressed_data = base64.b64decode(encoded_data)
        decompressed_data = gzip.decompress(compressed_data)
        payload = json.loads(decompressed_data)

        # 2. Extract Basic Info for Logging
        log_group = payload.get('logGroup')
        log_stream = payload.get('logStream')
        logger.info(f"Received logs from Log Group: {log_group}, Stream: {log_stream}")

        # 3. Invoke LangGraph
        initial_state = {"log_payload": payload}
        final_state = workflow_app.invoke(initial_state)
        
        investigation_report = final_state.get("final_diagnosis", {})
        logger.info(f"Investigation Report: {json.dumps(investigation_report, default=str)}")

        return {
            "statusCode": 200,
            "body": json.dumps(investigation_report, default=str)
        }

    except Exception as e:
        logger.error(f"Error processing logs: {e}")
        raise e
