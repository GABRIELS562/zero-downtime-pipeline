# Finance Trading Application

A high-performance, SOX-compliant trading system built with FastAPI, designed for zero-downtime deployment with comprehensive monitoring and compliance features.

## 🚀 Features

### Core Trading Capabilities
- **High-Frequency Trading**: Ultra-low latency order processing (<50ms)
- **Multi-Asset Support**: Equities, options, forex, cryptocurrencies
- **Real-Time Market Data**: WebSocket-based live price feeds with dual data sources
- **Advanced Order Types**: Market, limit, stop, stop-limit orders
- **Risk Management**: Real-time position monitoring and risk controls

### Market Data Sources
- **Simulation Mode** (Default): High-frequency synthetic data with realistic price movements
- **Alpha Vantage Integration**: Optional real market data with intelligent fallback
- **Hybrid Approach**: Real data for key symbols, simulation for ultra-low latency

### Compliance & Security
- **SOX Compliance**: Comprehensive audit trails and financial controls (SA equivalent: Companies Act 71 & King IV)
- **Immutable Logging**: Cryptographic integrity for all transactions
- **Role-Based Access**: Multi-level security with proper authorization
- **Data Encryption**: End-to-end encryption for sensitive data
- **Regulatory Reporting**: Automated compliance report generation

### DevOps & Infrastructure
- **Zero-Downtime Deployment**: Blue-green and canary deployment strategies
- **Comprehensive Monitoring**: Prometheus metrics, Grafana dashboards
- **Health Checks**: Multi-level health validation for system components
- **Auto-Scaling**: Kubernetes-ready with horizontal pod autoscaling
- **Disaster Recovery**: Automated backup and restore procedures

## 🛠 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Advanced ORM with async support
- **PostgreSQL**: Primary database with ACID compliance
- **Redis**: High-performance caching and session storage
- **Pydantic**: Data validation and serialization

### Infrastructure
- **Docker**: Containerized deployment
- **Kubernetes**: Container orchestration
- **Nginx**: Load balancer and reverse proxy
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───▶│   Trading API   │───▶│   Database      │
│   (Nginx)       │    │   (FastAPI)     │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Cache Layer   │              │
         │              │   (Redis)       │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Compliance    │    │   Risk Mgmt     │
│   (Prometheus)  │    │   (SOX Audit)   │    │   (Real-time)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development Setup

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd finance-trading
   cp config/.env.example .env
   ```

2. **Setup Volumes**
   ```bash
   ./scripts/setup-volumes.sh
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize Database**
   ```bash
   docker-compose run --rm db-init
   ```

5. **Configure Market Data (Optional)**
   ```bash
   # For real market data, get free API key from Alpha Vantage
   # https://www.alphavantage.co/support/#api-key
   # Then update .env file:
   MARKET_DATA_PROVIDER=alphavantage
   ALPHA_VANTAGE_API_KEY=your_actual_api_key
   ```

6. **Access Application**
   - API Documentation: http://localhost:8000/docs
   - Grafana Dashboards: http://localhost:3000
   - Prometheus Metrics: http://localhost:9091
   - Market Data Status: http://localhost:8000/api/v1/market-data/status

### Environment-Specific Deployment

#### Development
```bash
./scripts/deploy.sh development up
```

#### Staging
```bash
./scripts/deploy.sh staging up
```

#### Production
```bash
./scripts/deploy.sh production up
```

## 📁 Project Structure

```
finance-trading/
├── src/                          # Application source code
│   ├── api/                      # API endpoints
│   ├── database/                 # Database models and migrations
│   ├── services/                 # Business logic services
│   ├── middleware/               # Custom middleware
│   └── main.py                   # Application entry point
├── config/                       # Configuration files
│   ├── development.env           # Development environment
│   ├── staging.env              # Staging environment
│   └── production.env           # Production environment
├── scripts/                      # Deployment and utility scripts
│   ├── deploy.sh                # Main deployment script
│   ├── setup-volumes.sh         # Volume setup script
│   └── db-init/                 # Database initialization
├── monitoring/                   # Monitoring configurations
│   ├── prometheus.yml           # Prometheus configuration
│   ├── grafana/                 # Grafana dashboards
│   └── alert_rules.yml          # Alerting rules
├── nginx/                        # Load balancer configurations
├── docker-compose.yml           # Development environment
├── docker-compose.staging.yml   # Staging environment
├── docker-compose.prod.yml      # Production environment
└── Dockerfile                   # Multi-stage Docker build
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=trading_user
DB_PASSWORD=trading_password
DB_NAME=trading_db

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Trading
MARKET_DATA_PROVIDER=simulation
ORDER_EXECUTION_MODE=simulation

# Alpha Vantage (Optional - for real market data)
ALPHA_VANTAGE_API_KEY=your_free_api_key_here

# Compliance
SOX_COMPLIANCE_ENABLED=true
AUDIT_LOG_LEVEL=info
```

### Docker Compose Profiles

- **Default**: Core application services
- **dev-tools**: Development tools (pgAdmin, Redis Commander)
- **testing**: Test runners and validation
- **monitoring**: Full monitoring stack

## 📊 Monitoring & Observability

### Health Checks

The application provides comprehensive health check endpoints:

- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe  
- `/health/startup` - Startup probe
- `/health/ultra-low-latency` - <50ms performance check
- `/health/business` - Business metrics validation

### Metrics

Key performance indicators:

- **Latency**: 95th percentile response times
- **Throughput**: Orders per second, market data updates
- **Business**: Trading volume, revenue, success rates
- **Compliance**: Audit events, violations, data integrity

### Alerting

Critical alerts configured:

