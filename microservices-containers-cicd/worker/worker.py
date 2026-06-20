import redis
import time
import os
import signal
import sys

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

running = True


def shutdown_handler(signum, frame):
    global running
    print(f"Received signal {signum}, shutting down gracefully...")
    running = False


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


def process_job(job_id):
    print(f"Processing job {job_id}")
    time.sleep(2)
    r.hset(f"job:{job_id}", "status", "completed")
    print(f"Done: {job_id}")


def heartbeat():
    r.set("worker:heartbeat", int(time.time()), ex=30)


def main():
    print(f"Worker starting, connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
    while running:
        try:
            heartbeat()
            job = r.brpop("job", timeout=5)
            if job:
                _, job_id = job
                try:
                    process_job(job_id)
                except Exception as e:
                    print(f"Error processing job {job_id}: {e}")
                    r.hset(f"job:{job_id}", "status", "failed")
        except redis.ConnectionError as e:
            print(f"Redis connection error: {e}, retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)
    print("Worker shut down cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
