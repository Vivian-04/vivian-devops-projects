#!/bin/bash
# Integration test script: brings up stack, submits a job, verifies completion, tears down.
set -e

# Create .env from example if needed
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "=== Starting full stack ==="
docker compose up -d --build

echo "=== Waiting for services to be healthy (timeout: 90s) ==="
TIMEOUT=90
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  if curl -fs http://localhost:3000/health >/dev/null 2>&1 && \
     curl -fs http://localhost:8000/health >/dev/null 2>&1; then
    echo "All services healthy after ${ELAPSED}s"
    break
  fi
  sleep 3
  ELAPSED=$((ELAPSED + 3))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
  echo "ERROR: Services did not become healthy within ${TIMEOUT}s"
  docker compose ps
  docker compose logs
  docker compose down -v
  exit 1
fi

echo "=== Submitting a test job ==="
RESPONSE=$(curl -fsS -X POST http://localhost:3000/submit)
JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Submitted job: $JOB_ID"

echo "=== Polling for job completion (timeout: 60s) ==="
JOB_TIMEOUT=60
JOB_ELAPSED=0
while [ $JOB_ELAPSED -lt $JOB_TIMEOUT ]; do
  STATUS=$(curl -fsS "http://localhost:3000/status/$JOB_ID" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "=== SUCCESS: Job completed ==="
    docker compose down -v
    exit 0
  fi
  sleep 3
  JOB_ELAPSED=$((JOB_ELAPSED + 3))
done

echo "ERROR: Job did not complete within ${JOB_TIMEOUT}s"
docker compose logs worker
docker compose down -v
exit 1