- Trading application downtime
- High latency (>50ms)
- Market data feed issues
- Compliance violations
- Database connectivity problems

## 🔒 Security & Compliance

### SOX Compliance Features

- **Immutable Audit Trails**: All financial transactions logged
- **Cryptographic Integrity**: Hash chains for data validation
- **Access Controls**: Role-based permissions and authentication
- **Data Retention**: 7-year retention policy enforcement
- **Regular Audits**: Automated compliance checking

### Security Best Practices

- **Non-root Containers**: All services run as non-privileged users
- **Network Segmentation**: Isolated container networks
- **Secret Management**: Environment-based secret injection
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API endpoint protection

## 🚀 Deployment

### Deployment Strategies

1. **Blue-Green Deployment**
   - Zero-downtime deployments
   - Instant rollback capability
   - Full traffic switching

2. **Canary Deployment**
   - Gradual traffic shifting
   - Risk mitigation
   - Performance validation

### Trading Hours Awareness

The deployment system automatically:
- Blocks deployments during trading hours (9:30 AM - 4:00 PM EST)
- Allows deployments during market close
- Provides override options for emergency deployments

### Rollback Procedures

```bash
# Automatic rollback on failure
./scripts/deploy.sh production up

# Manual rollback
./scripts/deploy.sh production --rollback
```

## 📈 Performance

### Benchmarks

- **API Response Time**: <50ms 95th percentile
- **Order Processing**: >1000 orders/second
- **Market Data**: >10,000 updates/second
- **Database**: <10ms query response time

### Optimization Features

- **Connection Pooling**: Optimized database connections
- **Caching Strategy**: Multi-layer Redis caching
- **Async Processing**: Non-blocking I/O operations
- **Load Balancing**: Intelligent request distribution

## 🧪 Testing

### Test Categories

1. **Unit Tests**: Individual component validation
2. **Integration Tests**: Service interaction testing
3. **Load Tests**: Performance under stress
4. **Compliance Tests**: Regulatory requirement validation

### Running Tests

```bash
# All tests
docker-compose --profile testing run --rm test

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/load/
```

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/orders` - Place trading orders
- `GET /api/v1/portfolio` - Portfolio summary
- `GET /api/v1/positions` - Current positions
- `GET /api/v1/market-data` - Real-time market data
- `GET /api/v1/compliance/audit-trail` - Audit logs

## 🛠 Development

### Development Workflow

1. **Setup Development Environment**
   ```bash
   ./scripts/setup-volumes.sh
   docker-compose up -d
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run Tests**
   ```bash
   pytest
   ```

4. **Code Quality**
   ```bash
   black src/
   flake8 src/
   mypy src/
   ```

### Database Migrations

```bash
# Create migration
docker-compose run --rm migration revision --autogenerate -m "Description"

# Apply migrations
docker-compose run --rm migration upgrade head

# Rollback migration
docker-compose run --rm migration downgrade -1
```

## 📋 Maintenance

### Regular Tasks

1. **Database Backups**
   ```bash
   ./scripts/backup-database.sh production
   ```

2. **Volume Monitoring**
   ```bash
   ./scripts/monitor-volumes.sh
   ```

3. **Log Rotation**
   ```bash
   docker-compose exec app logrotate /etc/logrotate.conf
   ```

4. **Security Updates**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check PostgreSQL service status
   - Verify connection parameters
   - Review network connectivity

2. **High Latency**
   - Monitor system resources
   - Check database query performance
   - Review cache hit rates

3. **Market Data Issues**
   - Validate feed connectivity
   - Check WebSocket connections
   - Review data freshness

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug
docker-compose restart app

# Access application logs
docker-compose logs -f app

# Database debugging
docker-compose exec postgres psql -U trading_user trading_db
```

## 📋 Compliance Framework

### SOX (Sarbanes-Oxley Act) Overview
The **Sarbanes-Oxley Act of 2002** was enacted following major corporate scandals (Enron, WorldCom) that led to billions in investor losses. Named after sponsors Senator Paul Sarbanes and Representative Michael Oxley, SOX established strict financial reporting and corporate governance requirements for US public companies.

**Key Requirements:**
- **Section 302**: CEO/CFO certification of financial statement accuracy
- **Section 404**: Internal controls assessment and auditor attestation
- **Section 409**: Real-time disclosure of material changes
- **Audit Trails**: Complete, immutable record of all financial transactions
- **Segregation of Duties**: No single person controls entire financial processes

**Why Critical for Trading Systems:**
- Every trade must be logged with cryptographic integrity
- Real-time risk monitoring and automated controls
- Quarterly compliance reporting and audit readiness
- Data retention requirements (7+ years)

### South African Regulatory Equivalent
While SOX doesn't directly apply to SA companies, similar governance frameworks exist:

**Companies Act 71 of 2008:**
- Requires accurate financial reporting and director accountability
- Mandates internal controls and risk management
- Similar audit trail and documentation requirements

**King IV Corporate Governance Code:**
- Best practice governance framework for JSE-listed companies
- Emphasizes ethical leadership and transparency
- Includes IT governance and data protection principles

**JSE Listings Requirements:**
- Continuous disclosure obligations
- Financial reporting standards equivalent to international norms
- Risk management and internal control assessments

**Professional Impact:**
SA financial institutions (Standard Bank, FirstRand, Capitec) often implement SOX-level controls for international operations and best practice governance, making these skills highly valuable in the local market.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For support and questions:
- 📧 Email: support@trading-system.com
- 📝 Issues: GitHub Issues
- 📖 Documentation: Wiki

---

**⚠️ Important**: This is a financial trading system. Ensure proper testing and compliance validation before production deployment.