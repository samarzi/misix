# MISIX Backend

AI Personal Assistant backend built with FastAPI.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (via Supabase)
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd misix-project/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your actual values
```

**Required environment variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `JWT_SECRET_KEY` - Secret key for JWT (min 32 chars)
- `YANDEX_GPT_API_KEY` - Yandex GPT API key
- `YANDEX_FOLDER_ID` - Yandex Cloud folder ID

**Generate secrets:**
```bash
# Generate JWT secret
openssl rand -hex 32

# Generate encryption key (optional)
openssl rand -hex 32
```

5. **Run the application**
```bash
uvicorn app.web.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication

The API uses JWT (JSON Web Token) authentication. See [Authentication Documentation](docs/AUTHENTICATION.md) for details.

### Quick Example

```bash
# Register
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Use the access_token from login response
curl -X GET http://localhost:8000/api/v2/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── deps.py       # Dependencies (auth, etc.)
│   │   └── routers/      # Route handlers
│   │       └── auth.py   # Authentication endpoints
│   ├── bot/              # Telegram bot
│   │   ├── handlers.py   # Bot message handlers
│   │   ├── yandex_gpt.py # Yandex GPT integration
│   │   └── yandex_speech.py
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration
│   │   ├── security.py   # Security utilities
│   │   ├── exceptions.py # Custom exceptions
│   │   ├── logging.py    # Logging configuration
│   │   └── validators.py # Input validation
│   ├── middleware/       # Middleware components
│   │   ├── auth.py       # JWT authentication
│   │   ├── rate_limit.py # Rate limiting
│   │   ├── logging.py    # Request logging
│   │   └── error_handler.py # Error handling
│   ├── models/           # Pydantic models
│   │   ├── auth.py       # Auth models
│   │   ├── task.py       # Task models
│   │   ├── note.py       # Note models
│   │   ├── finance.py    # Finance models
│   │   └── common.py     # Common models
│   ├── services/         # Business logic
│   │   └── auth_service.py
│   ├── shared/           # Shared utilities (legacy)
│   │   ├── config.py     # Legacy config (deprecated)
│   │   └── supabase.py   # Supabase client
│   └── web/              # Web application
│       ├── main.py       # FastAPI app
│       └── routers/      # Legacy routers
├── docs/                 # Documentation
│   └── AUTHENTICATION.md
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

All configuration is done via environment variables. See `.env.example` for all available options.

### Key Settings

**Application:**
- `ENVIRONMENT` - Environment (development/staging/production)
- `DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `LOG_FORMAT` - Log format (json/text)

**Security:**
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token lifetime (default: 15)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token lifetime (default: 7)
- `RATE_LIMIT_PER_MINUTE` - General rate limit (default: 60)
- `RATE_LIMIT_AUTH_PER_MINUTE` - Auth endpoint rate limit (default: 5)

**File Uploads:**
- `MAX_UPLOAD_SIZE_MB` - Maximum file size (default: 10)
- `ALLOWED_UPLOAD_EXTENSIONS` - Allowed file extensions

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

Logs are output to stdout in JSON format (production) or human-readable format (development).

**Log Levels:**
- `DEBUG` - Detailed information for debugging
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

**Structured Logging:**
All logs include:
- `timestamp` - ISO 8601 timestamp
- `level` - Log level
- `message` - Log message
- `request_id` - Correlation ID for requests
- `user_id` - User ID (if authenticated)
- `duration_ms` - Request duration (for request logs)

## 🚢 Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `JWT_SECRET_KEY` (min 32 chars)
- [ ] Configure `FRONTEND_ALLOWED_ORIGINS` (no wildcards)
- [ ] Enable HTTPS
- [ ] Set up Redis for caching (optional)
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Review rate limits
- [ ] Test authentication flow
- [ ] Test error handling

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t misix-backend .

# Run
docker run -p 8000:8000 --env-file .env misix-backend
```

## 🐛 Troubleshooting

### "Configuration Error"

**Problem:** Application fails to start with configuration error.

**Solution:** Ensure all required environment variables are set in `.env` file.

### "Database connection not available"

**Problem:** Cannot connect to Supabase.

**Solution:** 
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Verify Supabase project is active
- Check network connectivity

### "Invalid or expired token"

**Problem:** Authentication fails with token error.

**Solution:**
- Token may have expired (access tokens expire after 15 minutes)
- Use refresh token to get new access token
- Check `JWT_SECRET_KEY` hasn't changed

### "Rate limit exceeded"

**Problem:** Too many requests error.

**Solution:**
- Wait for the retry-after period
- Reduce request frequency
- Adjust rate limits in configuration if needed

## 📝 Development

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions small and focused

### Adding New Endpoints

1. Create Pydantic models in `app/models/`
2. Create service in `app/services/`
3. Create router in `app/api/routers/`
4. Register router in `app/web/main.py`
5. Add tests in `tests/`

### Database Migrations

Database schema is managed in `infra/supabase/schema.sql`.

To apply changes:
1. Update `schema.sql`
2. Run migrations in Supabase dashboard
3. Test locally

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run linters and tests
5. Submit a pull request

## 📄 License

MIT License

## 🆘 Support

For issues or questions:
- Check documentation in `docs/`
- Review API docs at `/docs`
- Check application logs
- Contact the development team
