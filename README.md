# Python Code Execution API

A secure API service that executes arbitrary Python scripts in a sandboxed environment using Flask and nsjail. The service accepts Python code via HTTP POST requests and returns the result of the `main()` function execution.

## Features

- **Secure Execution**: Uses nsjail for sandboxing Python script execution
- **Resource Limits**: Memory, CPU time, and file size restrictions
- **Input Validation**: Ensures scripts contain a `main()` function
- **Standard Libraries**: Includes numpy, pandas, and os modules
- **Lightweight**: Built on Python 3.11-slim Docker image
- **Cloud Ready**: Designed for Google Cloud Run deployment

## API Endpoints

### `POST /execute`

Executes a Python script and returns the result.

**Request Body:**

```json
{
  "script": "def main():\n    return {'message': 'Hello, World!'}"
}
```

**Response:**

```json
{
  "result": { "message": "Hello, World!" },
  "stdout": ""
}
```

### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy"
}
```

## Script Requirements

1. **Must contain a `main()` function**: The script must define a function named `main()`
2. **Must return JSON-serializable data**: The `main()` function should return data that can be serialized to JSON
3. **Available libraries**: numpy, pandas, os, and standard Python libraries are available

## Example Scripts

### Simple Return

```python
def main():
    return {"result": "success", "value": 42}
```

### Using Libraries

```python
import numpy as np
import pandas as pd

def main():
    # Create a simple dataset
    data = pd.DataFrame({
        'numbers': [1, 2, 3, 4, 5],
        'squares': [1, 4, 9, 16, 25]
    })

    # Calculate mean using numpy
    mean_value = np.mean(data['numbers'])

    return {
        "mean": mean_value,
        "data_shape": data.shape,
        "total_records": len(data)
    }
```

### With Print Statements

```python
def main():
    print("This will appear in stdout")
    print("Processing data...")

    result = {"processed": True, "items": 10}
    print(f"Processed {result['items']} items")

    return result
```

## Local Development

### Prerequisites

- Docker

### Running Locally

1. **Build the Docker image:**

```bash
docker build -t python-executor .
```

2. **Run the container:**

```bash
docker run -p 8080:8080 python-executor
```

3. **Test the service:**

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello from local Docker!\"}"
  }'
```

## Example cURL Requests

### Basic Example

```bash
curl -X POST https://python-executor-XXXXX-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"result\": \"Hello, World!\", \"timestamp\": \"2024-01-01\"}"
  }'
```

### Data Processing Example

```bash
curl -X POST https://python-executor-XXXXX-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\nimport numpy as np\n\ndef main():\n    data = pd.DataFrame({\"values\": [1, 2, 3, 4, 5]})\n    return {\"mean\": float(np.mean(data[\"values\"])), \"sum\": int(data[\"values\"].sum())}"
  }'
```

### Error Handling Example

```bash
curl -X POST https://python-executor-XXXXX-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    raise ValueError(\"This is a test error\")"
  }'
```

## Security Features

- **Process Isolation**: Subprocess execution with timeout limits
- **Resource Limits**:
  - Execution timeout: 30 seconds
  - Memory limits via container constraints
- **Container Isolation**: Docker provides base-level isolation
- **Input Validation**: Strict validation of script requirements
- **Temporary File Cleanup**: Automatic cleanup of execution artifacts

**Note**: This implementation uses subprocess execution for compatibility. For enhanced security in production environments, consider implementing nsjail or similar sandboxing technologies.

## Error Responses

### Missing main() function

```json
{
  "error": "Script must contain a main() function"
}
```

### Invalid JSON

```json
{
  "error": "Request must be JSON"
}
```

### Execution timeout

```json
{
  "error": "Script execution timed out"
}
```

### Runtime error

```json
{
  "error": "Script execution error: division by zero"
}
```

## Deployment

### Google Cloud Run

1. **Build and push to Google Container Registry:**

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Build and tag the image
docker build -t gcr.io/$PROJECT_ID/python-executor .

# Push to GCR
docker push gcr.io/$PROJECT_ID/python-executor
```

2. **Deploy to Cloud Run:**

```bash
gcloud run deploy python-executor \
  --image gcr.io/$PROJECT_ID/python-executor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10
```

3. **Get the service URL:**

```bash
gcloud run services describe python-executor \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

## Testing the Cloud Run Service

Replace the URL with your actual Cloud Run service URL:

```bash
# Test with a simple script
curl -X POST https://python-executor-XXXXX-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import os\n    return {\"python_version\": \"3.11\", \"available_modules\": [\"numpy\", \"pandas\", \"os\"]}"
  }'

# Test with data processing
curl -X POST https://python-executor-XXXXX-uc.a.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\nimport pandas as pd\n\ndef main():\n    # Create sample data\n    data = np.random.rand(100)\n    df = pd.DataFrame({\"values\": data})\n    \n    return {\n        \"mean\": float(df[\"values\"].mean()),\n        \"std\": float(df[\"values\"].std()),\n        \"count\": len(df)\n    }"
  }'
```

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   HTTP Client   │───▶│  Flask App   │───▶│  nsjail + Python│
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐    ┌─────────────────┐
                       │  Validation  │    │  Temp Files     │
                       └──────────────┘    └─────────────────┘
```

## Performance Considerations

- **Cold Start**: ~2-3 seconds for first request
- **Warm Instance**: ~100-500ms for subsequent requests
- **Memory Usage**: ~50-100MB base + script requirements
- **Concurrent Requests**: Handled by Cloud Run auto-scaling

## Limitations

- **Execution Timeout**: 30 seconds maximum
- **Memory Limit**: 512MB per execution
- **No Network Access**: Scripts cannot make external HTTP requests
- **No Persistent Storage**: Files are not persisted between requests
- **Python Version**: Fixed to Python 3.11

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with Docker
5. Submit a pull request

## License

MIT License - see LICENSE file for details
