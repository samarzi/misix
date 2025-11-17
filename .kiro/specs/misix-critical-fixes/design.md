# Design Document: MISIX Critical Fixes and Refactoring

## Overview

This design document outlines the technical approach for refactoring the MISIX AI Personal Assistant to address critical security, architectural, and code quality issues. The refactoring will be done incrementally to maintain system stability while improving code quality, security, and maintainability.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React PWA)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Pages      │  │   Features   │  │  Components  │     │
│  │ - Analytics  │  │ - Auth       │  │ - Forms      │     │
│  │ - Tasks      │  │ - Tasks      │  │ - Modals     │     │
│  │ - Finances   │  │ - Finances   │  │ - Cards      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                 │
│                    ┌───────▼────────┐                       │
│                    │  API Client    │                       │
│                    │  (Axios + JWT) │                       │
│                    └───────┬────────┘                       │
└────────────────────────────┼──────────────────────────────┘
                             │ HTTPS + JWT
┌────────────────────────────▼──────────────────────────────┐
│                    Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Middleware Layer                         │ │
│  │  - JWT Authentication                                 │ │
│  │  - Rate Limiting                                      │ │
│  │  - CORS                                               │ │
│  │  - Request Logging                                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                            │                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              API Routers                              │ │
│  │  - auth_router                                        │ │
│  │  - tasks_router                                       │ │
│  │  - finances_router                                    │ │
│  │  - notes_router                                       │ │
│  │  - assistant_router                                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                            │                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Service Layer                            │ │
│  │  - AuthService                                        │ │
│  │  - TaskService                                        │ │
│  │  - FinanceService                                     │ │
│  │  - ConversationService                                │ │
│  │  - AIService                                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                            │                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Repository Layer                         │ │
│  │  - UserRepository                                     │ │
│  │  - TaskRepository                                     │ │
│  │  - FinanceRepository                                  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────┬──────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Supabase DB   │
                    │   + Redis Cache │
                    └─────────────────┘
```

## Components and Interfaces

### 1. Authentication System

#### JWT Authentication Middleware

```python
# backend/app/middleware/auth.py

from fastapi import Request, HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta

class JWTAuthMiddleware:
    """Middleware for JWT token validation"""
    
    async def __call__(self, request: Request, call_next):
        # Extract token from Authorization header
        # Validate token signature and expiration
        # Attach user_id to request.state
        # Call next middleware/handler
```

#### Auth Service

```python
# backend/app/services/auth_service.py

