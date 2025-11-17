# Design Document

## Overview

This design addresses two critical deployment failures in the MISIX application:

1. **Python 3.13 Compatibility Issue**: The `python-telegram-bot==21.0.1` library fails with `TypeError: cannot create weak reference to 'Application' object` on Python 3.13 due to changes in weak reference handling.

2. **Database Persistence Failure**: Web application data operations fail silently, preventing users from saving tasks, notes, and other entities.

The solution involves downgrading to Python 3.11 (stable and well-supported), enhancing database connection validation, implementing startup health checks, and adding comprehensive diagnostic logging.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Render Platform                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Python 3.11 Runtime                      │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         FastAPI Application                     │  │  │
│  │  │  ┌──────────────┐      ┌──────────────┐        │  │  │
│  │  │  │   Startup    │      │   Lifespan   │        │  │  │
│  │  │  │  Validator   │─────▶│   Manager    │        │  │  │
│  │  │  └──────────────┘      └──────────────┘        │  │  │
│  │  │         │                      │                │  │  │
│  │  │         ▼                      ▼                │  │  │
│  │  │  ┌──────────────┐      ┌──────────────┐        │  │  │
│  │  │  │   Database   │      │  Telegram    │        │  │  │
│  │  │  │  Connection  │      │     Bot      │        │  │  │
│  │  │  │   Validator  │      │  (Optional)  │        │  │  │
│  │  │  └──────────────┘      └──────────────┘        │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│                  ┌─────────────────┐                         │
│                  │  Supabase DB    │                         │
│                  │  (PostgreSQL)   │                         │
│                  └─────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Python Version Downgrade**: Use Python 3.11 instead of 3.13
   - Rationale: `python-telegram-bot` library has known compatibility issues with Python 3.13
   - Python 3.11 is stable, well-tested, and fully supported by all dependencies
   - Minimal migration effort (no code changes required)

2. **Graceful Bot Degradation**: Allow application to start even if Telegram bot fails
   - Rationale: Web API should remain functional even if bot component fails
   - Current implementation already has this pattern but needs enhancement

3. **Database Connection Validation**: Add explicit connection testing on startup
   - Rationale: Silent database failures prevent data persistence
   - Early detection prevents user-facing errors

4. **Comprehensive Logging**: Add detailed diagnostic information at each startup phase
   - Rationale: Render logs are the primary debugging tool in production
   - Helps identify configuration issues quickly

## Components and Interfaces

### 1. Runtime Configuration

**File**: `render.yaml` (new) or Render dashboard settings

**Purpose**: Specify Python version and build configuration

**Interface**:
```yaml
services:
  - type: web
    name: misix-backend
    runtime: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn app.web.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
```

### 2. Startup Validator

**File**: `backend/app/core/startup.py` (new)

**Purpose**: Validate all required configuration and connections before application starts

**Interface**:
```python
class StartupValidator:
    """Validates system requirements and configuration on startup."""
    
    async def validate_all(self) -> StartupValidationResult:
        """Run all validation checks."""
        
    async def validate_python_version(self) -> ValidationCheck:
        """Verify Python version compatibility."""
        
    async def validate_environment_variables(self) -> ValidationCheck:
        """Verify all required env vars are present."""
        
    async def validate_database_connection(self) -> ValidationCheck:
        """Test database connectivity and schema."""
        
    async def validate_telegram_bot(self) -> ValidationCheck:
        """Verify Telegram bot token (optional)."""
```

**Data Models**:
```python
@dataclass
class ValidationCheck:
    name: str
    passed: bool
    message: str
    details: dict[str, Any] | None = None

@dataclass
class StartupValidationResult:
    checks: list[ValidationCheck]
    all_passed: bool
    critical_failures: list[ValidationCheck]
    warnings: list[ValidationCheck]
```

### 3. Database Connection Validator

**File**: `backend/app/core/database.py` (new)

**Purpose**: Test database connectivity and verify schema

**Interface**:
```python
class DatabaseValidator:
    """Validates database connection and schema."""
    
    async def test_connection(self) -> bool:
        """Test basic database connectivity."""
        
    async def verify_schema(self) -> SchemaValidationResult:
        """Verify all required tables exist."""
        
    async def get_connection_info(self) -> dict[str, Any]:
        """Get anonymized connection information for logging."""

@dataclass
class SchemaValidationResult:
    all_tables_exist: bool
    missing_tables: list[str]
    existing_tables: list[str]
```

### 4. Enhanced Lifespan Manager

**File**: `backend/app/web/main.py` (modified)

**Purpose**: Orchestrate startup validation and component initialization

