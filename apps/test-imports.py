#!/usr/bin/env python3
"""
Quick import test script for both applications
Tests that all critical imports work before Docker build
"""

import sys
import os

def test_finance_imports():
    """Test imports for finance trading app"""
    print("Testing Finance Trading App imports...")
    
    # Add finance app to path
    finance_path = "/Users/user/zero-downtime-pipeline/apps/finance-trading/src"
    if finance_path not in sys.path:
        sys.path.insert(0, finance_path)
    
    try:
        # Test core dependencies
        import fastapi
        import uvicorn
        import httpx
        import prometheus_client
        import pydantic
        print("✓ Core web framework imports successful")
        
        # Test market data dependencies
        try:
            import alpha_vantage
            print("✓ Alpha Vantage import successful")
        except ImportError as e:
            print(f"⚠ Alpha Vantage import failed: {e} (will use mock data)")
        
        try:
            import pandas
            import numpy
            print("✓ Data processing imports successful")
        except ImportError as e:
            print(f"✗ Data processing imports failed: {e}")
            return False
        
        # Test application imports
        try:
            from src.api.health import health_router
            print("✓ Health API import successful")
        except ImportError as e:
            print(f"✗ Health API import failed: {e}")
            return False
        
        try:
            from src.services.market_data_service import MarketDataService
            print("✓ Market Data Service import successful")
        except ImportError as e:
            print(f"✗ Market Data Service import failed: {e}")
            return False
        
        print("✅ Finance Trading App imports: PASSED")
        return True
        
    except ImportError as e:
        print(f"✗ Finance Trading App import failed: {e}")
        return False

def test_pharma_imports():
    """Test imports for pharma manufacturing app"""
    print("\nTesting Pharma Manufacturing App imports...")
    
    # Add pharma app to path
    pharma_path = "/Users/user/zero-downtime-pipeline/apps/pharma-manufacturing/src"
    if pharma_path not in sys.path:
        sys.path.insert(0, pharma_path)
    
    try:
        # Test core dependencies
        import fastapi
        import uvicorn
        import sqlalchemy
        import prometheus_client
        import pydantic
        print("✓ Core web framework imports successful")
        
        # Test data dependencies
        try:
            import pandas
            import numpy
            print("✓ Data processing imports successful")
        except ImportError as e:
            print(f"⚠ Data processing imports failed: {e}")
        
        # Test application imports
        try:
            from src.api.health import router as health_router
            print("✓ Health API import successful")
        except ImportError as e:
            print(f"✗ Health API import failed: {e}")
            return False
        
        try:
            from src.services.database_manager import DatabaseManager
            print("✓ Database Manager import successful")
        except ImportError as e:
            print(f"✗ Database Manager import failed: {e}")
            return False
        
        try:
            from src.services.alert_manager import AlertManager
            print("✓ Alert Manager import successful")
        except ImportError as e:
            print(f"✗ Alert Manager import failed: {e}")
            return False
        
        try:
            from src.services.equipment_simulator import EquipmentSimulator
            print("✓ Equipment Simulator import successful")
        except ImportError as e:
            print(f"✗ Equipment Simulator import failed: {e}")
            return False
        
        print("✅ Pharma Manufacturing App imports: PASSED")
        return True
        
    except ImportError as e:
        print(f"✗ Pharma Manufacturing App import failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Zero-Downtime Pipeline: Import Test")
    print("=" * 50)
    
    finance_success = test_finance_imports()
    pharma_success = test_pharma_imports()
    
    print("\n" + "=" * 50)
    if finance_success and pharma_success:
        print("🎉 ALL IMPORT TESTS PASSED!")
        print("Both applications are ready for Docker build.")
        sys.exit(0)
    else:
        print("❌ IMPORT TESTS FAILED!")
        print("Please fix the import issues before building Docker images.")
        sys.exit(1)

if __name__ == "__main__":
    main()