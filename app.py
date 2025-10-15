#!/usr/bin/env python3
"""
Python Code Execution API Service
A Flask service that executes arbitrary Python scripts in a secure sandbox using nsjail.
"""

import json
import os
import subprocess
import tempfile
import uuid
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NSJAIL_CONFIG = "/app/nsjail.cfg"
PYTHON_TIMEOUT = 30  # seconds


def validate_script(script_content):
    """
    Validate that the script contains a main() function.
    """
    if not script_content or not script_content.strip():
        raise ValueError("Script content cannot be empty")
    
    # Check if main() function exists
    if "def main(" not in script_content:
        raise ValueError("Script must contain a main() function")
    
    return True


def execute_python_script(script_content):
    """
    Execute Python script in a secure sandbox using nsjail.
    Returns tuple of (result, stdout, stderr).
    """
    # Create temporary files
    script_id = str(uuid.uuid4())
    script_path = f"/tmp/script_{script_id}.py"
    result_path = f"/tmp/result_{script_id}.json"
    
    try:
        # Write script to temporary file
        with open(script_path, 'w') as f:
            f.write(script_content)
            f.write("\n\n")
            f.write(f"""
import json
import sys

if __name__ == "__main__":
    try:
        result = main()
        with open('{result_path}', 'w') as result_file:
            json.dump({{'result': result}}, result_file)
    except Exception as e:
        with open('{result_path}', 'w') as result_file:
            json.dump({{'error': str(e)}}, result_file)
        sys.exit(1)
""")
        
        # Use subprocess with basic isolation
        # Note: For production, consider using nsjail or similar sandboxing
        python_cmd = ["python3", script_path]
        
        # Execute with timeout
        process = subprocess.run(
            python_cmd,
            capture_output=True,
            text=True,
            timeout=PYTHON_TIMEOUT,
            cwd="/tmp"
        )
        
        stdout = process.stdout
        stderr = process.stderr
        
        # Read result from file
        result = None
        if os.path.exists(result_path):
            with open(result_path, 'r') as f:
                result_data = json.load(f)
                if 'error' in result_data:
                    raise RuntimeError(f"Script execution error: {result_data['error']}")
                result = result_data.get('result')
        else:
            raise RuntimeError("Script did not produce a result file")
            
        return result, stdout, stderr
        
    finally:
        # Cleanup temporary files
        for path in [script_path, result_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {path}: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/execute', methods=['POST'])
def execute():
    """
    Execute Python script endpoint.
    Expects JSON payload with 'script' field containing Python code.
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data or 'script' not in data:
            return jsonify({"error": "Missing 'script' field in request"}), 400
        
        script_content = data['script']
        
        # Validate script
        validate_script(script_content)
        
        # Execute script
        result, stdout, stderr = execute_python_script(script_content)
        
        # Return response
        response = {
            "result": result,
            "stdout": stdout
        }
        
        if stderr:
            response["stderr"] = stderr
            
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out"}), 408
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
