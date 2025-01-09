# BackTest AI Platform

## Project Overview
A sophisticated backtesting platform for algorithmic trading strategies, built with FastAPI, React, and PostgreSQL. Features advanced monitoring capabilities and historical data visualization.

## Current Status (as of January 8, 2025)
The project has completed major infrastructure improvements including CI/CD pipeline, monitoring system, caching infrastructure, database test isolation, and cache performance benchmarking.

### Recent Updates
- Completed comprehensive Redis cache documentation
- Added cache performance benchmarking suite
- Implemented distributed caching and replication
- Enhanced monitoring system with Prometheus and Grafana
- Added comprehensive system health checks
- Improved infrastructure automation
- Implemented database test isolation with transaction management
- Enhanced error handling and logging system

### Performance Metrics
- Cache Operations:
  - SET: 0.22ms average
  - GET: 0.29ms average
  - Pipeline: 0.05ms per operation
- Load Testing: 2,123 ops/sec
- Memory Efficiency: ~2MB Redis memory for test data

### In Progress
- Redis cluster production deployment
- Database state snapshots implementation
- Parallel test support
- Error handling strategy completion
- Advanced monitoring features

### Known Issues
- Distributed cache testing requires cluster setup
- Database schema versioning for testing needed

### Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 5.0+
- Node.js 18+
- Prometheus 2.45+
- Grafana 10.0+
- Terraform 1.0.0+
- AWS CLI configured

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/backtest.git
cd backtest
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Start monitoring services:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

6. Deploy infrastructure (if using AWS):
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Development Setup
1. Start backend server:
```bash
uvicorn main:app --reload
```

2. Start frontend development server:
```bash
cd frontend
npm install
npm start
```

3. Access services:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9091

### Running Tests
The test suite has been significantly improved with proper database isolation:
```bash
# Run all tests
pytest -v

# Run specific test module
pytest tests/core/database/test_test_utils.py -v

# Run with coverage
pytest --cov=backtest --cov-report=term-missing -v
```

Key test improvements:
- Proper transaction isolation
- Automatic rollback after tests
- Improved error handling
- Better test organization

## Project Structure
```
backtest/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration versions
│   └── env.py                 # Alembic configuration
├── api/                        # API implementation
│   ├── endpoints/              # API endpoint handlers
│   ├── middleware/             # Request/response middleware
│   ├── routers/               # API route definitions
│   ├── schemas/               # API request/response schemas
│   └── security/              # API security
├── core/                       # Core application framework
│   ├── cache/                 # Caching system
│   │   ├── decorators/       # Cache decorators
│   │   └── monitor/          # Cache monitoring
│   ├── config/               # Configuration management
│   ├── database/             # Database utilities
│   ├── errors/               # Error definitions
│   ├── exceptions/           # Custom exceptions
│   ├── logging/              # Logging configuration
│   ├── models/               # Core data models
│   ├── monitoring/           # System monitoring
│   ├── risk_management/      # Risk management core
│   ├── security/             # Authentication/authorization
│   └── services/             # Business services
├── data/                      # Data management
│   ├── pipeline/             # Data processing pipelines
│   ├── processing/           # Data processors
│   ├── providers/            # Data provider implementations
│   ├── sources/              # Data source definitions
│   └── storage/              # Data storage utilities
├── database/                  # Database layer
│   ├── models/               # Database models
│   ├── migrations/           # Database migrations
│   └── session.py            # Session management
├── Frontend/                  # Web interface
├── indicators/                # Technical indicators
│   └── advanced_indicators.py
├── infrastructure/            # Infrastructure management
├── models/                    # Domain models
├── monitoring/                # Monitoring system
│   ├── grafana/              # Grafana dashboards
│   └── prometheus/           # Prometheus configuration
├── project_context/           # Development history
│   ├── checkpoints/          # Development milestones
│   └── checklists/           # Development guidelines
├── risk/                      # Risk management
│   ├── analysis/             # Risk analysis tools
│   ├── management/           # Risk management
│   └── monitoring/           # Risk monitoring
├── schemas/                   # Data validation schemas
│   ├── backtest.py          # Backtesting schemas
│   ├── metrics.py           # Metrics schemas
│   ├── strategy.py          # Strategy schemas
│   └── token.py             # Authentication schemas
├── scripts/                   # Utility scripts
│   ├── database/            # Database management
│   ├── deployment/          # Deployment scripts
│   └── testing/             # Test utilities
├── strategies/                # Trading strategies
│   ├── base/                # Strategy base classes
│   ├── factory/             # Strategy creation
│   └── implementations/     # Strategy implementations
├── terraform/                 # Infrastructure as Code
│   ├── modules/             # Terraform modules
│   │   ├── compute/        # Compute resources
│   │   ├── database/       # Database resources
│   │   ├── monitoring/     # Monitoring setup
│   │   ├── network/        # Network configuration
│   │   └── security/       # Security groups
│   └── environments/        # Environment configs
├── tests/                     # Test suite
│   ├── api/                 # API tests
│   ├── core/                # Core tests
│   ├── database/            # Database tests
│   ├── integration/         # Integration tests
│   ├── monitoring/          # Monitoring tests
│   ├── security/            # Security tests
│   └── utils/               # Test utilities
├── .env                      # Environment variables
├── .env.test                 # Test environment
├── alembic.ini              # Alembic config
├── docker-compose.yml       # Docker composition
├── main.py                  # Application entry
├── pytest.ini              # PyTest config
└── requirements.txt         # Dependencies
```