**Changes**:
- Add startup validator execution before component initialization
- Add database connection validation
- Enhance logging with structured diagnostic information
- Fail fast on critical errors, warn on non-critical issues

### 5. Telegram Bot Initialization

**File**: `backend/app/bot/__init__.py` (modified)

**Purpose**: Remove Python 3.13 workaround, rely on Python 3.11 compatibility

**Changes**:
- Remove `.job_queue(None)` workaround
- Remove try-catch for weak reference error
- Simplify initialization logic
- Add better error messages

### 6. Configuration Enhancement

**File**: `backend/app/core/config.py` (modified)

**Purpose**: Add database URL configuration and validation

**Changes**:
```python
class Settings(BaseSettings):
    # Add optional DATABASE_URL for direct PostgreSQL access
    database_url: Optional[str] = Field(
        default=None,
        description="Direct PostgreSQL connection URL (optional, for Alembic)"
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format if provided."""
        if v and not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
```

## Data Models

### Startup Validation Models

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any

class ValidationSeverity(Enum):
    """Severity level for validation checks."""
    CRITICAL = "critical"  # Must pass for app to start
    WARNING = "warning"    # Should pass but app can continue
    INFO = "info"          # Informational only

@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    name: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: dict[str, Any] | None = None
    exception: Exception | None = None

@dataclass
class StartupValidationResult:
    """Aggregated results of all startup validations."""
    checks: list[ValidationCheck]
    
    @property
    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return all(check.passed for check in self.checks)
    
    @property
    def critical_failures(self) -> list[ValidationCheck]:
        """Get all critical failures."""
        return [
            check for check in self.checks
            if not check.passed and check.severity == ValidationSeverity.CRITICAL
        ]
    
    @property
    def warnings(self) -> list[ValidationCheck]:
        """Get all warnings."""
        return [
            check for check in self.checks
            if not check.passed and check.severity == ValidationSeverity.WARNING
        ]
```

### Database Validation Models

```python
@dataclass
class DatabaseConnectionInfo:
    """Anonymized database connection information."""
    host: str
    port: int
    database: str
    user: str
    ssl_enabled: bool
    connection_pool_size: int | None = None

@dataclass
class SchemaValidationResult:
    """Result of database schema validation."""
    all_tables_exist: bool
    required_tables: list[str]
    existing_tables: list[str]
    missing_tables: list[str]
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.all_tables_exist:
            return f"✅ All {len(self.required_tables)} required tables exist"
        return f"❌ Missing {len(self.missing_tables)} tables: {', '.join(self.missing_tables)}"
```

## Error Handling

### Error Categories

1. **Critical Errors** (Application cannot start):
   - Missing required environment variables (SUPABASE_URL, JWT_SECRET_KEY, etc.)
   - Invalid configuration values
   - Database connection failure
   - Python version incompatibility

2. **Warning Errors** (Application can start with degraded functionality):
   - Telegram bot token missing or invalid
   - Optional services unavailable (Redis, etc.)
   - Missing non-critical tables

3. **Info Messages** (Informational only):
   - Successful validation checks
   - Configuration values (sanitized)
   - Component initialization status

### Error Handling Strategy

```python
async def lifespan(app: FastAPI):
    """Enhanced lifespan with validation."""
    logger.info("🚀 Starting MISIX application...")
    
    # Phase 1: Validate configuration
    validator = StartupValidator()
    result = await validator.validate_all()
    
    # Log all validation results
    for check in result.checks:
        if check.passed:
            logger.info(f"✅ {check.name}: {check.message}")
        elif check.severity == ValidationSeverity.CRITICAL:
            logger.error(f"❌ {check.name}: {check.message}", extra=check.details)
        else:
            logger.warning(f"⚠️  {check.name}: {check.message}", extra=check.details)
    
    # Fail fast on critical errors
    if result.critical_failures:
        logger.error("❌ Critical validation failures detected. Cannot start application.")
        for failure in result.critical_failures:
            logger.error(f"  - {failure.name}: {failure.message}")
        raise RuntimeError("Startup validation failed")
    
    # Warn about non-critical issues
    if result.warnings:
        logger.warning(f"⚠️  {len(result.warnings)} warnings detected. Application will start with degraded functionality.")
    
    # Phase 2: Initialize components
    # ... rest of initialization
