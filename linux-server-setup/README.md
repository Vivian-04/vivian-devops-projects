# Linux Server Setup & Nginx Configuration

## Overview

A production-ready Ubuntu 22.04 server on AWS EC2 featuring:
- Hardened SSH configuration (key-based authentication only)
- Non-root user with sudo privileges
- UFW firewall (restricted to ports 22, 80, 443)
- Nginx web server with static file serving
- Let's Encrypt SSL certificate (HTTPS)
- HTTP → HTTPS 301 redirect

**Live Domain:** https://viviannduka.duckdns.org/

---

## Architecture

### Network Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET (User)                          │
│              Browser: viviannduka.duckdns.org                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  DNS Resolution │
                    │ (DuckDNS Service)
                    │   ↓ 56.228.5.190 │
                    └────────┬────────┘
                             │
                    ┌────────▼────────────────────┐
                    │  AWS EC2 Instance          │
                    │  (Ubuntu 22.04)            │
                    │  56.228.5.190              │
                    └────────┬────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │     UFW Firewall (Default: DENY)    │
          ├─ Port 22 (SSH, key-based)           │
          ├─ Port 80 (HTTP)                     │
          ├─ Port 443 (HTTPS)                   │
          └─ All others: BLOCKED                │
                             │
          ┌──────────────────┴──────────────────┐
          │       Nginx Web Server              │
          │      (/etc/nginx/)                  │
          └─────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ Port 80 │         │Port 443 │         │Port 22  │
   │  (HTTP) │         │(HTTPS)  │         │  (SSH)  │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                    │
        │                   │            hngdevops user
        │          ┌────────▼────────┐  (non-root)
        │          │  TLS/SSL Layer  │
        │          │ (Let's Encrypt)  │
        │          └────────┬────────┘
        │                   │
        │          ┌────────▼──────────┐
        │          │ Nginx Location    │
        │          │ Blocks            │
        │          ├─ location /       │
        │          ├─ location /api    │
        │          └─ try_files        │
        │                   │
        │          ┌────────▼─────────────┐
        │          │  Response Types      │
        └─────────→│ ├─ HTML (index.html) │
                   │ ├─ JSON (/api)       │
                   │ └─ 301 redirects     │
                   └──────────────────────┘
```

### Request Flow: User Types Domain

```
1. USER TYPES: https://viviannduka.duckdns.org/
                        ↓
2. DNS LOOKUP: "What's the IP for viviannduka.duckdns.org?"
                        ↓
3. DuckDNS RESPONSE: "56.228.5.190"
                        ↓
4. TCP CONNECTION: Browser → 56.228.5.190:443
                        ↓
5. TLS HANDSHAKE: 
   - Server sends Let's Encrypt certificate
   - Browser verifies: "Is this certificate valid?"
   - Both agree on encryption (TLS 1.2/1.3)
                        ↓
6. HTTP REQUEST: GET / HTTP/1.1
                        ↓
7. NGINX ROUTES: 
   - Checks location blocks
   - Matches "location /"
   - try_files $uri $uri/ =404
   - Finds /var/www/html/index.html
                        ↓
8. SERVER RESPONSE:
   HTTP/1.1 200 OK
   Content-Type: text/html
   [HTML content with "Vivian"]
                        ↓
9. BROWSER RENDERS: Shows page with username visible
```

### Security Layers Diagram

```
┌─────────────────────────────────────────────┐
│     LAYER 1: NETWORK SECURITY               │
│  UFW Firewall - Only 3 ports open           │
│  Everything else: BLOCKED                   │
│  (Reduces attack surface)                   │
└──────────┬──────────────────────────────────┘
           │
┌──────────▼────────────────────────────────────┐
│     LAYER 2: SSH SECURITY                     │
│  ✓ Key-based auth (no passwords)              │
│  ✓ Root login disabled                        │
│  ✓ Non-root user (hngdevops)                  │
│  ✓ Limited sudo (only sshd, ufw)              │
│  (Prevents unauthorized access)               │
└──────────┬───────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────┐
│     LAYER 3: DATA SECURITY                   │
│  ✓ HTTPS (encryption in transit)             │
│  ✓ Let's Encrypt certificate                 │
│  ✓ TLS 1.2+ only (no old protocols)          │
│  ✓ Strong ciphers (HIGH:!aNULL:!MD5)        │
│  (Protects data from eavesdropping)          │
└───────────────────────────────────────────────┘
```

---

## What This Project Teaches

### 1. Linux System Hardening

#### SSH Security
- **Problem:** SSH is a common attack vector. Default settings allow password guessing and root login.
- **Solution:**
  - `PermitRootLogin no` - Disable root SSH access
  - `PasswordAuthentication no` - Only allow keys, not passwords
  - `PubkeyAuthentication yes` - Require SSH keys
- **Why:** Keys are cryptographic (can't be brute-forced). Passwords can be guessed.

#### UFW Firewall
- **Problem:** Server is exposed to the internet on all ports. Attackers probe every port.
- **Solution:** 
  - Default: `DENY all incoming`
  - Allow only: ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
  - Block everything else
- **Why:** Minimize attack surface using principle of least privilege.

#### Non-Root User
- **Problem:** Using root for everything is dangerous. One mistake = entire system compromised.
- **Solution:**
  - Created user: `hngdevops`
  - Can use `sudo` for privileged commands
  - Normal operations run as non-root
- **Why:** Limited blast radius. If the user account is compromised, attacker doesn't have full system access.

---

### 2. Nginx Web Server

#### Server Blocks
Nginx can host multiple websites or configurations. Each is a "server block."
- HTTP (port 80) - Catches unencrypted traffic
- HTTPS (port 443) - Handles encrypted traffic

#### Location Blocks
Routes requests based on URL path:

```nginx
location / {
    # Handles: /, /about, /contact, etc.
    try_files $uri $uri/ =404;
    index index.html;
}

location /api {
    # Handles: /api specifically
    add_header Content-Type application/json;
    return 200 '{"message":"..."}';
}
```

#### HTTP → HTTPS Redirect
```nginx
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```
- Catches HTTP requests and redirects to HTTPS
- Uses 301 (permanent) not 302 (temporary)
- Ensures all traffic is encrypted

---

### 3. SSL/TLS Certificates

#### Why HTTPS?
- **HTTP:** Data visible to anyone on network (passwords, credit cards, etc.)
- **HTTPS:** Data encrypted end-to-end. Only browser and server can read it.

#### Let's Encrypt
- Provides free SSL certificates (no $ required)
- Certbot automates the process:
  1. Proves you own the domain (DNS verification)
  2. Gets certificate
  3. Auto-renews every 90 days

**Certificate Files:**
- `fullchain.pem` = Public certificate (browser verifies server)
- `privkey.pem` = Private key (server uses to decrypt messages)

#### Protocols & Ciphers
```nginx
ssl_protocols TLSv1.2 TLSv1.3;      # Modern only, no old SSL
ssl_ciphers HIGH:!aNULL:!MD5;       # Strong algorithms only
ssl_prefer_server_ciphers on;       # Server chooses, not browser
```
- Old SSL/TLS versions have known vulnerabilities
- Only support modern, secure versions

---

### 4. Debugging: Symlinks & Config Files

#### The Issue We Encountered
Had two Nginx configs:
- `sites-available/hng` (old, tried to proxy to port 3000)
- `sites-available/default` (new, serves static files)

Symlink pointed to wrong file → Nginx used old config → 502 error.

#### The Solution
```
Nginx reads from: /etc/nginx/sites-enabled/
To enable config: Create symlink from sites-available → sites-enabled
To disable config: Remove symlink (not the original file!)
To debug: Check which symlinks exist, verify they point to correct files
```

---

## Setup Process

### Phase 1: EC2 Instance
1. Launch Ubuntu 22.04 on AWS Free Tier
2. t2.micro instance
3. Copy public IP address

### Phase 2: SSH Hardening
1. Update system packages
2. Create hngdevops user
3. Copy SSH key to hngdevops
4. Edit `/etc/ssh/sshd_config`:
   - `PermitRootLogin no`
   - `PasswordAuthentication no`
   - `PubkeyAuthentication yes`
5. Restart SSH service

### Phase 3: UFW Firewall
1. Enable UFW
2. Allow ports: 22, 80, 443
3. Default deny incoming

### Phase 4: Nginx Installation
1. Install nginx
2. Create `/var/www/html/index.html` with username
3. Configure `/etc/nginx/sites-available/default`:
   - HTTP redirect to HTTPS (301)
   - Location / serves static HTML
   - Location /api returns JSON
4. Enable site: `ln -s sites-available/default sites-enabled/default`

### Phase 5: SSL Certificate
1. Update DuckDNS with server IP
2. Run certbot: `sudo certbot certonly --standalone -d viviannduka.duckdns.org`
3. Configure Nginx with certificate paths
4. Reload Nginx

### Phase 6: Testing
```bash
# HTTP redirect
curl -i http://viviannduka.duckdns.org/
# Returns: 301 Moved Permanently

# HTTPS homepage
curl https://viviannduka.duckdns.org/
# Returns: HTML page with "Vivian"

# HTTPS API
curl https://viviannduka.duckdns.org/api
# Returns: {"message":"HNGI14 Stage 0","track":"DevOps","username":"Vivian"}
```

---

## Key Nginx Config

```nginx
# HTTP Server (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS Server (main site)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;
    
    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/viviannduka.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/viviannduka.duckdns.org/privkey.pem;
    
    # Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Root directory for files
    root /var/www/html;
    
    # Serve static HTML
    location / {
        try_files $uri $uri/ =404;
        index index.html;
    }
    
    # JSON API endpoint
    location /api {
        add_header Content-Type application/json;
        return 200 '{"message":"HNGI14 Stage 0","track":"DevOps","username":"Vivian"}';
    }
}
```

---

## Security Checklist

- [x] Root SSH disabled
- [x] Password SSH disabled
- [x] Key-based SSH only
- [x] UFW firewall active
- [x] Only ports 22, 80, 443 open
- [x] Non-root user with sudo
- [x] HTTPS with valid certificate
- [x] HTTP redirects to HTTPS (301)
- [x] Modern TLS only (1.2+)
- [x] Strong ciphers

---

## Tools Used

- **Cloud:** AWS EC2
- **OS:** Ubuntu 22.04
- **Web Server:** Nginx 1.24
- **SSL:** Let's Encrypt + Certbot
- **Firewall:** UFW
- **Domain:** DuckDNS

---

## What I Learned

✅ Linux security best practices
✅ How web requests travel (DNS → IP → Port → Service)
✅ Nginx configuration and routing
✅ SSL/TLS and HTTPS
✅ UFW firewall basics
✅ Debugging web server issues (checking logs, configs, symlinks)
✅ Git & GitHub workflow

---

## Status

✅ **Complete and tested**

All endpoints working. Server is hardened and secure.
