# ChiliHead OpsManager v2.1 - Custom Open-WebUI Build
# Extends Open-WebUI with Email Client and Settings tabs integrated into the platform

FROM nginx:alpine AS static-server

# Copy ChiliHead static interface
COPY static/ /usr/share/nginx/html/

# Create nginx config to proxy Open-WebUI and serve ChiliHead
RUN echo 'server { \
    listen 3040; \
    server_name localhost; \
    \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /api { \
        proxy_pass http://chilihead-openwebui-backend:8080; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
    \
    location /openwebui/ { \
        proxy_pass http://chilihead-openwebui-backend:8080/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 3040
EXPOSE 3040

CMD ["nginx", "-g", "daemon off;"]
