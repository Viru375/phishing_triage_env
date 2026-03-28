#!/bin/bash
set -e

echo "=== OpenEnv Hackathon Validation Script ==="

echo "1. Checking Python dependencies & openenv.yaml exists..."
if [ ! -f "openenv.yaml" ]; then
    echo "ERROR: openenv.yaml not found!"
    exit 1
fi

echo "2. Building Docker image..."
docker build -t phishing-triage-env .

echo "3. Running Docker container locally..."
docker run -d --name phishing-test -p 8000:8000 phishing-triage-env
sleep 3 # wait for fastAPI to start

echo "4. Pinging Health Endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if [[ "$HEALTH" != *"healthy"* ]]; then
    echo "ERROR: Health endpoint failed!"
    docker stop phishing-test && docker rm phishing-test
    exit 1
fi
echo "Health check passed: $HEALTH"

echo "5. Testing Baseline Script Execution (Local dry-run)"
python baseline.py

echo "6. Cleaning Up"
docker stop phishing-test
docker rm phishing-test

echo "=== Validation SUCCESS ==="