```

### Logging Strategy

All logs include:
- Timestamp (ISO 8601)
- Log level (INFO, WARNING, ERROR)
- Component name
- Message
- Structured data (JSON format in production)

Example log output:
```json
{
  "timestamp": "2025-11-17T19:30:00.123Z",
  "level": "ERROR",
  "component": "startup.database",
  "message": "Database connection failed",
  "details": {
    "host": "db.xxx.supabase.co",
    "port": 5432,
    "database": "postgres",
    "error": "connection timeout",
    "retry_count": 3
  }
}
```

## Testing Strategy

### Unit Tests

1. **Startup Validator Tests** (`tests/unit/test_startup_validator.py`):
   - Test each validation check independently
   - Mock environment variables and external dependencies
   - Verify error messages and severity levels

2. **Database Validator Tests** (`tests/unit/test_database_validator.py`):
   - Test connection validation with mock database
   - Test schema validation with various table configurations
   - Test connection info anonymization

### Integration Tests

1. **Startup Integration Tests** (`tests/integration/test_startup.py`):
   - Test full startup sequence with real configuration
   - Test failure scenarios (missing env vars, bad database URL)
   - Test graceful degradation (bot disabled, optional services unavailable)

2. **Database Integration Tests** (`tests/integration/test_database.py`):
   - Test real database connection
   - Test schema validation against actual Supabase database
   - Test data persistence operations

### Manual Testing Checklist

1. **Python Version Verification**:
   - Deploy with Python 3.11 specified
   - Verify bot initializes without weak reference error
   - Verify all handlers are registered

2. **Database Connection**:
   - Create task via web API
   - Verify task appears in database
   - Verify task appears in web UI

3. **Telegram Bot**:
   - Send message to bot
   - Verify bot responds
   - Verify message is logged to database

4. **Error Scenarios**:
   - Deploy with missing DATABASE_URL (should fail)
   - Deploy with invalid SUPABASE_URL (should fail)
   - Deploy without TELEGRAM_BOT_TOKEN (should start with warning)

## Deployment Configuration

### Render Configuration

**Option 1: render.yaml** (recommended)
```yaml
services:
  - type: web
    name: misix-backend
    runtime: python
    plan: starter
    region: frankfurt
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn app.web.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
      # Secrets from Render dashboard
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: JWT_SECRET_KEY
        sync: false
      - key: YANDEX_GPT_API_KEY
        sync: false
      - key: YANDEX_FOLDER_ID
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
```

**Option 2: Render Dashboard Settings**
- Navigate to Service Settings → Environment
- Set "Python Version" to "3.11"
- Verify all environment variables are set

### Environment Variables Checklist

**Required** (application will not start without these):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`
- `JWT_SECRET_KEY` (min 32 characters)
- `YANDEX_GPT_API_KEY`
- `YANDEX_FOLDER_ID`

**Optional** (application will start with warnings):
- `TELEGRAM_BOT_TOKEN` (bot functionality disabled if missing)
- `DATABASE_URL` (for Alembic migrations)
- `REDIS_URL` (for distributed rate limiting)
- `FRONTEND_ALLOWED_ORIGINS` (defaults to localhost)

### Database Setup

The application uses Supabase PostgreSQL. Schema should be initialized using Alembic:

```bash
# On first deployment or after schema changes
cd backend
export DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
alembic upgrade head
```

Alternatively, the startup validator can detect missing tables and provide clear error messages.

## Migration Path

### Step 1: Update Python Version
1. Add `render.yaml` to repository root with Python 3.11 specified
2. Or update Python version in Render dashboard
3. Trigger redeploy

### Step 2: Implement Startup Validation
1. Create `backend/app/core/startup.py` with validation logic
2. Create `backend/app/core/database.py` with database validation
3. Update `backend/app/web/main.py` to use startup validator
4. Update `backend/app/core/config.py` to add DATABASE_URL field

### Step 3: Simplify Bot Initialization
1. Remove Python 3.13 workarounds from `backend/app/bot/__init__.py`
2. Restore standard bot initialization
3. Add better error messages

### Step 4: Deploy and Verify
1. Deploy to Render
2. Monitor startup logs for validation results
3. Test bot functionality
4. Test web API data persistence
5. Verify all components are operational

## Performance Considerations

- **Startup Time**: Validation adds ~2-3 seconds to startup time (acceptable for deployment)
- **Database Connection**: Connection pooling handled by Supabase client (no changes needed)
- **Logging Overhead**: Structured logging adds minimal overhead (<1% CPU)
- **Memory Usage**: No significant memory impact from validation components

## Security Considerations

- **Credential Logging**: All database connection info is anonymized before logging
- **Error Messages**: Error messages do not expose sensitive configuration values
- **Environment Variables**: Secrets remain in environment variables, never logged
- **Database URL**: If DATABASE_URL is provided, it's validated but never logged in full
