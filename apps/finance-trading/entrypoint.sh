#!/bin/bash
set -e

echo "Starting Finance Trading App..."
echo "PYTHONPATH: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Checking Python imports..."
python3 -c "import sys; print('Python path:', sys.path)"

echo "Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8001