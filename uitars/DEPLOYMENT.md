# UI-TARS Deployment Guide

Complete deployment instructions for the UI-TARS monitoring dashboard.

## Quick Start

### Local Development

```bash
# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env with your Dolphin service URL

# 3. Start development server
npm start

# Access at http://localhost:3000
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:3000
```

## Production Deployment

### Option 1: Docker (Recommended)

```bash
# Build production image
docker build -t uitars:1.0.0 .

# Run container
docker run -d \
  --name uitars \
  -p 80:80 \
  -e REACT_APP_WS_URL=ws://your-dolphin-service:8080/ws \
  -e REACT_APP_API_URL=http://your-dolphin-service:8080/api \
  --restart unless-stopped \
  uitars:1.0.0

# Check health
curl http://localhost/health
```

### Option 2: Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uitars
  labels:
    app: uitars
spec:
  replicas: 3
  selector:
    matchLabels:
      app: uitars
  template:
    metadata:
      labels:
        app: uitars
    spec:
      containers:
      - name: uitars
        image: uitars:1.0.0
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_WS_URL
          value: "ws://dolphin-service:8080/ws"
        - name: REACT_APP_API_URL
          value: "http://dolphin-service:8080/api"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: uitars-service
spec:
  selector:
    app: uitars
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

Apply with:
```bash
kubectl apply -f deployment.yaml
```

### Option 3: Traditional Server (Nginx)

```bash
# Build static files
npm run build

# Copy to web server
scp -r build/* user@server:/var/www/uitars/

# Configure Nginx
# See nginx-server.conf below
```

**nginx-server.conf:**
```nginx
server {
    listen 80;
    server_name uitars.yourdomain.com;

    root /var/www/uitars;
    index index.html;

    # Enable gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Proxy WebSocket to Dolphin
    location /ws {
        proxy_pass http://dolphin-backend:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Proxy API to Dolphin
    location /api {
        proxy_pass http://dolphin-backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # React app
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Environment Configuration

### Production Environment Variables

Create `.env.production` or set environment variables:

```bash
# Production Dolphin service
REACT_APP_WS_URL=wss://dolphin.yourdomain.com/ws
REACT_APP_API_URL=https://dolphin.yourdomain.com/api

# Reconnection settings (production)
REACT_APP_WS_RECONNECT_INTERVAL=5000
REACT_APP_WS_MAX_RECONNECT=20

# UI settings
REACT_APP_MAX_EXECUTIONS=500
REACT_APP_LOG_RETENTION_MS=7200000  # 2 hours

# Disable debug in production
REACT_APP_DEBUG=false

# Enable performance monitoring
REACT_APP_PERF_MONITORING=true
```

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d uitars.yourdomain.com

# Auto-renewal is configured automatically
```

### Using Custom Certificates

```nginx
server {
    listen 443 ssl http2;
    server_name uitars.yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name uitars.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring and Observability

### Health Checks

```bash
# Simple health check
curl http://localhost/health

# Expected response: "healthy"
```

### Docker Health Check

Already configured in Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1
```

### Kubernetes Probes

Liveness and readiness probes are configured in the deployment YAML above.

### Logging

```bash
# Docker logs
docker logs -f uitars

# Kubernetes logs
kubectl logs -f deployment/uitars

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

## Performance Optimization

### CDN Configuration

For static assets, consider using a CDN:

1. Build the app: `npm run build`
2. Upload `build/static/*` to CDN
3. Update `index.html` to reference CDN URLs

### Caching Strategy

- HTML: No cache (to get latest app version)
- JS/CSS: 1 year (files have content hashes)
- Images: 1 year (versioned by content)

### Compression

Nginx configuration includes gzip compression. For even better compression:

```nginx
# Enable Brotli (if module available)
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/javascript application/json;
```

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
# docker-compose with replicas
version: '3.8'
services:
  uitars:
    image: uitars:1.0.0
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### Load Balancer Configuration

Example HAProxy config:
```
frontend uitars_front
    bind *:80
    default_backend uitars_back

backend uitars_back
    balance roundrobin
    server uitars1 10.0.1.10:80 check
    server uitars2 10.0.1.11:80 check
    server uitars3 10.0.1.12:80 check
```

## Troubleshooting

### WebSocket Connection Fails

1. Check Dolphin service is accessible
2. Verify WebSocket URL in browser console
3. Check for proxy/firewall blocking WebSocket
4. Ensure correct protocol (ws:// vs wss://)

**Debug:**
```javascript
// In browser console
console.log(process.env.REACT_APP_WS_URL)
```

### CORS Issues

If API calls fail, configure CORS on Dolphin service:
```go
// In Dolphin service
w.Header().Set("Access-Control-Allow-Origin", "https://uitars.yourdomain.com")
w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
```

### Blank Page After Deployment

1. Check browser console for errors
2. Verify `package.json` `homepage` field (if using subdirectory)
3. Check Nginx `try_files` configuration
4. Verify all static assets are accessible

**Debug:**
```bash
# Check if static files are accessible
curl -I http://localhost/static/js/main.*.js

# Should return 200 OK
```

### High Memory Usage

If container uses too much memory:

```yaml
# Limit container memory
services:
  uitars:
    image: uitars:1.0.0
    deploy:
      resources:
        limits:
          memory: 256M
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup environment config
cp .env .env.backup

# Backup Nginx config
cp /etc/nginx/sites-available/uitars /backup/nginx-uitars.conf
```

### Rollback Procedure

```bash
# Docker rollback
docker tag uitars:1.0.0 uitars:rollback
docker pull uitars:previous-version
docker tag uitars:previous-version uitars:1.0.0
docker-compose up -d

# Kubernetes rollback
kubectl rollout undo deployment/uitars
```

## Updates and Maintenance

### Updating UI-TARS

```bash
# 1. Build new version
docker build -t uitars:1.1.0 .

# 2. Tag as latest
docker tag uitars:1.1.0 uitars:latest

# 3. Rolling update (Docker Swarm)
docker service update --image uitars:1.1.0 uitars_service

# 4. Rolling update (Kubernetes)
kubectl set image deployment/uitars uitars=uitars:1.1.0
kubectl rollout status deployment/uitars
```

### Zero-Downtime Deployment

Use blue-green or canary deployments:

```bash
# Kubernetes canary deployment
kubectl apply -f deployment-canary.yaml
# Monitor for issues
# If OK, update main deployment
kubectl apply -f deployment.yaml
# Remove canary
kubectl delete -f deployment-canary.yaml
```

## Security Best Practices

1. **Always use HTTPS** in production
2. **Set security headers** (already configured in nginx.conf)
3. **Keep dependencies updated**: `npm audit fix`
4. **Use environment variables** for secrets
5. **Restrict network access** to Dolphin service
6. **Enable rate limiting** on API endpoints
7. **Regular security scans**: `npm audit`

## Support

For issues or questions:
- Check troubleshooting section above
- Review browser console for errors
- Check server logs
- Verify Dolphin service is functioning
- Ensure network connectivity between UI-TARS and Dolphin

## License

MIT
