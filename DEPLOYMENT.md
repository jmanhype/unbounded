# Unbounded Deployment Guide

## Table of Contents
1. [Development Deployment](#development-deployment)
2. [Production Deployment](#production-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [External Services](#external-services)
6. [Monitoring](#monitoring)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## Development Deployment

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- Ollama

### Local Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/unbounded.git
   cd unbounded
   ```

2. Set up environment:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. Start Ollama:
   ```bash
   ollama serve
   ollama pull llama2
   ```

4. Start services:
   ```bash
   docker compose up -d
   ```

5. Initialize database:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

## Production Deployment

### Prerequisites
- Linux server (Ubuntu 22.04 LTS recommended)
- Docker and Docker Compose
- Nginx
- SSL certificate
- Domain name

### Server Setup

1. Update system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install dependencies:
   ```bash
   sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx
   ```

3. Configure firewall:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

### Application Deployment

1. Clone repository:
   ```bash
   git clone https://github.com/yourusername/unbounded.git
   cd unbounded
   ```

2. Configure environment:
   ```bash
   cp .env.template .env.prod
   # Edit .env.prod with production values
   ```

3. Create docker-compose.prod.yml:
   ```yaml
   version: '3.8'
   services:
     backend:
       build: 
         context: ./backend
         dockerfile: Dockerfile.prod
       environment:
         - ENVIRONMENT=production
       restart: always
       depends_on:
         - db
       networks:
         - internal

     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile.prod
       restart: always
       networks:
         - internal

     db:
       image: postgres:15
       volumes:
         - postgres_data:/var/lib/postgresql/data
       networks:
         - internal
       restart: always

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - frontend
         - backend
       networks:
         - internal
       restart: always

   volumes:
     postgres_data:

   networks:
     internal:
   ```

4. Configure Nginx:
   ```nginx
   # nginx.conf
   events {
       worker_connections 1024;
   }

   http {
       upstream frontend {
           server frontend:3000;
       }

       upstream backend {
           server backend:8000;
       }

       server {
           listen 80;
           server_name yourdomain.com;
           return 301 https://$host$request_uri;
       }

       server {
           listen 443 ssl;
           server_name yourdomain.com;

           ssl_certificate /etc/nginx/ssl/cert.pem;
           ssl_certificate_key /etc/nginx/ssl/key.pem;

           location / {
               proxy_pass http://frontend;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
           }

           location /api {
               proxy_pass http://backend;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
           }
       }
   }
   ```

5. SSL setup:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

6. Start services:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

## Environment Configuration

### Required Environment Variables

1. Database Configuration:
   ```
   POSTGRES_USER=production_user
   POSTGRES_PASSWORD=strong_password
   POSTGRES_DB=unbounded_db
   DATABASE_URL=postgresql://production_user:strong_password@db:5432/unbounded_db
   ```

2. Security Keys:
   ```
   SECRET_KEY=<generated_secret>
   JWT_SECRET_KEY=<generated_jwt_secret>
   ```

3. API Keys:
   ```
   DEEPSEEK_API_KEY=<your_key>
   BFL_API_KEY=<your_key>
   REPLICATE_API_KEY=<your_key>
   STABILITY_API_KEY=<your_key>
   OPENAI_API_KEY=<your_key>
   MEM0_API_KEY=<your_key>
   HUME_API_KEY=<your_key>
   HUME_SECRET_KEY=<your_key>
   ```

## Database Setup

1. Initial setup:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. Backup:
   ```bash
   docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql
   ```

3. Restore:
   ```bash
   cat backup.sql | docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB
   ```

## External Services

1. Ollama Setup:
   - Development: Local installation
   - Production: Dedicated server or managed service

2. Memory Service:
   - Configure mem0 storage path
   - Set up backup system

3. Image Generation:
   - Configure rate limits
   - Set up caching

## Monitoring

1. Application Monitoring:
   ```bash
   # Install monitoring stack
   docker compose -f docker-compose.monitoring.yml up -d
   ```

2. Log Management:
   - Configure log rotation
   - Set up log aggregation

3. Alerts:
   - Set up email notifications
   - Configure Discord/Slack webhooks

## Backup and Recovery

1. Database Backups:
   ```bash
   # Create backup script
   cat > backup.sh << 'EOF'
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$DATE.sql
   EOF
   chmod +x backup.sh
   ```

2. Memory Store Backups:
   ```bash
   # Backup memory data
   tar -czf memories_backup.tar.gz data/memories/
   ```

3. Configuration Backups:
   ```bash
   # Backup configs
   tar -czf configs_backup.tar.gz .env* *.yml *.conf
   ```

## Troubleshooting

### Common Issues

1. Database Connection:
   ```bash
   # Check database logs
   docker compose logs db
   
   # Check connection
   docker compose exec backend python -c "from app.database import engine; print(engine.connect())"
   ```

2. Memory Service:
   ```bash
   # Check memory service logs
   docker compose logs backend | grep memory
   
   # Verify storage
   docker compose exec backend ls -la /app/data/memories
   ```

3. External Services:
   ```bash
   # Test Ollama
   curl http://localhost:11434/api/generate -d '{"model": "llama2", "prompt": "test"}'
   
   # Check API keys
   docker compose exec backend python -c "import os; print(os.environ.get('OPENAI_API_KEY'))"
   ```

### Recovery Steps

1. Service Recovery:
   ```bash
   # Restart services
   docker compose restart
   
   # Rebuild services
   docker compose up -d --build
   ```

2. Database Recovery:
   ```bash
   # Restore from backup
   cat backup.sql | docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB
   ```

3. Memory Store Recovery:
   ```bash
   # Restore memories
   tar -xzf memories_backup.tar.gz -C /path/to/data/
   ``` 