### Key Directory Relationships

1. **Core Application Components**
   - `api/` → `core/` → `database/`: Main application flow
   - `strategies/` → `indicators/` → `data/`: Trading logic flow
   - `risk/` → `monitoring/`: Risk tracking flow

2. **Data Flow**
   - `data/sources/` → `data/pipeline/` → `data/storage/`
   - `database/models/` ↔ `schemas/`
   - `monitoring/` → `grafana/` → `prometheus/`

3. **Development Flow**
   - `scripts/` → `terraform/` → `infrastructure/`
   - `tests/` → `project_context/` → `docs/`

4. **Security Flow**
   - `api/security/` → `core/security/` → `database/`
   - `schemas/` → `models/` → `database/models/`

## Database Structure

The application uses PostgreSQL with the following key tables:

- `users`: Core user management and authentication
- `strategies`: Trading strategy storage and management
- `backtests`: Backtest execution records
- `trades`: Individual trade tracking
- `metrics`: Performance metrics storage
- `audit_logs`: System audit tracking

### Database Migrations

We use Alembic for database migrations. Key commands:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Show current version
alembic current

# Show migration history
alembic history
```

### Authentication System

The authentication system uses:
- JWT tokens with Redis backend
- Role-based access control
- Comprehensive audit logging
- Rate limiting for security
- Session management
- Secure password policies

## Development Setup

1. Install PostgreSQL and create databases:
   ```bash
   createdb backtest
   createdb backtest_test
   ```

2. Install required PostgreSQL extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   CREATE EXTENSION IF NOT EXISTS "hstore";
   CREATE EXTENSION IF NOT EXISTS "btree_gist";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   ```

3. Set up Redis for session management:
   ```bash
   # Install Redis
   # Start Redis server
   redis-server

   # Verify Redis connection
   redis-cli ping
   ```

4. Run database migrations:
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Run migrations
   alembic upgrade head
   ```

## Features

### Monitoring System
- Basic Prometheus metrics integration
- Initial Grafana dashboard setup
- Historical timestamp support (needs fixes)
- Custom metric collectors (under revision)
- Performance monitoring (partial implementation)

### Trading Strategies
- Mean reversion strategy implementation
- Trend following capabilities
- Real-time performance tracking
- Risk management integration
- Position sizing and management

### Error Handling
- Global error handler implementation
- Custom exception hierarchy
- Error logging with context
- Retry mechanisms for transient failures
- Error reporting system (needs testing)

### Database Management
- PostgreSQL with SQLAlchemy ORM
- Basic migration system
- Robust test database isolation
- Transaction management
- Data validation checks
- Automatic cleanup mechanisms

### Testing
- Comprehensive test suite
- Test database isolation framework
- Parallel test execution support
- Test coverage tracking

## Monitoring Setup

### Grafana Dashboards
The platform includes several pre-configured Grafana dashboards:

1. **System Overview Dashboard**
   - Real-time CPU and Memory usage gauges
   - Request latency tracking
   - Error rate monitoring
   - System performance metrics

2. **Backtest Performance Dashboard**
   - Portfolio value tracking
   - Trade execution metrics
   - Strategy performance analytics
   - Risk metrics visualization

### Prometheus Configuration
- Custom metric collectors for system and application metrics
- Configured to run on port 9091 to avoid conflicts
- Automated metric collection every 15 seconds
- Integration with Grafana for visualization
- Support for historical data retention

### Monitoring Features
- Real-time system metrics tracking
- Automated dashboard provisioning
- Pre-configured data source connections
- Custom metric collectors for:
  - System resources (CPU, Memory)
  - Application performance
  - Database operations
  - Cache efficiency
  - Alert conditions

### Alert Management
- Configurable threshold-based alerts
- Support for multiple notification channels
- Integration with external alert managers
- Custom alert rules for critical metrics

### Cache System
The platform uses Redis for caching with the following features:
- Automatic function result caching
- Cache warming strategies
- Memory-based eviction
- Performance monitoring
- Pipeline operations support

Performance metrics:
- Basic operations: ~1,632 ops/sec
- Pipeline operations: ~282 ops/sec

## CI/CD Pipeline
- Automated deployment to staging/production
- Blue/green deployment strategy
- Infrastructure as code with Terraform
- Automated health checks
- Rollback mechanisms
