# Comprehensive Deployment Guide - Multi-Retail POS System

## 📋 Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Deployment Architecture](#deployment-architecture)
3. [Development Environment Deployment](#development-environment-deployment)
4. [Production Environment Deployment](#production-environment-deployment)
5. [Docker Containerization](#docker-containerization)
6. [Cloud Deployment](#cloud-deployment)
7. [Load Balancer Configuration](#load-balancer-configuration)
8. [Database Deployment](#database-deployment)
9. [Security Configuration](#security-configuration)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Scaling Strategies](#scaling-strategies)
12. [Deployment Automation](#deployment-automation)
13. [Backup and Recovery](#backup-and-recovery)
14. [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Deployment Overview

### Deployment Models

The multi-retail POS system supports multiple deployment models:

```
┌─────────────────────────────────────────────────────────────┐
│                Deployment Models                       │
├─────────────────────────────────────────────────────────────┤
│ 1. Single Instance Deployment                           │
│    - Development & Testing                               │
│    - Small Businesses                                    │
│    - All components on single server                      │
├─────────────────────────────────────────────────────────────┤
│ 2. Multi-Instance Deployment                            │
│    - Medium to Large Businesses                          │
│    - Load balancing across multiple servers              │
│    - Database clustering                                │
├─────────────────────────────────────────────────────────────┤
│ 3. Cloud-Based Deployment                              │
│    - Enterprise deployments                             │
│    - Auto-scaling capabilities                         │
│    - Managed services                                 │
├─────────────────────────────────────────────────────────────┤
│ 4. Hybrid Deployment                                   │
│    - On-premise + Cloud                              │
│    - Disaster recovery                                 │
│    - Data sovereignty compliance                        │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Components

```
┌─────────────────────────────────────────────────────────────┐
│                Application Stack                        │
├─────────────────────────────────────────────────────────────┤
│ Load Balancer (Nginx/HAProxy)                        │
│ Web Server (Gunicorn/uWSGI)                           │
│ Application (Flask)                                     │
│ Database (PostgreSQL/MySQL)                             │
│ Cache (Redis/Memcached)                                │
│ File Storage (Local/S3/NFS)                            │
│ Monitoring (Prometheus/Grafana)                         │
│ Logging (ELK Stack/Fluentd)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Single Instance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Single Server                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Nginx (Port 80/443)               │   │
│  │  - Static Files                                    │   │
│  │  - Reverse Proxy                                   │   │
│  │  - SSL Termination                                │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                      │                                   │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │            Gunicorn (Port 8000)                 │   │
│  │  - Flask Application                               │   │
│  │  - Worker Processes                               │   │
│  │  - Request Handling                               │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                      │                                   │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │            PostgreSQL (Port 5432)                │   │
│  │  - Application Database                           │   │
│  │  - Connection Pooling                            │   │
│  │  - Data Persistence                              │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                      │                                   │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              Redis (Port 6379)                   │   │
│  │  - Caching Layer                                 │   │
│  │  - Session Storage                               │   │
│  │  - Task Queue                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Instance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Load Balancer                          │
│              (Nginx/HAProxy)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐        ┌────────▼────────┐
│   Server 1      │        │   Server 2      │
│                 │        │                 │
│ ┌─────────────┐  │        │ ┌─────────────┐  │
│ │   Nginx     │  │        │ │   Nginx     │  │
│ └─────┬───────┘  │        │ └─────┬───────┘  │
│       │          │        │       │          │
│ ┌─────▼─────┐    │        │ ┌─────▼─────┐    │
│ │ Gunicorn   │    │        │ │ Gunicorn   │    │
│ └─────┬─────┘    │        │ └─────┬─────┘    │
│       │          │        │       │          │
│ ┌─────▼─────┐    │        │ ┌─────▼─────┐    │
│ │  Redis     │    │        │ │  Redis     │    │
│ └─────┬─────┘    │        │ └─────┬─────┘    │
│       │          │        │       │          │
└───────┼──────────┘        └───────┼──────────┘
        │                           │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │      Database Cluster      │
        │   (PostgreSQL Master/     │
        │     Replica Setup)        │
        └───────────────────────────┘
```

---

## Development Environment Deployment

### Local Development Setup

#### Prerequisites

```bash
# System Requirements
- Python 3.9+
- PostgreSQL 12+ (optional for development)
- Redis 6+ (optional for development)
- Git
- Node.js (for frontend tools)

# Recommended Hardware
- CPU: 2+ cores
- RAM: 4GB+
- Storage: 20GB+
```

#### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/multi-retail-pos.git
cd multi-retail-pos/multi_web_cloud

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Initialize database
python init_database.py

# 6. Run the application
python app.py
```

#### Development Environment Configuration

```bash
# .env for development
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///restaurant_pos_dev.db
REDIS_URL=redis://localhost:6379/0

# Feature Flags
FEATURE_SALES_PROCESSING=true
FEATURE_PRODUCT_CATALOG=true
FEATURE_TABLE_MANAGEMENT=true
FEATURE_CRM_LOYALTY=true

# Multi-tenancy
MULTI_TENANT=True
DEFAULT_TENANT=default
TENANT_ISOLATION=row_level

# Security
RATE_LIMIT_AUTH=10
RATE_LIMIT_API=200
MAX_FAILED_ATTEMPTS=10

# Payment (Test Mode)
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
RAZORPAY_TEST_MODE=true
```

#### Development Services

```bash
# Using Docker Compose for development services
docker-compose -f docker-compose.dev.yml up -d

# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: pos_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/dev.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

---

## Production Environment Deployment

### Production Server Setup

#### System Requirements

```bash
# Minimum Requirements
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Network: 1Gbps

# Recommended Requirements
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 500GB SSD
- Network: 10Gbps

# Software Requirements
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Nginx 1.18+
```

#### Production Deployment Steps

```bash
# 1. Server Preparation
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3.9-venv python3.9-dev
sudo apt install -y postgresql-13 postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx
sudo apt install -y build-essential

# 2. Application Setup
# Create application user
sudo useradd -m -s /bin/bash posuser
sudo su - posuser

# Clone repository
git clone https://github.com/your-org/multi-retail-pos.git
cd multi-retail-pos/multi_web_cloud

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# 3. Database Setup
sudo -u postgres psql
CREATE DATABASE pos_prod;
CREATE USER posuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE pos_prod TO posuser;
\q

# Configure application
cp .env.example .env
# Edit .env with production values

# Initialize database
python init_database.py

# 4. Gunicorn Service
sudo tee /etc/systemd/system/pos-app.service > /dev/null <<EOF
[Unit]
Description=POS Application
After=network.target

[Service]
User=posuser
Group=posuser
WorkingDirectory=/home/posuser/multi-retail-pos/multi_web_cloud
Environment="PATH=/home/posuser/multi-retail-pos/multi_web_cloud/venv/bin"
ExecStart=/home/posuser/multi-retail-pos/multi_web_cloud/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pos-app
sudo systemctl start pos-app

# 5. Nginx Configuration
sudo tee /etc/nginx/sites-available/pos > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/posuser/multi-retail-pos/multi_web_cloud/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/pos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 6. SSL Certificate (Let's Encrypt)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### Production Environment Configuration

```bash
# .env for production
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://posuser:secure_password@localhost/pos_prod
REDIS_URL=redis://localhost:6379/0

# Multi-tenancy
MULTI_TENANT=True
DEFAULT_TENANT=default
TENANT_ISOLATION=database

# Security
RATE_LIMIT_AUTH=5
RATE_LIMIT_API=100
MAX_FAILED_ATTEMPTS=5
FORCE_HTTPS=True

# Payment (Production Mode)
RAZORPAY_KEY_ID=rzp_live_XXXXXXXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret

# Performance
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/pos/app.log
```

---

## Docker Containerization

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash posuser
RUN chown -R posuser:posuser /app
USER posuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://posuser:${DB_PASSWORD}@postgres:5432/pos_prod
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - RAZORPAY_KEY_ID=${RAZORPAY_KEY_ID}
      - RAZORPAY_KEY_SECRET=${RAZORPAY_KEY_SECRET}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=pos_prod
      - POSTGRES_USER=posuser
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - app
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Docker Deployment Commands

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Scale application
docker-compose -f docker-compose.prod.yml up -d --scale app=5

# Update deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U posuser pos_prod > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U posuser pos_prod < backup.sql
```

---

## Cloud Deployment

### AWS Deployment

#### AWS ECS (Elastic Container Service)

```yaml
# ecs-task-definition.json
{
  "family": "pos-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "pos-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/pos-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/pos_prod"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:pos/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pos-app",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### AWS RDS Configuration

```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier pos-prod-db \
    --db-instance-class db.m5.large \
    --engine postgres \
    --engine-version 13.7 \
    --master-username posuser \
    --master-user-password secure_password \
    --allocated-storage 100 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-subnet-group-name default \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted

# Create read replica
aws rds create-db-instance-read-replica \
    --db-instance-identifier pos-prod-db-replica \
    --source-db-instance-identifier pos-prod-db \
    --db-instance-class db.m5.large
```

#### AWS ElastiCache (Redis)

```bash
# Create Redis cluster
aws elasticache create-replication-group \
    --replication-group-id pos-prod-redis \
    --replication-group-description "POS Production Redis" \
    --num-cache-clusters 3 \
    --cache-node-type cache.m5.large \
    --engine redis \
    --engine-version 6.x \
    --cache-parameter-group-name default.redis6.x \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-group-name default
```

### Azure Deployment

#### Azure Container Instances

```yaml
# azure-container.yml
apiVersion: 2019-12-01
location: eastus
name: pos-app-group
properties:
  containers:
  - name: pos-app
    properties:
      image: yourregistry.azurecr.io/pos-app:latest
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 2.0
      ports:
      - port: 8000
      environmentVariables:
      - name: FLASK_ENV
        value: production
      - name: DATABASE_URL
        secureValue: postgresql://user:pass@server:5432/db
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 80
      targetPort: 8000
```

#### Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres server create \
    --name pos-prod-db \
    --resource-group pos-resources \
    --location eastus \
    --admin-user posuser \
    --admin-password secure_password \
    --sku-name GP_Gen5_2 \
    --version 13

# Configure firewall
az postgres server firewall-rule create \
    --name allow-all \
    --server pos-prod-db \
    --resource-group pos-resources \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255
```

### GCP Deployment

#### Google Cloud Run

```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/pos-app', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/pos-app']

images:
- 'gcr.io/$PROJECT_ID/pos-app'
```

```bash
# Deploy to Cloud Run
gcloud run deploy pos-app \
    --image gcr.io/$PROJECT_ID/pos-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars FLASK_ENV=production \
    --set-secrets DATABASE_URL=pos-db-url:latest
```

---

## Load Balancer Configuration

### Nginx Load Balancer

```nginx
# nginx-lb.conf
upstream pos_backend {
    least_conn;
    server 10.0.1.10:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 weight=1 max_fails=3 fail_timeout=30s;
}

# Rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    # Health check endpoint
    location /health {
        proxy_pass http://pos_backend;
        access_log off;
    }

    # API rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://pos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Auth rate limiting
    location /auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://pos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Main application
    location / {
        proxy_pass http://pos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

### HAProxy Load Balancer

```cfg
# haproxy.cfg
global
    daemon
    maxconn 4096
    log stdout format raw local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option dontlognull

frontend pos_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/your-domain.pem
    redirect scheme https if !{ ssl_fc }
    
    # ACLs
    acl is_api path_beg /api/
    acl is_auth path_beg /auth/
    
    # Rate limiting
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
    
    # Backend selection
    use_backend pos_api if is_api
    use_backend pos_auth if is_auth
    default_backend pos_main

backend pos_api
    balance roundrobin
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check

backend pos_auth
    balance roundrobin
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check

backend pos_main
    balance roundrobin
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check

# Health check
backend health_check
    mode http
    option httpchk GET /health
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check
```

---

## Database Deployment

### PostgreSQL Master-Slave Replication

#### Master Configuration

```bash
# postgresql.conf (Master)
listen_addresses = '*'
port = 5432
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# WAL settings for replication
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3
synchronous_commit = on
synchronous_standby_names = 'standby1,standby2'

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'
log_min_duration_statement = 1000
```

```bash
# pg_hba.conf (Master)
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer
local   all             all                                     md5

# Replication connections
host    replication     replicator      10.0.1.0/24           md5

# Application connections
host    pos_prod        posuser         10.0.1.0/24           md5
```

#### Slave Configuration

```bash
# recovery.conf (Slave)
standby_mode = 'on'
primary_conninfo = 'host=10.0.1.10 port=5432 user=replicator'
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
archive_cleanup_command = 'pg_archivecleanup /var/lib/postgresql/wal_archive %r'
```

### Database Connection Pooling

#### PgBouncer Configuration

```ini
# pgbouncer.ini
[databases]
pos_prod = host=localhost port=5432 dbname=pos_prod user=posuser

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 5
max_db_connections = 50
max_user_connections = 50

# Timeouts
server_reset_query = DISCARD ALL
server_check_delay = 30
server_check_query = select 1
server_lifetime = 3600
server_idle_timeout = 600

# Logging
syslog = 0
syslog_facility = daemon
syslog_ident = pgbouncer
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

---

## Security Configuration

### SSL/TLS Configuration

#### Let's Encrypt SSL Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### SSL Hardening

```nginx
# SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Firewall Configuration

```bash
# UFW Firewall Rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow database (from specific IPs only)
sudo ufw allow from 10.0.1.0/24 to any port 5432
sudo ufw allow from 10.0.1.0/24 to any port 6379

# Enable firewall
sudo ufw enable
```

### Application Security

```python
# Security middleware
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

---

## Monitoring and Logging

### Prometheus Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "pos_rules.yml"

scrape_configs:
  - job_name: 'pos-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "POS Application Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "flask_http_request_duration_seconds",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{datname}}"
          }
        ]
      }
    ]
  }
}
```

### Log Management

```python
# Logging configuration
import logging
from logging.handlers import RotatingFileHandler
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'tenant_id'):
            log_entry['tenant_id'] = record.tenant_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        return json.dumps(log_entry)

# Configure logging
def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            '/var/log/pos/app.log',
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
```

---

## Scaling Strategies

### Horizontal Scaling

#### Auto-scaling with Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'

services:
  app:
    image: your-registry/pos-app:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    networks:
      - pos-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == manager
    networks:
      - pos-network

networks:
  pos-network:
    driver: overlay
```

#### Kubernetes Auto-scaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pos-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pos-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Scaling

#### Read Replicas

```bash
# Create read replicas
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
GRANT REPLICATION CONNECT ON DATABASE pos_prod TO replicator;

# In postgresql.conf
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on

# Application connection logic
def get_db_connection(read_only=False):
    if read_only:
        # Connect to replica
        return psycopg2.connect(
            host='replica-endpoint',
            database='pos_prod',
            user='posuser',
            password='password'
        )
    else:
        # Connect to master
        return psycopg2.connect(
            host='master-endpoint',
            database='pos_prod',
            user='posuser',
            password='password'
        )
```

---

## Deployment Automation

### CI/CD Pipeline

#### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=app

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: |
        docker build -t your-registry/pos-app:${{ github.sha }} .
        docker tag your-registry/pos-app:${{ github.sha }} your-registry/pos-app:latest
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push your-registry/pos-app:${{ github.sha }}
        docker push your-registry/pos-app:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to production
      run: |
        # Deploy to production server
        ssh user@server "docker-compose -f /path/to/docker-compose.prod.yml pull"
        ssh user@server "docker-compose -f /path/to/docker-compose.prod.yml up -d"
```

### Blue-Green Deployment

```bash
#!/bin/bash
# blue-green-deploy.sh

CURRENT_ENV=$(docker service ls --filter name=pos-app --format "{{.Name}}" | head -1 | cut -d'-' -f3)
NEW_ENV="green"

if [ "$CURRENT_ENV" = "green" ]; then
    NEW_ENV="blue"
fi

echo "Deploying to $NEW_ENV environment"

# Deploy new version
docker service create \
    --name pos-app-$NEW_ENV \
    --network pos-network \
    --replicas 3 \
    your-registry/pos-app:latest

# Wait for health check
echo "Waiting for health check..."
sleep 30

# Switch traffic
docker service update \
    --detach=false \
    --image nginx:alpine \
    pos-lb

# Cleanup old environment
docker service rm pos-app-$CURRENT_ENV

echo "Deployment completed successfully"
```

---

## Backup and Recovery

### Database Backup Strategy

```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pos_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -h localhost -U posuser -d pos_prod > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE.gz s3://pos-backups/database/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### Application Backup

```bash
#!/bin/bash
# backup-application.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_BACKUP_DIR="$BACKUP_DIR/app_backup_$DATE"

# Create backup directory
mkdir -p $APP_BACKUP_DIR

# Backup application files
tar -czf $APP_BACKUP_DIR/app.tar.gz /home/posuser/multi-retail-pos

# Backup uploads
tar -czf $APP_BACKUP_DIR/uploads.tar.gz /home/posuser/uploads

# Backup configuration
cp /home/posuser/multi-retail-pos/.env $APP_BACKUP_DIR/.env

# Upload to S3
aws s3 sync $APP_BACKUP_DIR s3://pos-backups/application/$DATE/

echo "Application backup completed: $APP_BACKUP_DIR"
```

### Recovery Procedures

```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Download backup from S3
aws s3 cp s3://pos-backups/database/$BACKUP_FILE /tmp/

# Extract backup
gunzip /tmp/$BACKUP_FILE

# Stop application
sudo systemctl stop pos-app

# Restore database
psql -h localhost -U posuser -d pos_prod < /tmp/${BACKUP_FILE%.gz}

# Start application
sudo systemctl start pos-app

echo "Database restore completed"
```

---

## Troubleshooting Deployment

### Common Issues

#### Database Connection Issues

```bash
# Check database status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U posuser -d pos_prod

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Test from application server
telnet postgres-server 5432
```

#### Application Issues

```bash
# Check application status
sudo systemctl status pos-app

# Check logs
sudo journalctl -u pos-app -f

# Check Gunicorn processes
ps aux | grep gunicorn

# Restart application
sudo systemctl restart pos-app
```

#### Load Balancer Issues

```bash
# Check Nginx status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

### Performance Issues

```bash
# Check system resources
top
htop
iostat -x 1

# Check database performance
sudo -u postgres psql -d pos_prod -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
sudo -u postgres psql -d pos_prod -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check network connections
netstat -an | grep :8000
```

### Monitoring Alerts

```yaml
# prometheus-alerts.yml
groups:
- name: pos-app-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(flask_http_request_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"

  - alert: DatabaseConnectionsHigh
    expr: pg_stat_database_numbackends > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database connections"
      description: "Database has {{ $value }} active connections"
```

---

**Version**: 1.0.0 Deployment Guide  
**Last Updated**: December 2024  
**Documentation**: Flask POS Development Team