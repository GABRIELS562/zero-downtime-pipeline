#!/usr/bin/env python3
"""
Simplified main entry point for testing
"""
import sys
import os

print("=== Finance App Startup Test ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Directory contents:")
os.system("ls -la")

# Test basic imports
try:
    print("\nTesting FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

# Create minimal app
app = FastAPI(title="Finance Test App")

@app.get("/")
def read_root():
    return {"status": "ok", "app": "finance-trading-test"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)