class AuthService:
    """Service for authentication operations"""
    
    async def register(self, email: str, password: str, full_name: str) -> User:
        """Register new user with hashed password"""
        
    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token"""
        
    async def verify_token(self, token: str) -> User:
        """Verify JWT token and return user"""
        
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
```

#### Pydantic Models

```python
# backend/app/models/auth.py

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

### 2. Configuration Management

#### Secure Configuration

```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Required settings (no defaults)
    supabase_url: str = Field(..., description="Supabase URL")
    supabase_service_key: str = Field(..., description="Supabase service key")
    jwt_secret_key: str = Field(..., description="JWT secret key")
    yandex_gpt_api_key: str = Field(..., description="Yandex GPT API key")
    yandex_folder_id: str = Field(..., description="Yandex folder ID")
    
    # Optional settings with safe defaults
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    environment: str = "development"
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 3. Backend Modularization

#### New Directory Structure

```
backend/app/
├── api/
│   ├── __init__.py
│   ├── deps.py              # Dependency injection
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── tasks.py
│       ├── finances.py
│       ├── notes.py
│       ├── assistant.py
│       └── health.py
├── core/
│   ├── __init__.py
│   ├── config.py            # Configuration
│   ├── security.py          # Security utilities
│   └── exceptions.py        # Custom exceptions
├── middleware/
│   ├── __init__.py
│   ├── auth.py              # JWT middleware
│   ├── rate_limit.py        # Rate limiting
│   └── logging.py           # Request logging
├── models/
│   ├── __init__.py
│   ├── auth.py              # Auth models
│   ├── task.py              # Task models
│   ├── finance.py           # Finance models
│   └── note.py              # Note models
├── repositories/
│   ├── __init__.py
│   ├── base.py              # Base repository
│   ├── user.py              # User repository
│   ├── task.py              # Task repository
│   └── finance.py           # Finance repository
├── services/
│   ├── __init__.py
│   ├── auth_service.py      # Authentication
│   ├── task_service.py      # Task business logic
│   ├── finance_service.py   # Finance business logic
│   ├── ai_service.py        # AI integration
│   └── conversation_service.py  # Conversation management
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── message.py       # Message handlers
│   │   ├── sleep.py         # Sleep tracking
│   │   └── command.py       # Command handlers
│   ├── yandex_gpt.py
│   └── yandex_speech.py
└── tests/
    ├── __init__.py
    ├── conftest.py          # Test fixtures
    ├── unit/
    │   ├── test_auth_service.py
    │   └── test_task_service.py
    └── integration/
        ├── test_auth_api.py
        └── test_task_api.py
```

#### Service Layer Pattern

```python
# backend/app/services/task_service.py

class TaskService:
    """Business logic for task management"""
    
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo
    
    async def create_task(
        self, 
        user_id: str, 
        task_data: CreateTaskRequest
    ) -> Task:
        """Create a new task with validation"""
        # Validate task data
        # Check user permissions
        # Create task in repository
        # Return created task
    
    async def get_user_tasks(
        self, 
        user_id: str,
        filters: TaskFilters,
        pagination: Pagination
    ) -> PaginatedResponse[Task]:
        """Get user tasks with filtering and pagination"""
        # Apply filters
        # Apply pagination
        # Return paginated results
```

### 4. Frontend Modularization

#### New Directory Structure

```
frontend/src/
├── pages/
│   ├── DashboardPage.tsx    # Main dashboard (simplified)
│   ├── AnalyticsPage.tsx    # Analytics detail
│   ├── TasksPage.tsx        # Tasks management
│   ├── FinancesPage.tsx     # Finance management
│   ├── NotesPage.tsx        # Notes management
│   ├── RemindersPage.tsx    # Reminders
│   └── PersonalPage.tsx     # Personal data
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── hooks/
│   │   │   └── useAuth.ts
│   │   └── api/
│   │       └── authApi.ts
│   ├── tasks/
│   │   ├── components/
│   │   │   ├── TaskList.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   └── TaskCard.tsx
│   │   ├── hooks/
│   │   │   ├── useTasks.ts
│   │   │   └── useTaskForm.ts
│   │   └── types.ts
│   └── finances/
│       ├── components/
│       ├── hooks/
│       └── types.ts
├── components/
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── Form.tsx
│   └── layout/
│       ├── AppLayout.tsx
│       └── Sidebar.tsx
├── hooks/
│   ├── useApi.ts            # Generic API hook
│   ├── useForm.ts           # Generic form hook
│   └── usePagination.ts     # Pagination hook
├── lib/
│   ├── api/
│   │   ├── client.ts        # Axios client with JWT
│   │   └── interceptors.ts  # Request/response interceptors
│   └── validation/
│       └── schemas.ts       # Zod schemas
└── stores/
    ├── authStore.ts         # Auth state
    └── uiStore.ts           # UI state
```

#### Custom Hooks Pattern

```typescript
// frontend/src/features/tasks/hooks/useTasks.ts

export function useTasks(filters?: TaskFilters) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => fetchTasks(filters),
  });
  
  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => refetch(),
  });
  
  return {
    tasks: data?.tasks ?? [],
    isLoading,
    error,
    createTask: createMutation.mutate,
    refetch,
  };
}
```

### 5. Input Validation

#### Backend Validation

```python
# backend/app/models/task.py

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NEW
    deadline: Optional[datetime] = None
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError('Deadline cannot be in the past')
        return v
```

#### Frontend Validation

```typescript
// frontend/src/lib/validation/schemas.ts

import { z } from 'zod';

export const createTaskSchema = z.object({
  title: z.string().min(1).max(500),
  description: z.string().max(5000).optional(),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  status: z.enum(['new', 'in_progress', 'waiting', 'completed', 'cancelled']),
  deadline: z.date().min(new Date()).optional(),
});

export type CreateTaskInput = z.infer<typeof createTaskSchema>;
```

### 6. Error Handling

#### Custom Exceptions

```python
# backend/app/core/exceptions.py

class AppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(AppException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class ValidationError(AppException):
    """Raised when validation fails"""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(message, status_code=422)
        self.errors = errors

class NotFoundError(AppException):
    """Raised when resource not found"""
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} with id {id} not found", status_code=404)
```

#### Error Handler Middleware

```python
# backend/app/middleware/error_handler.py

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": getattr(exc, 'errors', None),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
```

## Data Models

### User Model

```python
class User(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    telegram_id: Optional[int]
    email_verified: bool
    created_at: datetime
    updated_at: datetime
```

### Task Model

```python
class Task(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    priority: TaskPriority
    status: TaskStatus
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### JWT Token Payload

```python
class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str  # "access" or "refresh"
```

## Error Handling

### Error Response Format

```json
{
  "error": "Validation failed",
  "details": {
    "title": ["Field required"],
    "deadline": ["Deadline cannot be in the past"]
  },
  "timestamp": "2025-01-17T10:30:00Z",
  "request_id": "abc-123-def"
}
```

### HTTP Status Codes

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 429: Too Many Requests
- 500: Internal Server Error

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/test_auth_service.py

@pytest.mark.asyncio
async def test_register_user_success(auth_service, user_repo_mock):
    # Arrange
    email = "test@example.com"
    password = "SecurePass123!"
    
    # Act
    user = await auth_service.register(email, password, "Test User")
    
    # Assert
    assert user.email == email
    assert user.password_hash != password  # Password should be hashed
    user_repo_mock.create.assert_called_once()
```

### Integration Tests

```python
# backend/tests/integration/test_auth_api.py

@pytest.mark.asyncio
async def test_login_endpoint(client):
    # Arrange
    await create_test_user(email="test@example.com", password="password123")
    
    # Act
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

### Frontend Tests

```typescript
// frontend/src/features/auth/components/LoginForm.test.tsx

describe('LoginForm', () => {
  it('should validate email format', async () => {
    render(<LoginForm />);
    
    const emailInput = screen.getByLabelText('Email');
    await userEvent.type(emailInput, 'invalid-email');
    
    const submitButton = screen.getByRole('button', { name: 'Login' });
    await userEvent.click(submitButton);
    
    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
  });
});
```

## Security Considerations

### Password Hashing

- Use bcrypt with cost factor 12
- Never store plain text passwords
- Implement password strength requirements

### JWT Security

- Use HS256 algorithm
- Set reasonable expiration times (15 min for access, 7 days for refresh)
- Store refresh tokens securely
- Implement token rotation

### Rate Limiting

- Implement per-IP rate limiting
- Stricter limits for auth endpoints
- Use Redis for distributed rate limiting

### CORS Configuration

- Explicitly list allowed origins
- No wildcard (*) in production
- Include credentials support

### File Upload Security

- Validate file types
- Limit file sizes (max 10MB)
- Scan for malware
- Store in secure location

## Performance Optimization

### Database Optimization

- Use connection pooling
- Implement query result caching
- Add indexes for frequently queried fields
- Use pagination for large result sets

### Caching Strategy

- Cache user sessions in Redis
- Cache frequently accessed data (user profiles, categories)
- Implement cache invalidation on updates
- Use TTL for automatic expiration

### API Response Optimization

- Implement field selection (sparse fieldsets)
- Use compression (gzip)
- Implement ETag for conditional requests
- Minimize payload sizes

## Deployment Considerations

### Environment Variables

Required environment variables:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `JWT_SECRET_KEY`
- `YANDEX_GPT_API_KEY`
- `YANDEX_FOLDER_ID`
- `REDIS_URL`
- `ENVIRONMENT` (development/staging/production)

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {
            "database": await check_database(),
            "redis": await check_redis(),
            "yandex_gpt": await check_yandex_gpt(),
        }
    }
```

### Monitoring

- Log all requests with duration
- Track error rates by endpoint
- Monitor database query performance
- Set up alerts for critical errors

## Migration Strategy

### Phase 1: Security Fixes (Week 1)
1. Implement authentication system
2. Fix configuration security
3. Add input validation
4. Implement rate limiting

### Phase 2: Code Refactoring (Week 2-3)
1. Split handlers.py into modules
2. Implement service layer
3. Split DashboardPage.tsx
4. Create custom hooks

### Phase 3: Testing & Documentation (Week 4)
1. Write unit tests
2. Write integration tests
3. Generate API documentation
4. Update README

### Phase 4: Optimization (Week 5)
1. Implement caching
2. Optimize database queries
3. Add monitoring
4. Performance testing

## Rollback Plan

- Keep old code in separate branches
- Use feature flags for new functionality
- Implement gradual rollout
- Monitor error rates during deployment
- Have rollback scripts ready
