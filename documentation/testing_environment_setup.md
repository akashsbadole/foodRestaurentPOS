# Testing Environment Setup Procedures

## Overview

This document provides comprehensive procedures for setting up testing environments for the support system and license validation system. It includes local development environments, CI/CD environments, performance testing environments, and production-like staging environments.

## Table of Contents

1. [Environment Types](#environment-types)
2. [Prerequisites](#prerequisites)
3. [Local Development Environment Setup](#local-development-environment-setup)
4. [CI/CD Environment Setup](#cicd-environment-setup)
5. [Performance Testing Environment Setup](#performance-testing-environment-setup)
6. [Staging Environment Setup](#staging-environment-setup)
7. [Production Environment Setup](#production-environment-setup)
8. [Environment Configuration Management](#environment-configuration-management)
9. [Database Setup Procedures](#database-setup-procedures)
10. [Security Configuration](#security-configuration)
11. [Monitoring and Logging Setup](#monitoring-and-logging-setup)
12. [Environment Validation Procedures](#environment-validation-procedures)

## Environment Types

### Environment Hierarchy

```
Production (PROD)
    ↑
Staging (STAGE) - Production-like environment for final testing
    ↑
Performance Testing (PERF) - Dedicated environment for performance testing
    ↑
Integration Testing (INT) - Environment for integration testing
    ↑
Development (DEV) - Local development environment
```

### Environment Characteristics

| Environment | Purpose | Data | Scale | Access |
|-------------|---------|------|-------|-------|
| Development | Local development and unit testing | Mock/Synthetic | Single user | Developer only |
| Integration | Integration testing between components | Test data | Small team | Development team |
| Performance | Load and performance testing | Scaled test data | Simulated load | Test team |
| Staging | Production-like testing | Anonymized production | Production-like | QA team |
| Production | Live environment | Real data | Full scale | Authorized users |

## Prerequisites

### System Requirements

#### Hardware Requirements

**Minimum Development Environment:**
- CPU: 4 cores (2.5 GHz)
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 100 Mbps

**Recommended Development Environment:**
- CPU: 8 cores (3.0 GHz)
- RAM: 16 GB
- Storage: 100 GB SSD
- Network: 1 Gbps

**Performance Testing Environment:**
- CPU: 16 cores (3.5 GHz)
- RAM: 32 GB
- Storage: 500 GB SSD
- Network: 10 Gbps

#### Software Requirements

**Operating Systems:**
- Windows 10/11 (64-bit)
- macOS 10.15+ (Catalina or later)
- Ubuntu 20.04+ LTS
- CentOS/RHEL 8+

**Development Tools:**
- Python 3.8+
- Git 2.25+
- Docker 20.10+
- Docker Compose 1.29+
- Node.js 16+ (for frontend testing)
- PostgreSQL 12+ (optional, for database testing)

**Testing Tools:**
- pytest 6.0+
- Selenium WebDriver 4.0+
- JMeter 5.4+ (for performance testing)
- Postman 9.0+ (for API testing)

### Network Requirements

**Port Requirements:**
- 8000-8099: Application servers
- 3000-3099: Frontend development servers
- 5432: PostgreSQL database
- 6379: Redis cache
- 8080: Test API server
- 9200: Elasticsearch (for logging)

**Firewall Rules:**
- Allow outbound HTTPS (443) for external service calls
- Allow outbound HTTP (80) for package downloads
- Allow inbound connections on test ports from authorized IPs

## Local Development Environment Setup

### Quick Start Setup Script

```bash
#!/bin/bash
# scripts/setup_dev_environment.sh

set -e

echo "🚀 Setting up local development environment..."

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.8+"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        echo "❌ Git is not installed. Please install Git 2.25+"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker 20.10+"
        exit 1
    fi
    
    echo "✅ All prerequisites satisfied"
}

# Create virtual environment
create_virtual_env() {
    echo "🐍 Creating Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    echo "✅ Pip upgraded"
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # Install Python dependencies
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -r requirements-test.txt
    
    echo "✅ Python dependencies installed"
}

# Setup database
setup_database() {
    echo "🗄️ Setting up database..."
    
    # Start PostgreSQL container
    docker run -d \
        --name posmvp-postgres-dev \
        -e POSTGRES_DB=posmvp_dev \
        -e POSTGRES_USER=dev_user \
        -e POSTGRES_PASSWORD=dev_password \
        -p 5432:5432 \
        postgres:13
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    python database_setup.py --env=dev
    
    echo "✅ Database setup complete"
}

# Setup test data
setup_test_data() {
    echo "📊 Setting up test data..."
    
    python scripts/load_test_data.py --env=dev
    
    echo "✅ Test data loaded"
}

# Setup configuration files
setup_configuration() {
    echo "⚙️ Setting up configuration files..."
    
    # Create development configuration
    cat > config/dev_config.json << EOF
{
    "database": {
        "url": "postgresql://dev_user:dev_password@localhost:5432/posmvp_dev",
        "pool_size": 5,
        "max_overflow": 10
    },
    "license_server": {
        "url": "https://dev-license-server.example.com/api/v1",
        "timeout": 30,
        "retry_attempts": 3
    },
    "email_service": {
        "url": "https://dev-email-service.example.com/api/v1",
        "api_key": "dev-api-key",
        "from_email": "dev@example.com"
    },
    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "logs/dev.log"
    },
    "security": {
        "secret_key": "dev-secret-key-change-in-production",
        "encryption_key": "dev-encryption-key",
        "jwt_expiration": 3600
    },
    "features": {
        "debug_mode": true,
        "mock_external_services": true,
        "enable_test_endpoints": true
    }
}
EOF
    
    echo "✅ Configuration files created"
}

# Setup development tools
setup_dev_tools() {
    echo "🛠️ Setting up development tools..."
    
    # Install pre-commit hooks
    pip install pre-commit
    pre-commit install
    
    # Setup Git hooks
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for development

echo "Running pre-commit checks..."

# Run linting
echo "Running linting..."
flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

# Run type checking
echo "Running type checking..."
mypy src/ --ignore-missing-imports

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

echo "✅ Pre-commit checks passed"
EOF
    
    chmod +x .git/hooks/pre-commit
    
    echo "✅ Development tools setup complete"
}

# Create startup scripts
create_startup_scripts() {
    echo "📜 Creating startup scripts..."
    
    # Create development server startup script
    cat > scripts/start_dev_server.sh << 'EOF'
#!/bin/bash
# Start development server

echo "Starting development server..."

# Activate virtual environment
source venv/bin/activate

# Set environment
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start server
python main.py --config=config/dev_config.json
EOF
    
    chmod +x scripts/start_dev_server.sh
    
    # Create test runner script
    cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash
# Run tests

echo "Running tests..."

# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

echo "✅ Tests completed"
EOF
    
    chmod +x scripts/run_tests.sh
    
    echo "✅ Startup scripts created"
}

# Main execution
main() {
    check_prerequisites
    create_virtual_env
    install_dependencies
    setup_database
    setup_test_data
    setup_configuration
    setup_dev_tools
    create_startup_scripts
    
    echo ""
    echo "🎉 Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start development server: ./scripts/start_dev_server.sh"
    echo "3. Run tests: ./scripts/run_tests.sh"
    echo "4. Open http://localhost:8000 in your browser"
    echo ""
}

# Run main function
main "$@"
```

### Docker Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/venv
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=postgresql://dev_user:dev_password@postgres:5432/posmvp_dev
    depends_on:
      - postgres
      - redis
    networks:
      - posmvp-network

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: posmvp_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    networks:
      - posmvp-network

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - posmvp-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/dev.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
    networks:
      - posmvp-network

volumes:
  postgres_data:
  redis_data:

networks:
  posmvp-network:
    driver: bridge
```

### Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-test.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "main.py", "--config", "config/dev_config.json"]
```

## CI/CD Environment Setup

### GitHub Actions Configuration

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: 3.9
  NODE_VERSION: 16

jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      cache-key: ${{ steps.cache-key.outputs.key }}
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Generate cache key
      id: cache-key
      run: |
        echo "key=${{ hashFiles('**/requirements*.txt') }}-${{ env.PYTHON_VERSION }}" >> $GITHUB_OUTPUT

  lint:
    runs-on: ubuntu-latest
    needs: setup
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ needs.setup.outputs.cache-key }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort mypy
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
        black --check src/ tests/
        isort --check-only src/ tests/
        mypy src/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    needs: setup
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: posmvp_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ needs.setup.outputs.cache-key }}-${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Setup database
      run: |
        python database_setup.py --env=test
        python scripts/load_test_data.py --env=test
      env:
        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/posmvp_test
    
    - name: Run unit tests
      run: |
        python -m pytest tests/unit/ -v --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/posmvp_test
    
    - name: Run integration tests
      run: |
        python -m pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://test_user:test_password@localhost:5432/posmvp_test
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    needs: setup
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
        pip install -r requirements.txt
    
    - name: Run security scan
      run: |
        bandit -r src/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  build:
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

## Performance Testing Environment Setup

### Performance Testing Infrastructure

```yaml
# docker-compose.perf.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.perf
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=performance
      - DATABASE_URL=postgresql://perf_user:perf_password@postgres:5432/posmvp_perf
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - perf-network

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: posmvp_perf
      POSTGRES_USER: perf_user
      POSTGRES_PASSWORD: perf_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_perf_data:/var/lib/postgresql/data
      - ./scripts/init_perf_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    networks:
      - perf-network

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_perf_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    networks:
      - perf-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/perf.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
    networks:
      - perf-network

  jmeter:
    image: justb4/jmeter:5.4.3
    environment:
      - JVM_ARGS="-Xms2g -Xmx4g"
    volumes:
      - ./jmeter/tests:/tests
      - ./jmeter/results:/results
    command: |
      sh -c "
      while ! nc -z app 8000; do
        echo 'Waiting for application...'
        sleep 2
      done
      jmeter -n -t /tests/performance_test.jmx -l /results/results.jtl -j /results/jmeter.log
      "
    depends_on:
      - app
    networks:
      - perf-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - perf-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - perf-network

volumes:
  postgres_perf_data:
  redis_perf_data:
  prometheus_data:
  grafana_data:

networks:
  perf-network:
    driver: bridge
```

### Performance Test Configuration

```xml
<!-- jmeter/tests/performance_test.jmx -->
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Performance Test Plan" enabled="true">
      <stringProp name="TestPlan.comments">Performance test for POS MVP application</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="BASE_URL" elementType="Argument">
            <stringProp name="Argument.name">BASE_URL</stringProp>
            <stringProp name="Argument.value">http://app:8000</stringProp>
          </elementProp>
          <elementProp name="THREADS" elementType="Argument">
            <stringProp name="Argument.name">THREADS</stringProp>
            <stringProp name="Argument.value">100</stringProp>
          </elementProp>
          <elementProp name="RAMP_UP" elementType="Argument">
            <stringProp name="Argument.name">RAMP_UP</stringProp>
            <stringProp name="Argument.value">60</stringProp>
          </elementProp>
          <elementProp name="DURATION" elementType="Argument">
            <stringProp name="Argument.name">DURATION</stringProp>
            <stringProp name="Argument.value">300</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <!-- License Validation Test -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="License Validation" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">${DURATION}</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${THREADS}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${RAMP_UP}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${DURATION}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="License Validation Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
          <stringProp name="HTTPSampler.path">/api/v1/license/validate</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
        </hashTree>
      </hashTree>
      
      <!-- Support Ticket Creation Test -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Support Ticket Creation" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">${DURATION}</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">${THREADS}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${RAMP_UP}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${DURATION}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Create Support Ticket" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
          <stringProp name="HTTPSampler.path">/api/v1/support/tickets</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Authorization</stringProp>
                <stringProp name="Header.value">Bearer test-token</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
        </hashTree>
      </hashTree>
      
      <!-- Results Collection -->
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename">/results/results.jtl</stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

## Staging Environment Setup

### Staging Infrastructure

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=staging
      - DATABASE_URL=postgresql://stage_user:stage_password@postgres:5432/posmvp_stage
      - REDIS_URL=redis://redis:6379/0
      - LICENSE_SERVER_URL=https://stage-license-server.example.com/api/v1
      - EMAIL_SERVICE_URL=https://stage-email-service.example.com/api/v1
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    networks:
      - staging-network

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: posmvp_stage
      POSTGRES_USER: stage_user
      POSTGRES_PASSWORD: stage_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_stage_data:/var/lib/postgresql/data
      - ./backups:/backups
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
    networks:
      - staging-network

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_stage_data:/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - staging-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - app
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    networks:
      - staging-network

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    networks:
      - staging-network

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    ports:
      - "5044:5044"
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      - ./logs:/logs
    depends_on:
      - elasticsearch
    networks:
      - staging-network

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - staging-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - staging-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - staging-network

volumes:
  postgres_stage_data:
  redis_stage_data:
  elasticsearch_data:
  prometheus_data:
  grafana_data:

networks:
  staging-network:
    driver: bridge
```

## Environment Configuration Management

### Configuration Templates

```python
# config/environment_config.py
"""Environment configuration management"""

import os
import json
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

@dataclass
class LicenseServerConfig:
    """License server configuration"""
    url: str
    timeout: int = 30
    retry_attempts: int = 3
    api_key: str = ""

@dataclass
class EmailServiceConfig:
    """Email service configuration"""
    url: str
    api_key: str
    from_email: str
    smtp_server: str = ""
    smtp_port: int = 587

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    encryption_key: str
    jwt_expiration: int = 3600
    password_salt: str = ""

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/app.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5

@dataclass
class FeatureConfig:
    """Feature configuration"""
    debug_mode: bool = False
    mock_external_services: bool = False
    enable_test_endpoints: bool = False
    enable_api_docs: bool = True

class EnvironmentConfig:
    """Environment configuration manager"""
    
    def __init__(self, env: str = None):
        self.env = env or os.getenv('ENVIRONMENT', 'development')
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration for environment"""
        config_file = f"config/{self.env}_config.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database": {
                "url": "sqlite:///posmvp.db",
                "pool_size": 5,
                "max_overflow": 10,
                "echo": False
            },
            "license_server": {
                "url": "https://api.license-server.com/v1",
                "timeout": 30,
                "retry_attempts": 3,
                "api_key": ""
            },
            "email_service": {
                "url": "https://api.email-service.com/v1",
                "api_key": "",
                "from_email": "noreply@example.com",
                "smtp_server": "",
                "smtp_port": 587
            },
            "security": {
                "secret_key": "change-me-in-production",
                "encryption_key": "change-me-in-production",
                "jwt_expiration": 3600,
                "password_salt": "change-me-in-production"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log",
                "max_bytes": 10485760,
                "backup_count": 5
            },
            "features": {
                "debug_mode": False,
                "mock_external_services": False,
                "enable_test_endpoints": False,
                "enable_api_docs": True
            }
        }
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self.config.get('database', {})
        return DatabaseConfig(**db_config)
    
    @property
    def license_server(self) -> LicenseServerConfig:
        """Get license server configuration"""
        ls_config = self.config.get('license_server', {})
        return LicenseServerConfig(**ls_config)
    
    @property
    def email_service(self) -> EmailServiceConfig:
        """Get email service configuration"""
        es_config = self.config.get('email_service', {})
        return EmailServiceConfig(**es_config)
    
    @property
    def security(self) -> SecurityConfig:
        """Get security configuration"""
        sec_config = self.config.get('security', {})
        return SecurityConfig(**sec_config)
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration"""
        log_config = self.config.get('logging', {})
        return LoggingConfig(**log_config)
    
    @property
    def features(self) -> FeatureConfig:
        """Get feature configuration"""
        feat_config = self.config.get('features', {})
        return FeatureConfig(**feat_config)
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Validate database configuration
        if not self.database.url:
            errors.append("Database URL is required")
        
        # Validate security configuration
        if self.env == 'production':
            if self.security.secret_key == 'change-me-in-production':
                errors.append("Secret key must be changed in production")
            if self.security.encryption_key == 'change-me-in-production':
                errors.append("Encryption key must be changed in production")
        
        # Validate license server configuration
        if not self.license_server.url:
            errors.append("License server URL is required")
        
        # Validate email service configuration
        if not self.email_service.api_key:
            errors.append("Email service API key is required")
        
        if errors:
            for error in errors:
                print(f"Configuration error: {error}")
            return False
        
        return True
```

## Database Setup Procedures

### Database Initialization Script

```python
# scripts/init_database.py
"""Database initialization script"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

def create_database(db_name, db_user, db_password, db_host='localhost', db_port=5432):
    """Create database"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user='postgres',
            password=db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}")
        
        cursor.close()
        conn.close()
        
        print(f"✅ Database '{db_name}' created successfully")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def run_migrations(db_url, migrations_dir='migrations'):
    """Run database migrations"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Create migrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get executed migrations
        cursor.execute("SELECT filename FROM migrations ORDER BY filename")
        executed_migrations = {row[0] for row in cursor.fetchall()}
        
        # Run pending migrations
        migration_files = sorted(Path(migrations_dir).glob('*.sql'))
        
        for migration_file in migration_files:
            if migration_file.name not in executed_migrations:
                print(f"Running migration: {migration_file.name}")
                
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                
                cursor.execute(migration_sql)
                cursor.execute(
                    "INSERT INTO migrations (filename) VALUES (%s)",
                    (migration_file.name,)
                )
                
                conn.commit()
                print(f"✅ Migration {migration_file.name} executed")
        
        cursor.close()
        conn.close()
        
        print("✅ All migrations executed successfully")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error running migrations: {e}")
        return False

def load_test_data(db_url, test_data_file='scripts/test_data.sql'):
    """Load test data"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        if os.path.exists(test_data_file):
            with open(test_data_file, 'r') as f:
                test_data_sql = f.read()
            
            cursor.execute(test_data_sql)
            conn.commit()
            
            print(f"✅ Test data loaded from {test_data_file}")
        else:
            print(f"⚠️ Test data file {test_data_file} not found")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error loading test data: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('--env', required=True, choices=['dev', 'test', 'stage', 'prod'])
    parser.add_argument('--create-db', action='store_true', help='Create database')
    parser.add_argument('--run-migrations', action='store_true', help='Run migrations')
    parser.add_argument('--load-data', action='store_true', help='Load test data')
    
    args = parser.parse_args()
    
    # Environment-specific configuration
    configs = {
        'dev': {
            'db_name': 'posmvp_dev',
            'db_user': 'dev_user',
            'db_password': 'dev_password',
            'db_host': 'localhost',
            'db_port': 5432
        },
        'test': {
            'db_name': 'posmvp_test',
            'db_user': 'test_user',
            'db_password': 'test_password',
            'db_host': 'localhost',
            'db_port': 5432
        },
        'stage': {
            'db_name': 'posmvp_stage',
            'db_user': 'stage_user',
            'db_password': os.getenv('STAGE_DB_PASSWORD'),
            'db_host': 'stage-db.example.com',
            'db_port': 5432
        },
        'prod': {
            'db_name': 'posmvp_prod',
            'db_user': 'prod_user',
            'db_password': os.getenv('PROD_DB_PASSWORD'),
            'db_host': 'prod-db.example.com',
            'db_port': 5432
        }
    }
    
    config = configs[args.env]
    db_url = f"postgresql://{config['db_user']}:{config['db_password']}@{config['db_host']}:{config['db_port']}/{config['db_name']}"
    
    print(f"🗄️ Initializing database for {args.env} environment")
    
    success = True
    
    if args.create_db:
        success &= create_database(
            config['db_name'],
            config['db_user'],
            config['db_password'],
            config['db_host'],
            config['db_port']
        )
    
    if args.run_migrations:
        success &= run_migrations(db_url)
    
    if args.load_data:
        success &= load_test_data(db_url)
    
    if success:
        print("✅ Database initialization completed successfully")
    else:
        print("❌ Database initialization failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Environment Validation Procedures

### Environment Health Check Script

```python
# scripts/validate_environment.py
"""Environment validation script"""

import os
import sys
import time
import requests
import psycopg2
import redis
from typing import Dict, List, Tuple

class EnvironmentValidator:
    """Environment validation utility"""
    
    def __init__(self, config_file: str):
        self.config = self.load_config(config_file)
        self.results = []
    
    def load_config(self, config_file: str) -> Dict:
        """Load environment configuration"""
        import json
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def validate_database(self) -> bool:
        """Validate database connection"""
        try:
            db_config = self.config['database']
            conn = psycopg2.connect(db_config['url'])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.results.append({
                'component': 'Database',
                'status': 'PASS',
                'message': 'Database connection successful',
                'response_time': 0.1
            })
            return True
            
        except Exception as e:
            self.results.append({
                'component': 'Database',
                'status': 'FAIL',
                'message': f'Database connection failed: {str(e)}',
                'response_time': None
            })
            return False
    
    def validate_redis(self) -> bool:
        """Validate Redis connection"""
        try:
            redis_config = self.config.get('redis', {})
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0)
            )
            r.ping()
            
            self.results.append({
                'component': 'Redis',
                'status': 'PASS',
                'message': 'Redis connection successful',
                'response_time': 0.05
            })
            return True
            
        except Exception as e:
            self.results.append({
                'component': 'Redis',
                'status': 'FAIL',
                'message': f'Redis connection failed: {str(e)}',
                'response_time': None
            })
            return False
    
    def validate_license_server(self) -> bool:
        """Validate license server connectivity"""
        try:
            license_config = self.config['license_server']
            start_time = time.time()
            
            response = requests.get(
                f"{license_config['url']}/health",
                timeout=license_config.get('timeout', 30)
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.results.append({
                    'component': 'License Server',
                    'status': 'PASS',
                    'message': 'License server is healthy',
                    'response_time': response_time
                })
                return True
            else:
                self.results.append({
                    'component': 'License Server',
                    'status': 'FAIL',
                    'message': f'License server returned status {response.status_code}',
                    'response_time': response_time
                })
                return False
                
        except Exception as e:
            self.results.append({
                'component': 'License Server',
                'status': 'FAIL',
                'message': f'License server connection failed: {str(e)}',
                'response_time': None
            })
            return False
    
    def validate_email_service(self) -> bool:
        """Validate email service connectivity"""
        try:
            email_config = self.config['email_service']
            start_time = time.time()
            
            response = requests.get(
                f"{email_config['url']}/health",
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.results.append({
                    'component': 'Email Service',
                    'status': 'PASS',
                    'message': 'Email service is healthy',
                    'response_time': response_time
                })
                return True
            else:
                self.results.append({
                    'component': 'Email Service',
                    'status': 'FAIL',
                    'message': f'Email service returned status {response.status_code}',
                    'response_time': response_time
                })
                return False
                
        except Exception as e:
            self.results.append({
                'component': 'Email Service',
                'status': 'FAIL',
                'message': f'Email service connection failed: {str(e)}',
                'response_time': None
            })
            return False
    
    def validate_application(self) -> bool:
        """Validate application health"""
        try:
            app_config = self.config.get('application', {})
            base_url = app_config.get('base_url', 'http://localhost:8000')
            start_time = time.time()
            
            response = requests.get(
                f"{base_url}/health",
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.results.append({
                    'component': 'Application',
                    'status': 'PASS',
                    'message': 'Application is healthy',
                    'response_time': response_time
                })
                return True
            else:
                self.results.append({
                    'component': 'Application',
                    'status': 'FAIL',
                    'message': f'Application returned status {response.status_code}',
                    'response_time': response_time
                })
                return False
                
        except Exception as e:
            self.results.append({
                'component': 'Application',
                'status': 'FAIL',
                'message': f'Application connection failed: {str(e)}',
                'response_time': None
            })
            return False
    
    def validate_all(self) -> bool:
        """Validate all components"""
        print("🔍 Validating environment...")
        
        validations = [
            self.validate_database,
            self.validate_redis,
            self.validate_license_server,
            self.validate_email_service,
            self.validate_application
        ]
        
        all_passed = True
        for validation in validations:
            passed = validation()
            all_passed &= passed
        
        return all_passed
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION RESULTS")
        print("="*60)
        
        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            response_time = f" ({result['response_time']:.3f}s)" if result['response_time'] else ""
            print(f"{status_icon} {result['component']}: {result['message']}{response_time}")
        
        # Summary
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        total = len(self.results)
        
        print(f"\nSummary: {passed}/{total} components healthy")
        
        if passed == total:
            print("🎉 Environment validation PASSED")
        else:
            print("❌ Environment validation FAILED")
    
    def generate_report(self, output_file: str):
        """Generate validation report"""
        import json
        from datetime import datetime
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.config.get('environment', 'unknown'),
            'results': self.results,
            'summary': {
                'total_components': len(self.results),
                'passed_components': len([r for r in self.results if r['status'] == 'PASS']),
                'failed_components': len([r for r in self.results if r['status'] == 'FAIL'])
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Validation report saved to {output_file}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate environment')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--output', help='Output report file path')
    
    args = parser.parse_args()
    
    validator = EnvironmentValidator(args.config)
    
    if validator.validate_all():
        exit_code = 0
    else:
        exit_code = 1
    
    validator.print_results()
    
    if args.output:
        validator.generate_report(args.output)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
```

---

This comprehensive testing environment setup guide provides detailed procedures for establishing all necessary testing environments for the support system and license validation system. The procedures include local development setup, CI/CD configuration, performance testing infrastructure, staging environment deployment, and comprehensive validation procedures to ensure reliable testing across all environments.