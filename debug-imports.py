#!/usr/bin/env python3
"""
Debug script to test import paths
"""
import sys
import os

print("=== Import Path Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"sys.path: {sys.path}")

# Test pharma app imports
print("\n=== Testing Pharma App Imports ===")
try:
    sys.path.insert(0, '/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing')
    print("Added pharma app to path")
    
    # Try importing the main app
    from src.main import app as pharma_app
    print("✅ Successfully imported pharma app")
except Exception as e:
    print(f"❌ Failed to import pharma app: {e}")

# Test finance app imports  
print("\n=== Testing Finance App Imports ===")
try:
    sys.path.insert(0, '/Users/user/zero-downtime-pipeline/apps/finance-trading')
    print("Added finance app to path")
    
    # Try importing the main app
    from src.main import app as finance_app
    print("✅ Successfully imported finance app")
except Exception as e:
    print(f"❌ Failed to import finance app: {e}")

print("\n=== Testing Module Resolution ===")
# Test if src.models can be found
try:
    from src.models import manufacturing
    print("✅ Can import src.models.manufacturing")
except Exception as e:
    print(f"❌ Cannot import src.models.manufacturing: {e}")

print("\nTo fix import issues:")
print("1. Ensure PYTHONPATH=/app is set in Docker")
print("2. All imports should use 'src.' prefix")
print("3. Working directory should be /app in container")