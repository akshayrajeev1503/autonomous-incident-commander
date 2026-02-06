import gzip
import json
import base64
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Agent Lambda that ingests CloudWatch Logs.
    The 'awslogs' data is base64 encoded and gzip compressed.
    """
    try:
        # 1. Decode and Decompress
        encoded_data = event['awslogs']['data']
        compressed_data = base64.b64decode(encoded_data)
        decompressed_data = gzip.decompress(compressed_data)
        payload = json.loads(decompressed_data)

        # 2. Extract Metadata and Messages
        log_group = payload.get('logGroup')
        log_stream = payload.get('logStream')
        log_events = payload.get('logEvents', [])

        logger.info(f"Received logs from Log Group: {log_group}, Stream: {log_stream}")

        for log_event in log_events:
            message = log_event.get('message')
            timestamp = log_event.get('timestamp')
            
            # The message from the logging lambda might be a JSON string itself (if we logged json.dumps)
            # or just a plain string. We'll try to parse it if it looks like JSON.
            try:
                message_json = json.loads(message)
                # If successful, we have a structured object essentially triggering this agent
                logger.info(f"Processed Structured Log: {json.dumps(message_json)}")
                
                # HERE IS WHERE THE AGENT LOGIC WOULD GO
                # e.g., "if message_json['system']['platform'] == 'Linux'..."
                
            except (json.JSONDecodeError, TypeError):
                # Fallback for plain text logs
                logger.info(f"Processed Text Log: {message}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Logs processed successfully"})
        }

    except Exception as e:
        logger.error(f"Error processing logs: {e}")
        raise e
