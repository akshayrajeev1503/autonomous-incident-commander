import gzip
import base64
import json
import app

def test_decoding():
    # 1. Create a dummy log payload
    log_data = {
        "logGroup": "/aws/lambda/test_function",
        "logStream": "test_stream",
        "logEvents": [
            {
                "timestamp": 1234567890,
                "message": json.dumps({"system": "Linux", "status": "critical"})
            },
            {
                "timestamp": 1234567891,
                "message": "Simple text log message"
            }
        ]
    }
    
    # 2. Compress and Encode
    json_bytes = json.dumps(log_data).encode('utf-8')
    compressed = gzip.compress(json_bytes)
    encoded = base64.b64encode(compressed).decode('utf-8')
    
    event = {
        "awslogs": {
            "data": encoded
        }
    }
    
    # 3. Invoke Handler
    print("Invoking handler with mocked CloudWatch event...")
    response = app.handler(event, None)
    print(f"Response: {response}")

if __name__ == "__main__":
    test_decoding()
