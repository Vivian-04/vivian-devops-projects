# FIXES.md

This document lists every bug found in the starter repository and how each was fixed.

---

## Bug 1: Environment file with secrets committed to repository
- **File:** `api/.env`
- **Line:** Entire file (committed across git history)
- **Problem:** The file contained `REDIS_PASSWORD=supersecretpassword123` and `APP_ENV=production`. Committing secrets to version control exposes them publicly and violates the task requirement that `.env` must never appear in the repository or its history.
- **Fix:** Deleted `api/.env`, created a root-level `.gitignore` that excludes all `.env` files, created `.env.example` with placeholder values, and purged the file from git history using `git filter-repo`.

---

## Bug 2: Hardcoded Redis host in API
- **File:** `api/main.py`
- **Line:** 6
- **Problem:** `redis.Redis(host="localhost", port=6379)` hardcodes `localhost`, which breaks inside Docker because Redis runs in a separate container reachable by its service name.
- **Fix:** Read `REDIS_HOST` and `REDIS_PORT` from environment variables with sensible defaults (`redis` and `6379`).

---

## Bug 3: API missing /health endpoint
- **File:** `api/main.py`
- **Line:** N/A (endpoint missing entirely)
- **Problem:** Docker's `HEALTHCHECK` instruction requires an endpoint that returns successfully when the service is healthy. Without it, the container can never report healthy status.
- **Fix:** Added a `GET /health` endpoint that pings Redis and returns HTTP 200 with `{"status": "healthy"}` on success, 503 on Redis failure.

---

## Bug 4: API returns wrong status code for missing jobs
- **File:** `api/main.py`
- **Line:** 16-18
- **Problem:** When a job is not found, the API returns HTTP 200 with `{"error": "not found"}`. A missing resource must return HTTP 404.
- **Fix:** Replaced the dict return with `raise HTTPException(status_code=404, detail="job not found")`.

---

## Bug 5: Unused import in API
- **File:** `api/main.py`
- **Line:** 4
- **Problem:** `import os` was present but never used, which flake8 flags as F401 and fails lint checks.
- **Fix:** The `os` module is now actually used to read environment variables, so the import is justified.

---

## Bug 6: API dependencies have no version pinning
- **File:** `api/requirements.txt`
- **Line:** 1-3
- **Problem:** Dependencies were listed without versions (`fastapi`, `uvicorn`, `redis`). This produces non-reproducible builds — a build today may succeed and tomorrow may fail if upstream releases a breaking change.
- **Fix:** Pinned exact versions: `fastapi==0.109.0`, `uvicorn[standard]==0.27.0`, `redis==5.0.1`.

---

## Bug 7: Hardcoded Redis host in worker
- **File:** `worker/worker.py`
- **Line:** 5
- **Problem:** Same as Bug 2 — `redis.Redis(host="localhost", port=6379)` hardcoded in the worker, which fails inside Docker.
- **Fix:** Read `REDIS_HOST` and `REDIS_PORT` from environment variables.

---

## Bug 8: Worker has no graceful shutdown handling
- **File:** `worker/worker.py`
- **Line:** 4 (`import signal` was imported but never used)
- **Problem:** The worker runs `while True:` with no signal handlers. When Docker sends SIGTERM during `docker stop`, the worker is killed mid-job, potentially leaving jobs in an inconsistent state.
- **Fix:** Registered `SIGTERM` and `SIGINT` handlers that set a `running` flag to `False`, allowing the main loop to finish the current iteration and exit cleanly.

---

## Bug 9: Worker has no error handling around job processing
- **File:** `worker/worker.py`
- **Line:** Entire main loop
- **Problem:** If `process_job` raises an exception (e.g. Redis disconnect mid-job), the entire worker process crashes and no further jobs are processed.
- **Fix:** Wrapped `process_job` in a try/except that logs the error, marks the job as `failed` in Redis, and continues processing. Also added an outer try/except for Redis connection errors with a retry-with-backoff pattern.

---

## Bug 10: Worker has no healthcheck mechanism
- **File:** `worker/worker.py`
- **Line:** N/A (feature missing entirely)
- **Problem:** The worker has no HTTP endpoint, so there was no way for Docker to verify it is alive.
- **Fix:** Added a heartbeat that writes the current timestamp to Redis key `worker:heartbeat` on every loop iteration (30s expiry). Created `worker/healthcheck.py` — a script Docker's `HEALTHCHECK` runs that reads the key and verifies the age is under 30 seconds.

---

## Bug 11: Worker dependencies have no version pinning
- **File:** `worker/requirements.txt`
- **Line:** 1
- **Problem:** Dependencies listed without versions produces non-reproducible builds.
- **Fix:** Pinned to `redis==5.0.1`.

---

## Bug 12: Hardcoded API URL in frontend
- **File:** `frontend/app.js`
- **Line:** 5
- **Problem:** `const API_URL = "http://localhost:8000";` hardcodes localhost, which fails inside Docker where the API is reachable as `http://api:8000` on the internal network.
- **Fix:** Changed to `process.env.API_URL || 'http://api:8000'` — reads from environment with a sensible default.

---

## Bug 13: Frontend missing /health endpoint
- **File:** `frontend/app.js`
- **Line:** N/A (endpoint missing)
- **Problem:** Same issue as Bug 3 — Docker's `HEALTHCHECK` requires an endpoint to probe.
- **Fix:** Added `GET /health` returning HTTP 200 with `{"status": "healthy"}`.

---

## Bug 14: Frontend port hardcoded
- **File:** `frontend/app.js`
- **Line:** 22
- **Problem:** `app.listen(3000, ...)` hardcodes the port, making it impossible to configure the service via environment variables as required by the task.
- **Fix:** Read `PORT` from environment with a default of `3000`.

---

## Bug 15: README is essentially empty
- **File:** `README.md`
- **Line:** Entire file (only 22 bytes)
- **Problem:** The task requires a README that explains prerequisites, setup, and successful startup. The original contained only a placeholder.
- **Fix:** Wrote a complete README covering prerequisites, cloning, environment setup, startup commands, expected output, endpoint documentation, and troubleshooting.
