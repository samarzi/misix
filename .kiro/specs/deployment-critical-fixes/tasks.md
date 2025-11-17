# Implementation Plan

- [x] 1. Configure Python 3.11 runtime
  - Create render.yaml configuration file specifying Python 3.11
  - Add Python version specification to deployment settings
  - Document Python version requirement in README
  - _Requirements: 1.1, 1.4_

- [x] 2. Implement startup validation system
- [x] 2.1 Create startup validator module
  - Create backend/app/core/startup.py with StartupValidator class
  - Implement validation check data models (ValidationCheck, StartupValidationResult)
  - Implement validate_python_version() method
  - Implement validate_environment_variables() method
  - Implement validate_all() orchestration method
  - _Requirements: 4.1, 4.3, 5.1_

- [x] 2.2 Create database validator module
  - Create backend/app/core/database.py with DatabaseValidator class
  - Implement test_connection() method to verify database connectivity
  - Implement verify_schema() method to check required tables exist
  - Implement get_connection_info() method with credential anonymization
  - Create SchemaValidationResult and DatabaseConnectionInfo data models
  - _Requirements: 2.1, 2.3, 2.4, 3.1, 3.4_

- [x] 2.3 Add database URL configuration
  - Update backend/app/core/config.py to add optional database_url field
  - Add validator for database_url format (must be PostgreSQL URL)
  - Update configuration documentation
  - _Requirements: 4.2_

- [x] 3. Enhance application startup sequence
- [x] 3.1 Integrate startup validation into lifespan
  - Update backend/app/web/main.py lifespan function
  - Add startup validator execution before component initialization
  - Implement fail-fast logic for critical validation failures
  - Add warning logging for non-critical issues
  - Add structured logging for all validation results
  - _Requirements: 1.4, 4.3, 5.3, 5.5_

- [x] 3.2 Add database validation to startup
  - Integrate DatabaseValidator into lifespan startup sequence
  - Test database connection before accepting requests
  - Verify schema completeness and log missing tables
  - Add database connection info to startup logs (anonymized)
  - _Requirements: 2.1, 2.3, 2.4, 3.1, 3.3, 3.4, 5.4_

- [x] 4. Simplify Telegram bot initialization
  - Remove Python 3.13 workaround (.job_queue(None)) from backend/app/bot/__init__.py
  - Remove try-catch for weak reference error
  - Restore standard Application.builder().token().build() pattern
  - Enhance error messages for bot initialization failures
  - Keep graceful degradation (app starts even if bot fails)
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 4.4_

- [x] 5. Enhance diagnostic logging
- [x] 5.1 Add startup phase logging
  - Log Python version and platform information on startup
  - Log all installed package versions for python-telegram-bot, fastapi, supabase
  - Add structured logging for each startup phase (config, database, bot, scheduler)
  - Log successful completion of each phase with checkmark emoji
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 5.2 Add database operation logging
  - Add logging to Supabase client operations in backend/app/shared/supabase.py
  - Log database operation attempts (create, update, delete)
  - Log database operation failures with anonymized connection details
  - Add transaction commit/rollback logging
  - _Requirements: 2.3, 2.4, 5.4_

- [x] 5.3 Add error context logging
  - Update error handlers to include full stack traces in logs
  - Add request context to error logs (method, path, user_id)
  - Ensure no sensitive data (passwords, tokens) appears in logs
  - _Requirements: 5.3_

- [x] 6. Update deployment documentation
  - Update DEPLOYMENT.md with Python 3.11 requirement
  - Document new environment variable DATABASE_URL (optional)
  - Add troubleshooting section for common deployment issues
  - Document startup validation checks and expected log output
  - Add checklist for verifying successful deployment
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 7. Create deployment verification script
  - Create backend/scripts/verify_deployment.py script
  - Implement health check endpoint verification
  - Implement database connectivity test
  - Implement bot functionality test (if token provided)
  - Add script to verify all required environment variables are set
  - _Requirements: 3.3, 4.1, 4.3_

- [x] 8. Add integration tests for startup validation
  - Create tests/integration/test_startup.py
  - Test successful startup with all configuration present
  - Test startup failure with missing critical environment variables
  - Test startup with missing optional configuration (bot token)
  - Test database connection validation
  - Test schema validation with missing tables
  - _Requirements: 1.4, 2.1, 3.1, 4.1_

- [x] 9. Add unit tests for validators
  - Create tests/unit/test_startup_validator.py
  - Test each validation check independently with mocked dependencies
  - Test validation result aggregation
  - Create tests/unit/test_database_validator.py
  - Test database connection validation with mock database
  - Test schema validation with various table configurations
  - Test connection info anonymization
  - _Requirements: 2.1, 2.4, 3.1, 3.4_
