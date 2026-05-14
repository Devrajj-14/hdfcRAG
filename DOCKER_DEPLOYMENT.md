# Docker Deployment Guide - HDFC RAG System

## 🐳 Quick Start

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- At least 4GB RAM available
- 10GB free disk space (for model download)

---

## 🚀 Deployment Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/Devrajj-14/hdfcRAG.git
cd hdfcRAG
```

### Step 2: Build and Start with Docker Compose
```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

**What happens during first run:**
1. Docker builds the image (~5-10 minutes)
2. Installs all Python dependencies
3. Downloads LLaMA 3.2-1B model (~1.5GB) on first API call
4. Starts the FastAPI server on port 8000

### Step 3: Verify Deployment
```bash
# Check if container is running
docker ps

# Check health status
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","components":{"rag":"ready","slm":"ready"}}
```

### Step 4: Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Web UI**: http://localhost:8000 (if index.html is configured)

---

## 📊 Upload CSV Data

### Using cURL
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@your_hdfc_loan_data.csv"
```

### Using Python
```python
import requests

url = "http://localhost:8000/v1/documents/upload"
files = {"files": open("hdfc_loan_data.csv", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Expected Response
```json
{
  "status": "success",
  "files_processed": ["hdfc_loan_data.csv"],
  "chunks_indexed": 1000
}
```

---

## 🔍 Query Examples

### UC-1: Decision Explainer
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why was loan HDFC100005 rejected despite having a guarantor?"
  }'
```

### UC-2: Grievance Handler
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all negative feedback from Delhi branch"
  }'
```

### UC-3: Policy Q&A
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the NPCI integration requirements for business loans?"
  }'
```

---

## 🛠️ Docker Commands

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific service
docker-compose logs app
```

### Stop the Application
```bash
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps data in volumes)
docker-compose down

# Stop and remove everything including volumes (⚠️ deletes data)
docker-compose down -v
```

### Restart the Application
```bash
# Restart without rebuilding
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Access Container Shell
```bash
# Open bash shell in running container
docker-compose exec app bash

# Or using docker directly
docker exec -it hdfc-rag-app bash
```

---

## 📁 Volume Mounts

The docker-compose.yml mounts two directories:

### 1. Data Volume (`./data`)
- **Purpose**: Stores FAISS vector index and metadata
- **Location**: `./data/vector_store/`
- **Files**: 
  - `index.faiss` - Vector embeddings
  - `index.pkl` - Document metadata
- **Persistence**: Data survives container restarts

### 2. Models Volume (`./models`)
- **Purpose**: Stores downloaded LLaMA model
- **Location**: `./models/slm/`
- **Files**: `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (~1.5GB)
- **Persistence**: Model downloads once, reused on restarts

---

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to add environment variables:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=INFO
  - MAX_UPLOAD_SIZE=100MB
```

### Port Configuration

Change the exposed port in `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"  # Access on port 9000 instead of 8000
```

### Resource Limits

Add resource constraints:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

---

## 🐛 Troubleshooting

### Issue: Container won't start
```bash
# Check logs
docker-compose logs app

# Common causes:
# - Port 8000 already in use
# - Insufficient memory
# - Docker daemon not running
```

### Issue: Model download fails
```bash
# Check internet connection
# Manually download model:
mkdir -p models/slm
cd models/slm
wget https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf
```

### Issue: Out of memory
```bash
# Increase Docker memory limit in Docker Desktop settings
# Minimum: 4GB
# Recommended: 8GB
```

### Issue: CSV upload fails
```bash
# Check file size (default limit: 100MB)
# Check CSV format (must have proper headers)
# Check logs: docker-compose logs app
```

### Issue: Slow responses
```bash
# First query is slow (model loading)
# Subsequent queries should be faster
# Check CPU usage: docker stats hdfc-rag-app
```

---

## 🔄 Reset Everything

### Reset Vector Index (keep model)
```bash
# Stop container
docker-compose down

# Delete vector index
rm -rf data/vector_store/*

# Restart
docker-compose up -d
```

### Complete Reset (delete everything)
```bash
# Stop and remove containers
docker-compose down -v

# Delete data and models
rm -rf data/ models/

# Rebuild from scratch
docker-compose up --build
```

---

## 📊 Health Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### Docker Health Status
```bash
# Check container health
docker ps

# Look for "healthy" status
# If "unhealthy", check logs
```

### Manual Health Check
```bash
# Test upload
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@test.txt"

# Test query
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

---

## 🚀 Production Deployment

### Using Docker Compose (Recommended for single server)

1. **Update docker-compose.yml for production:**
```yaml
services:
  app:
    build: .
    container_name: hdfc-rag-prod
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=WARNING
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

2. **Start in production mode:**
```bash
docker-compose -f docker-compose.yml up -d
```

3. **Set up reverse proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using Docker Swarm (For multi-server)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml hdfc-rag

# Scale service
docker service scale hdfc-rag_app=3
```

---

## 📈 Performance Tips

1. **Pre-download Model**: Download model before first query
2. **Use SSD**: Store data/ and models/ on SSD for faster access
3. **Increase Memory**: Allocate at least 8GB RAM to Docker
4. **CPU Cores**: More cores = faster inference
5. **Batch Uploads**: Upload multiple CSVs at once

---

## 🔐 Security Considerations

1. **Network Isolation**: Use Docker networks
2. **Environment Variables**: Store secrets in .env file
3. **Volume Permissions**: Set proper file permissions
4. **Firewall**: Restrict port 8000 access
5. **HTTPS**: Use reverse proxy with SSL

---

## 📝 Maintenance

### Backup Data
```bash
# Backup vector index
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup to remote
rsync -avz data/ user@backup-server:/backups/hdfc-rag/
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### Monitor Disk Usage
```bash
# Check Docker disk usage
docker system df

# Clean up unused images
docker system prune -a
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start in background |
| `docker-compose logs -f` | View logs |
| `docker-compose stop` | Stop containers |
| `docker-compose restart` | Restart containers |
| `docker-compose down` | Stop and remove |
| `docker-compose ps` | List containers |
| `docker-compose exec app bash` | Access shell |

---

## 📞 Support

- **Logs**: `docker-compose logs app`
- **Health**: `curl http://localhost:8000/health`
- **Docs**: http://localhost:8000/docs

---

**Status**: ✅ Ready for Deployment  
**Last Updated**: 2026-05-14  
**Docker Version**: 20.10+  
**Docker Compose Version**: 2.0+
