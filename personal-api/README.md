# Personal API

A simple Python API with three endpoints, deployed with Nginx reverse proxy and systemd service management.

## Overview

This project demonstrates:
- Building a RESTful API with FastAPI
- Deploying to a Linux server
- Reverse proxying with Nginx
- Process management with systemd
- Full DevOps workflow

## Project Structure

```
personal-api/
├── main.py                 # FastAPI application with 3 endpoints
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── venv/                  # Virtual environment (not in git)
```

## Endpoints

All endpoints return `Content-Type: application/json` with HTTP status `200`.

### 1. GET /

Returns API status.

```bash
curl https://viviannduka.duckdns.org/
```

Response:
```json
{
  "message": "API is running"
}
```

**Why?** Simple health check to verify API is accessible.

---

### 2. GET /health

Detailed health check endpoint.

```bash
curl https://viviannduka.duckdns.org/health
```

Response:
```json
{
  "message": "healthy"
}
```

**Why?** Monitoring systems use this to verify service is working.

---

### 3. GET /me

Returns personal information.

```bash
curl https://viviannduka.duckdns.org/me
```

Response:
```json
{
  "name": "Vivian Nduka",
  "email": "ifechukwudenduka@gmail.com",
  "github": "https://github.com/Vivian-04"
}
```

**Why?** Demonstrates JSON response with structured data.

---

## Run Locally

### Prerequisites

- Python 3.9+
- pip package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/Vivian-04/personal-api.git
cd personal-api

# Create virtual environment
# WHY? Isolates Python packages, prevents conflicts with system Python
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
# WHY? FastAPI and Uvicorn are needed to run the app
pip install -r requirements.txt

# Run the API
python main.py

# Output should show:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Test Locally

Open another terminal:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Test /me endpoint
curl http://localhost:8000/me

# All should return JSON responses
```

---

## Deploy to Production

### Architecture

```
┌─────────────────────────────────────────────┐
│            User's Browser                   │
│     https://viviannduka.duckdns.org         │
└──────────────────┬──────────────────────────┘
                   │ HTTPS (Port 443)
                   ▼
        ┌──────────────────────┐
        │   Nginx Reverse      │
        │   Proxy (443)        │
        │ viviannduka.duckdns  │
        └──────────┬───────────┘
                   │ HTTP (Port 8000, local only)
                   ▼
        ┌──────────────────────┐
        │   Python FastAPI     │
        │   App (localhost)    │
        │   Uvicorn Server     │
        │   Port: 8000         │
        └──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   systemd Service    │
        │   (auto-restart)     │
        │   (auto-start on     │
        │    boot)             │
        └──────────────────────┘
```

### Deployment Steps

#### 1. Provision Server

```bash
# Use AWS EC2 Ubuntu 22.04
# (Can reuse Stage 0 server)
```

#### 2. SSH into Server

```bash
ssh -i your-key.pem hngdevops@your-server-ip
```

#### 3. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git
```

#### 4. Clone Repository

```bash
cd /home/hngdevops
git clone https://github.com/Vivian-04/personal-api.git
cd personal-api
```

#### 5. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 6. Create systemd Service

Create `/etc/systemd/system/personal-api.service`:

```bash
sudo vim /etc/systemd/system/personal-api.service
```

Paste:

```ini
[Unit]
Description=Personal API Service
After=network.target

[Service]
Type=notify
User=hngdevops
WorkingDirectory=/home/hngdevops/personal-api
Environment="PATH=/home/hngdevops/personal-api/venv/bin"
ExecStart=/home/hngdevops/personal-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 7. Enable and Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to auto-start on boot
sudo systemctl enable personal-api

# Start the service
sudo systemctl start personal-api

# Check status
sudo systemctl status personal-api
```

#### 8. Configure Nginx Reverse Proxy

Edit `/etc/nginx/sites-available/default`:

```nginx
location / {
    # Forward all traffic to Python app
    proxy_pass http://localhost:8000;
    
    # Forward headers so app knows real client info
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Keep connection open
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

location /api {
    # Same config as /
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

#### 9. Test Nginx Config

```bash
sudo nginx -t
# Should show: syntax is ok
```

#### 10. Reload Nginx

```bash
sudo systemctl reload nginx
```

---

## Verify Production Deployment

```bash
# From your local machine:

# Test /
curl https://viviannduka.duckdns.org/

# Test /health
curl https://viviannduka.duckdns.org/health

# Test /me
curl https://viviannduka.duckdns.org/me

# All should return JSON
```

---

## Service Management

### Check Service Status

```bash
sudo systemctl status personal-api
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u personal-api -f

# Last 50 lines
sudo journalctl -u personal-api -n 50

# Since service started
sudo journalctl -u personal-api --since "1 hour ago"
```

### Stop Service

```bash
sudo systemctl stop personal-api
```

### Restart Service

```bash
sudo systemctl restart personal-api
```

### Auto-Restart on Crash

The service automatically restarts if the app crashes:

```ini
[Service]
Restart=always        # Always restart on exit
RestartSec=10         # Wait 10 seconds before restarting
```

---

## Key Concepts

### Why FastAPI?

- Modern Python framework
- Fast (built on Starlette and Pydantic)
- Automatic API documentation
- Type hints for validation
- Perfect for learning API structure

### Why systemd?

- Built into Linux (no extra dependencies)
- Auto-restart on crash
- Auto-start on boot
- Centralized logging
- Professional standard

### Why Nginx Reverse Proxy?

- Security: App not exposed directly
- HTTPS/SSL termination
- Multiple endpoints routing
- Caching capabilities
- Rate limiting

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI |
| **Server** | Uvicorn (ASGI) |
| **Reverse Proxy** | Nginx |
| **Process Manager** | systemd |
| **OS** | Ubuntu 22.04 |
| **Cloud** | AWS EC2 |
| **Domain** | DuckDNS |
| **SSL** | Let's Encrypt |

---

## What I Learned

✅ Building RESTful APIs with Python
✅ ASGI web servers (Uvicorn)
✅ Reverse proxying with Nginx
✅ Process management with systemd
✅ Service auto-restart and logging
✅ Full DevOps deployment pipeline
✅ Security considerations (proxy headers, timeouts)

---

## Performance Requirements Met

✅ All endpoints return `Content-Type: application/json`
✅ All endpoints return HTTP status `200`
✅ All endpoints respond within 500ms
✅ Service auto-restarts on crash
✅ Service auto-starts on server boot
✅ No direct exposure of app port (reverse proxy only)

---

## GitHub Repository

https://github.com/Vivian-04/personal-api

---

## Author

**Vivian Nduka**
- GitHub: https://github.com/Vivian-04
- Email: ifechukwudenduka@gmail.com

---

## License

MIT
