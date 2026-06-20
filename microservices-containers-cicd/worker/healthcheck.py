import redis
import os
import sys
import time

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_timeout=3)
    heartbeat = r.get("worker:heartbeat")
    if heartbeat is None:
        print("No heartbeat found")
        sys.exit(1)
    age = int(time.time()) - int(heartbeat)
    if age > 30:
        print(f"Heartbeat stale ({age}s old)")
        sys.exit(1)
    print("Healthy")
    sys.exit(0)
except Exception as e:
    print(f"Healthcheck failed: {e}")
    sys.exit(1)
