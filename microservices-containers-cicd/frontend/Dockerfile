# ---------- Stage 1: Builder ----------
FROM node:20-alpine AS builder

WORKDIR /build

# Copy dependency manifests first for layer caching
COPY package.json ./

# Install ALL dependencies (including dev) — but we only have prod deps here
RUN npm install --omit=dev && npm cache clean --force

# ---------- Stage 2: Runtime ----------
FROM node:20-alpine AS runtime

# Alpine's node image already has a non-root user named 'node'
# But we'll create our own to match convention
RUN addgroup -S -g 1001 appgroup \
    && adduser -S -u 1001 -G appgroup appuser \
    && apk add --no-cache wget

WORKDIR /app

# Copy only production node_modules from builder
COPY --from=builder --chown=appuser:appgroup /build/node_modules ./node_modules

# Copy application source
COPY --chown=appuser:appgroup app.js package.json ./
COPY --chown=appuser:appgroup views ./views

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "app.js"]
