# HNG Stage 2 DevOps - Dockerized Microservices with CI/CD

A multi-service job processing system built with **FastAPI**, **Node.js**, **Redis**, and **Python**, fully containerized with Docker Compose and backed by a production-grade GitHub Actions CI/CD pipeline.

**Submitted by:** Vivian Nduka (GitHub: [@Vivian-04](https://github.com/Vivian-04))

---

## Architecture

Four services communicate over a private Docker network:

| Service    | Tech           | Port  | Purpose                                         |
| ---------- | -------------- | ----- | ----------------------------------------------- |
| `frontend` | Node.js 20     | 3000  | HTTP gateway that submits and queries jobs      |
| `api`      | FastAPI        | 8000  | Accepts jobs, stores them in Redis              |
| `worker`   | Python         | —     | Polls Redis, processes jobs, updates status     |
| `redis`    | Redis 7 Alpine | (int) | Job queue and state store (not exposed to host) |

**Flow:** User hits `frontend:3000/submit` → `frontend` calls `api:8000/submit` → `api` writes job to Redis → `worker` polls Redis, processes job, writes result back → user polls `frontend:3000/status/<id>` to see completion.

---

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2
- Git

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Vivian-04/hng14-stage2-devops.git
cd hng14-stage2-devops

# Create a .env file from the example
cp .env.example .env

# Build and start the stack
docker compose up -d --build

# Verify all services are healthy
docker compose ps
```

Expected output: all four services with `(healthy)` status.

---

## Usage

**Submit a job:**

```bash
curl -X POST http://localhost:3000/submit
# -> {"job_id": "abc123"}
```

**Check job status:**

```bash
curl http://localhost:3000/status/abc123
# -> {"job_id": "abc123", "status": "completed", "result": "..."}
```

**Health checks:**

```bash
curl http://localhost:3000/health    # Frontend
curl http://localhost:8000/health    # API (also pings Redis)
```

---

## Endpoints

### Frontend (`localhost:3000`)

| Method | Path           | Description                            |
| ------ | -------------- | -------------------------------------- |
| GET    | `/health`      | Frontend liveness check                |
| POST   | `/submit`      | Submit a new job, returns `job_id`     |
| GET    | `/status/:id`  | Get current status of a job            |

### API (`localhost:8000`)

| Method | Path           | Description                                |
| ------ | -------------- | ------------------------------------------ |
| GET    | `/health`      | API + Redis connectivity check             |
| POST   | `/submit`      | Internal: create a job record in Redis     |
| GET    | `/status/:id`  | Internal: fetch job state from Redis (404 if not found) |

---

## Environment Variables

See `.env.example` for the full list. Key variables:

- `REDIS_HOST` — Redis hostname (default: `redis`)
- `REDIS_PORT` — Redis port (default: `6379`)
- `API_URL` — How the frontend reaches the API (default: `http://api:8000`)
- `API_PORT` — API service port (default: `8000`)
- `FRONTEND_PORT` — Frontend port (default: `3000`)
- `APP_ENV` — Environment tag (default: `production`)

---

## CI/CD Pipeline

Every push to `main` triggers `.github/workflows/ci.yml`, which runs **6 stages in strict order**:

1. **Lint** — `flake8` (Python), `eslint` (JS), `hadolint` (all 3 Dockerfiles)
2. **Test** — `pytest` with coverage; Redis is mocked so tests run hermetically
3. **Build** — Multi-stage builds of api, worker, frontend images pushed to a local registry
4. **Security scan** — Trivy scans all 3 images for CRITICAL vulnerabilities (SARIF uploaded as artifact)
5. **Integration test** — Full stack brought up via `docker compose`; a real job is submitted and polled until `completed`
6. **Deploy** — Simulated rolling update with 60s health-check window; aborts on health failure (runs on `main` only)

Each stage blocks the next via `needs:` — failures halt the pipeline.

---

## Local Development

**Run tests:**

```bash
cd api
pip install -r requirements-dev.txt
pytest tests/ -v --cov=main
```

**Run linters:**

```bash
flake8 api/ worker/
cd frontend && npx eslint app.js
```

**Rebuild a single service:**

```bash
docker compose up -d --build api
```

---

## Troubleshooting

**Services not healthy?**

```bash
docker compose ps            # See status of each service
docker compose logs <svc>    # Check logs for a specific service
docker compose down -v       # Nuke everything and start fresh
```

**Port 3000 or 8000 already in use?**  
Change `FRONTEND_PORT` or `API_PORT` in `.env` before running `docker compose up`.

**Redis connection errors?**  
Ensure `REDIS_HOST=redis` in `.env` (not `localhost`) — services communicate via the Docker network, not the host.

---

## Project Structure
Bug fixes applied to the original starter code are documented in [`FIXES.md`](./FIXES.md).
