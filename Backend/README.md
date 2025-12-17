## 🔒 Security Configuration

For production deployments, you **MUST** set secure values for the following environment variables:

### Critical Secrets (fail-fast in non-dev environments):
- `JWT_SECRET_KEY`: Used for signing JWT tokens. Generate with: `openssl rand -hex 32`
- `FCM_SERVER_KEY`: Firebase Cloud Messaging server key from Firebase Console
- `AI_SERVICE_AUTH_TOKEN`: Internal token for AI service communication

### Environment-specific behavior:
- **Development (`APP_ENV=dev`)**: Default values are allowed but generate warnings
- **Stage/Production (`APP_ENV=stage` or `APP_ENV=prod`)**: 
  - Default values will cause application startup failure
  - Secrets must be at least 16 characters long
  - Common insecure defaults are rejected

### Quick start for production:
```bash
# Generate secure secrets
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export AI_SERVICE_AUTH_TOKEN=$(openssl rand -hex 32)
# Set FCM_SERVER_KEY from Firebase Console
export FCM_SERVER_KEY="your-actual-fcm-key"

# Set environment to production
export APP_ENV=prod

# Start the application
docker compose up --build
```
### Verification:
After startup, check logs for SECURITY_CONFIG_VALIDATED entry confirming all secrets are properly set

## 🌐 CORS Configuration

CORS is configured securely with the following rules:

### Environment-specific behavior:

**Development (`APP_ENV=dev`)**:
- `CORS_ALLOW_CREDENTIALS=true` by default
- Default origins: `["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]`
- If you try to use `["*"]` with credentials, it will automatically fall back to development defaults

**Stage/Production (`APP_ENV=stage` or `APP_ENV=prod`)**:
- `CORS_ALLOW_CREDENTIALS=true` by default
- **MUST** explicitly configure `CORS_ALLOW_ORIGINS`
- **Cannot** use wildcard (`*`) when credentials are enabled (browser security restriction)
- Application will fail to start if origins are not properly configured

### Configuration options:

1. **JSON array format** (recommended):
```bash
CORS_ALLOW_ORIGINS='["https://app.yourdomain.com", "https://admin.yourdomain.com"]'
```
2. **Comma-separated format**: 
```bash
CORS_ALLOW_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
```
3. **Disable credentials** (if not using cookies/auth headers):
```bash
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOW_ORIGINS='["*"]'  # Now wildcard is allowed
```
### Example production configuration:
```bash
# Production environment
APP_ENV=prod

# Explicit origins for your frontend applications
CORS_ALLOW_ORIGINS='["https://app.lifemerge.com", "https://admin.lifemerge.com"]'

# Enable credentials for authentication
CORS_ALLOW_CREDENTIALS=true

# Secure secrets
JWT_SECRET_KEY=your_secure_jwt_secret_here
FCM_SERVER_KEY=your_firebase_server_key
AI_SERVICE_AUTH_TOKEN=your_ai_service_token
```
### Verification:

Check application logs for CORS_CONFIGURATION entry on startup to verify your CORS settings.

## Database schema management

### Local/Dev
В `ENV=local|dev` допускается auto-create таблиц (удобство для разработки).

### Stage/Prod
В `ENV=stage|prod` auto-create запрещен.
Перед запуском обязателен шаг:

```bash
alembic upgrade head
````

Если схема БД не совпадает с Alembic head — сервис не стартует.