import json
import logging
import os
import sys
import platform

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda handler that logs extensive details about the environment and request.
    """
    logger.info("Function started")

    # 1. Log System Information
    system_info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_executable": sys.executable,
    }
    logger.info(f"System Info: {json.dumps(system_info)}")

    # 2. Log Environment Variables
    # Be careful with sensitive data in production, but for this task we log everything as requested.
    env_vars = dict(os.environ)
    logger.info(f"Environment Variables: {json.dumps(env_vars, default=str)}")

    # 3. Log Context Object
    # Context object cannot be directly serialized to JSON easily, so we extract known properties.
    context_info = {
        "function_name": getattr(context, "function_name", "N/A"),
        "function_version": getattr(context, "function_version", "N/A"),
        "invoked_function_arn": getattr(context, "invoked_function_arn", "N/A"),
        "memory_limit_in_mb": getattr(context, "memory_limit_in_mb", "N/A"),
        "aws_request_id": getattr(context, "aws_request_id", "N/A"),
        "log_group_name": getattr(context, "log_group_name", "N/A"),
        "log_stream_name": getattr(context, "log_stream_name", "N/A"),
        "remaining_time_ms": context.get_remaining_time_in_millis() if hasattr(context, "get_remaining_time_in_millis") else "N/A"
    }
    logger.info(f"Context Info: {json.dumps(context_info)}")

    # 4. Log Event Payload
    logger.info(f"Event Payload: {json.dumps(event)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Logging complete",
            "request_id": context_info["aws_request_id"]
        })
    }
