# Deployment Guide

## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- OpenRouter API key

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd llm-council
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

3. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- Health check: http://localhost:8001/api/health

### Environment Variables

See `.env.example` for all available configuration options.

Required:
- `OPENROUTER_API_KEY`: Your OpenRouter API key

Optional:
- `COUNCIL_MODELS`: Comma-separated list of model identifiers
- `CHAIRMAN_MODEL`: Model for final synthesis
- `RATE_LIMIT_REQUESTS`: Requests per window (default: 10)
- `RATE_LIMIT_WINDOW`: Time window in seconds (default: 60)

### Production Deployment

For production, consider:

1. **Use HTTPS**: Set up a reverse proxy (nginx/Caddy) with SSL
2. **Secure secrets**: Use Docker secrets or environment variable management
3. **Monitoring**: Add logging and monitoring solutions
4. **Backups**: Regular backups of the `data/` directory
5. **Resource limits**: Set memory and CPU limits in docker-compose.yml

### Manual Deployment

**Backend:**
```bash
uv sync
uv run python -m backend.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
# Serve the dist/ folder with your web server
```

## Testing

Run tests with:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=backend --cov-report=html
```

## Health Checks

- Backend: `GET /api/health`
- Frontend: `GET /health` (nginx)

Both should return 200 OK when healthy.
