#!/usr/bin/env python3
"""
Test scripts for the Python execution API
"""

# Test script 1: Simple return
simple_script = '''
def main():
    return {"message": "Hello, World!", "status": "success"}
'''

# Test script 2: Using libraries
library_script = '''
import numpy as np
import pandas as pd
import os

def main():
    # Test numpy
    arr = np.array([1, 2, 3, 4, 5])
    mean_val = float(np.mean(arr))
    
    # Test pandas
    df = pd.DataFrame({"values": [1, 2, 3, 4, 5]})
    sum_val = int(df["values"].sum())
    
    # Test os
    current_dir = os.getcwd()
    
    return {
        "numpy_mean": mean_val,
        "pandas_sum": sum_val,
        "current_directory": current_dir,
        "libraries_working": True
    }
'''

# Test script 3: With print statements
print_script = '''
def main():
    print("Starting execution...")
    print("Processing data...")
    
    result = {"processed_items": 10, "success": True}
    print(f"Processed {result['processed_items']} items successfully")
    
    return result
'''

# Test script 4: Error case - no main function
no_main_script = '''
def hello():
    return "This should fail"

x = 42
'''

# Test script 5: Error case - main function with error
error_script = '''
def main():
    return 1 / 0  # This will cause a division by zero error
'''

if __name__ == "__main__":
    import requests
    import json
    
    # Test against local server
    base_url = "http://localhost:8080"
    
    test_cases = [
        ("Simple Script", simple_script),
        ("Library Script", library_script), 
        ("Print Script", print_script),
        ("No Main Function", no_main_script),
        ("Error Script", error_script)
    ]
    
    print("Testing Python Execution API")
    print("=" * 40)
    
    for name, script in test_cases:
        print(f"\nTesting: {name}")
        print("-" * 20)
        
        try:
            response = requests.post(
                f"{base_url}/execute",
                json={"script": script},
                timeout=60
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
