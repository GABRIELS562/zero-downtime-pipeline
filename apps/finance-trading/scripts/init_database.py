#!/usr/bin/env python3
"""
Database Initialization Script
Sets up the trading system database with initial data and configuration
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from database.connection import init_database, get_db_session, database_manager
from database.models import (
    User, Account, Instrument, MarketData, Order, Execution, 
    Position, Transaction, AuditLog, Base
)
from database.migrations import MigrationManager
from services.sox_compliance import SOXComplianceService
from services.risk_manager import RiskManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Database initialization and setup"""
    
    def __init__(self):
        self.migration_manager = MigrationManager()
        self.sox_compliance = SOXComplianceService()
        self.risk_manager = RiskManager()
    
    async def initialize_database(self):
        """Initialize the complete database"""
        logger.info("Starting database initialization...")
        
        try:
            # 1. Initialize database connection
            await init_database()
            logger.info("Database connection initialized")
            
            # 2. Create all tables
            await self.create_tables()
            logger.info("Database tables created")
            
            # 3. Create initial data
            await self.create_initial_data()
            logger.info("Initial data created")
            
            # 4. Set up audit triggers
            await self.setup_audit_triggers()
            logger.info("Audit triggers set up")
            
            # 5. Create indexes for performance
            await self.create_performance_indexes()
            logger.info("Performance indexes created")
            
            # 6. Verify database integrity
            await self.verify_database_integrity()
            logger.info("Database integrity verified")
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def create_tables(self):
        """Create all database tables"""
        async with database_manager.get_session() as session:
            # Create all tables
            await session.run_sync(Base.metadata.create_all, database_manager.engine)
    
    async def create_initial_data(self):
        """Create initial reference data"""
        await self.create_demo_users()
        await self.create_sample_instruments()
        await self.create_sample_market_data()
        await self.create_initial_compliance_data()
    
    async def create_demo_users(self):
        """Create demo users for testing"""
        demo_users = [
            {
                'username': 'demo_trader',
                'email': 'demo@trading.com',
                'password_hash': '$2b$12$dummy_hash_for_demo_user',
                'salt': 'demo_salt',
                'first_name': 'Demo',
                'last_name': 'Trader',
                'is_active': True,
                'is_verified': True,
                'risk_level': 'medium',
                'kyc_status': 'verified',
                'accredited_investor': True
            },
            {
                'username': 'admin_user',
                'email': 'admin@trading.com',
                'password_hash': '$2b$12$dummy_hash_for_admin_user',
                'salt': 'admin_salt',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True,
                'is_verified': True,
                'is_admin': True,
                'risk_level': 'low',
                'kyc_status': 'verified',
                'accredited_investor': True
            }
        ]
        
        async with database_manager.get_session() as session:
            for user_data in demo_users:
                user = User(**user_data)
                session.add(user)
                await session.flush()
                
                # Create demo account for each user
                account = Account(
                    user_id=user.id,
                    account_number=f"DEMO{user.id.hex[:8].upper()}",
                    account_type='DEMO',
                    account_name=f"{user.first_name} {user.last_name} Demo Account",
                    cash_balance=Decimal('100000.00'),  # $100K demo money
                    available_balance=Decimal('100000.00'),
                    buying_power=Decimal('200000.00'),  # 2:1 leverage
                    currency='USD',
                    is_active=True
                )
                session.add(account)
            
            await session.commit()
            logger.info(f"Created {len(demo_users)} demo users with accounts")
    
    async def create_sample_instruments(self):
        """Create sample trading instruments"""
        instruments = [
            # Major stocks
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'description': 'Technology company',
                'asset_class': 'EQUITY',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'exchange': 'NASDAQ',
                'tick_size': Decimal('0.01'),
                'lot_size': 1,
                'min_quantity': Decimal('1'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.25')
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'description': 'Technology company',
                'asset_class': 'EQUITY',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'exchange': 'NASDAQ',
                'tick_size': Decimal('0.01'),
                'lot_size': 1,
                'min_quantity': Decimal('1'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.25')
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'description': 'Electric vehicle manufacturer',
                'asset_class': 'EQUITY',
                'sector': 'Automotive',
                'industry': 'Electric Vehicles',
                'exchange': 'NASDAQ',
                'tick_size': Decimal('0.01'),
                'lot_size': 1,
                'min_quantity': Decimal('1'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.30')
            },
            {
                'symbol': 'SPY',
                'name': 'SPDR S&P 500 ETF',
                'description': 'S&P 500 Index ETF',
                'asset_class': 'EQUITY',
                'sector': 'Financial',
                'industry': 'Exchange Traded Funds',
                'exchange': 'NYSE',
                'tick_size': Decimal('0.01'),
                'lot_size': 1,
                'min_quantity': Decimal('1'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.25')
            },
            # Forex pairs
            {
                'symbol': 'EURUSD',
                'name': 'Euro / US Dollar',
                'description': 'EUR/USD currency pair',
                'asset_class': 'FOREX',
                'sector': 'Currency',
                'industry': 'Foreign Exchange',
                'exchange': 'FOREX',
                'tick_size': Decimal('0.00001'),
                'lot_size': 100000,
                'min_quantity': Decimal('0.01'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.02')
            },
            {
                'symbol': 'GBPUSD',
                'name': 'British Pound / US Dollar',
                'description': 'GBP/USD currency pair',
                'asset_class': 'FOREX',
                'sector': 'Currency',
                'industry': 'Foreign Exchange',
                'exchange': 'FOREX',
                'tick_size': Decimal('0.00001'),
                'lot_size': 100000,
                'min_quantity': Decimal('0.01'),
                'is_tradable': True,
                'is_shortable': True,
                'margin_requirement': Decimal('0.02')
            }
        ]
        
        async with database_manager.get_session() as session:
            for instrument_data in instruments:
                instrument = Instrument(**instrument_data)
                session.add(instrument)
            
            await session.commit()
            logger.info(f"Created {len(instruments)} sample instruments")
    
    async def create_sample_market_data(self):
        """Create sample market data"""
        # Get instruments
        async with database_manager.get_session() as session:
            result = await session.execute(
                "SELECT id, symbol FROM instruments LIMIT 10"
            )
            instruments = result.fetchall()
        
        # Sample market data
        market_data_samples = [
            ('AAPL', Decimal('150.00'), Decimal('149.95'), Decimal('150.05')),
            ('GOOGL', Decimal('2500.00'), Decimal('2499.50'), Decimal('2500.50')),
            ('TSLA', Decimal('800.00'), Decimal('799.50'), Decimal('800.50')),
            ('SPY', Decimal('400.00'), Decimal('399.95'), Decimal('400.05')),
            ('EURUSD', Decimal('1.1000'), Decimal('1.0999'), Decimal('1.1001')),
            ('GBPUSD', Decimal('1.2500'), Decimal('1.2499'), Decimal('1.2501'))
        ]
        
        async with database_manager.get_session() as session:
            for symbol, price, bid, ask in market_data_samples:
                # Find instrument
                result = await session.execute(
                    "SELECT id FROM instruments WHERE symbol = :symbol",
                    {'symbol': symbol}
                )
                instrument_row = result.fetchone()
                
                if instrument_row:
                    market_data = MarketData(
                        instrument_id=instrument_row[0],
                        price=price,
                        bid=bid,
                        ask=ask,
                        volume=Decimal('1000000'),
                        data_source='DEMO',
                        is_delayed=False
                    )
                    session.add(market_data)
            
            await session.commit()
            logger.info(f"Created {len(market_data_samples)} market data samples")
    
    async def create_initial_compliance_data(self):
        """Create initial compliance and audit data"""
        async with database_manager.get_session() as session:
            # Create initial audit log entry
            audit_log = AuditLog(
                user_id=None,
                event_type='SYSTEM_INITIALIZATION',
                event_description='Database initialized with initial data',
                table_name='system',
                sox_relevant=True,
                retention_until=datetime.now(timezone.utc).replace(year=datetime.now().year + 7),
                hash_value='initial_system_hash',
                compliance_tags={'system_init': True, 'initial_setup': True}
            )
            session.add(audit_log)
            
            await session.commit()
            logger.info("Initial compliance data created")
    
    async def setup_audit_triggers(self):
        """Set up database audit triggers"""
        async with database_manager.get_session() as session:
            # Create audit function
            await session.execute("""
                CREATE OR REPLACE FUNCTION audit_trigger_function()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF TG_OP = 'DELETE' THEN
                        INSERT INTO audit_logs (
                            user_id, event_type, event_description, table_name, 
                            record_id, old_values, retention_until, hash_value, created_at
                        ) VALUES (
                            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
                            'DELETE',
                            'Record deleted from ' || TG_TABLE_NAME,
                            TG_TABLE_NAME,
                            OLD.id,
                            to_jsonb(OLD),
                            NOW() + INTERVAL '7 years',
                            encode(digest(to_jsonb(OLD)::text, 'sha256'), 'hex'),
                            NOW()
                        );
                        RETURN OLD;
                    ELSIF TG_OP = 'UPDATE' THEN
                        INSERT INTO audit_logs (
                            user_id, event_type, event_description, table_name, 
                            record_id, old_values, new_values, retention_until, hash_value, created_at
                        ) VALUES (
                            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
                            'UPDATE',
                            'Record updated in ' || TG_TABLE_NAME,
                            TG_TABLE_NAME,
                            NEW.id,
                            to_jsonb(OLD),
                            to_jsonb(NEW),
                            NOW() + INTERVAL '7 years',
                            encode(digest((to_jsonb(OLD)::text || to_jsonb(NEW)::text), 'sha256'), 'hex'),
                            NOW()
                        );
                        RETURN NEW;
                    ELSIF TG_OP = 'INSERT' THEN
                        INSERT INTO audit_logs (
                            user_id, event_type, event_description, table_name, 
                            record_id, new_values, retention_until, hash_value, created_at
                        ) VALUES (
                            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
                            'INSERT',
                            'Record inserted into ' || TG_TABLE_NAME,
                            TG_TABLE_NAME,
                            NEW.id,
                            to_jsonb(NEW),
                            NOW() + INTERVAL '7 years',
                            encode(digest(to_jsonb(NEW)::text, 'sha256'), 'hex'),
                            NOW()
                        );
                        RETURN NEW;
                    END IF;
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
            """)
            
            # Create triggers for critical tables
            critical_tables = ['orders', 'executions', 'positions', 'transactions', 'accounts']
            for table in critical_tables:
                await session.execute(f"""
                    DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
                    CREATE TRIGGER {table}_audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
                """)
            
            await session.commit()
            logger.info("Audit triggers created")
    
    async def create_performance_indexes(self):
        """Create performance indexes"""
        async with database_manager.get_session() as session:
            # Additional indexes for high-frequency trading
            performance_indexes = [
                # Orders table indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_symbol_status ON orders(instrument_id, status) WHERE status IN ('PENDING', 'PARTIALLY_FILLED')",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_created_desc ON orders(user_id, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_account_updated_desc ON orders(account_id, updated_at DESC)",
                
                # Market data indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_symbol_timestamp_desc ON market_data(instrument_id, timestamp DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_timestamp_desc ON market_data(timestamp DESC)",
                
                # Positions indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_positions_account_nonzero ON positions(account_id, quantity) WHERE quantity != 0",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_positions_symbol_quantity ON positions(instrument_id, quantity)",
                
                # Executions indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_executions_timestamp_desc ON executions(executed_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_executions_order_timestamp ON executions(order_id, executed_at DESC)",
                
                # Transactions indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_account_type_created ON transactions(account_id, transaction_type, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_user_created_desc ON transactions(user_id, created_at DESC)",
                
                # Audit logs indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_table_created_desc ON audit_logs(table_name, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_event_created ON audit_logs(user_id, event_type, created_at DESC)",
                
                # Instruments indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_instruments_asset_class_tradable ON instruments(asset_class, is_tradable) WHERE is_tradable = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_instruments_exchange_symbol ON instruments(exchange, symbol)",
            ]
            
            for index_sql in performance_indexes:
                try:
                    await session.execute(index_sql)
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
                    await session.rollback()
            
            logger.info("Performance indexes created")
    
    async def verify_database_integrity(self):
        """Verify database integrity"""
        async with database_manager.get_session() as session:
            # Check table counts
            tables = ['users', 'accounts', 'instruments', 'market_data', 'audit_logs']
            
            for table in tables:
                result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                logger.info(f"Table {table}: {count} records")
            
            # Check constraints
            result = await session.execute("""
                SELECT conname, contype 
                FROM pg_constraint 
                WHERE contype IN ('c', 'f', 'u') 
                AND conname LIKE '%trading%'
                ORDER BY conname
            """)
            
            constraints = result.fetchall()
            logger.info(f"Found {len(constraints)} constraints")
            
            # Check indexes
            result = await session.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE '%idx_%'
                ORDER BY tablename, indexname
            """)
            
            indexes = result.fetchall()
            logger.info(f"Found {len(indexes)} custom indexes")

async def main():
    """Main initialization function"""
    try:
        initializer = DatabaseInitializer()
        await initializer.initialize_database()
        print("✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)