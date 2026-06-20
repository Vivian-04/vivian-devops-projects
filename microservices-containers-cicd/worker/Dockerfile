# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

RUN groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --no-create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app

COPY --chown=appuser:appgroup worker.py healthcheck.py ./

USER appuser

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

CMD ["python", "-u", "worker.py"]
