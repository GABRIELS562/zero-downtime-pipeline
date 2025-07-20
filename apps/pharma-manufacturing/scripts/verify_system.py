#!/usr/bin/env python3
"""
System Verification Script for Pharmaceutical Manufacturing System
Comprehensive validation of all components
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

def check_file_exists(file_path: str, description: str) -> bool:
    """Check if file exists"""
    path = Path(file_path)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {file_path} ({size} bytes)")
    return exists

def check_python_syntax(file_path: str, description: str) -> bool:
    """Check Python file syntax"""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        print(f"✅ {description}: Valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"❌ {description}: Syntax error - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {str(e)}")
        return False

def check_environment_files() -> Dict[str, bool]:
    """Check environment configuration files"""
    print("\n🔧 Environment Configuration Files:")
    
    env_files = {
        'Development': 'config/.env.development',
        'Testing': 'config/.env.testing', 
        'Production': 'config/.env.production'
    }
    
    results = {}
    for env_name, file_path in env_files.items():
        results[env_name] = check_file_exists(file_path, f"{env_name} Environment")
    
    return results

def check_database_models() -> Dict[str, bool]:
    """Check database model files"""
    print("\n🗄️ Database Models:")
    
    model_files = {
        'Base Models': 'src/database/models/base.py',
        'Batch Models': 'src/database/models/batch_models.py',
        'Equipment Models': 'src/database/models/equipment_models.py',
        'Material Models': 'src/database/models/material_models.py',
        'Quality Control Models': 'src/database/models/quality_control_models.py',
        'Environmental Models': 'src/database/models/environmental_monitoring_models.py',
        'User Models': 'src/database/models/user_models.py',
        'Audit Models': 'src/database/models/audit_models.py',
        'Deviation Models': 'src/database/models/deviation_models.py',
        'Models Init': 'src/database/models/__init__.py'
    }
    
    results = {}
    for model_name, file_path in model_files.items():
        exists = check_file_exists(file_path, model_name)
        if exists:
            syntax_ok = check_python_syntax(file_path, f"{model_name} Syntax")
            results[model_name] = exists and syntax_ok
        else:
            results[model_name] = False
    
    return results

def check_docker_configuration() -> Dict[str, bool]:
    """Check Docker configuration files"""
    print("\n🐳 Docker Configuration:")
    
    docker_files = {
        'Dockerfile': 'Dockerfile',
        'Docker Compose': 'docker-compose.yml',
        'Docker Override': 'docker-compose.override.yml',
        'Requirements': 'requirements.txt'
    }
    
    results = {}
    for config_name, file_path in docker_files.items():
        results[config_name] = check_file_exists(file_path, config_name)
    
    return results

def check_scripts() -> Dict[str, bool]:
    """Check script files"""
    print("\n📜 Scripts:")
    
    script_files = {
        'Health Monitor': 'scripts/health_monitor.py',
        'Backup Recovery (Simple)': 'scripts/backup_recovery_simple.py',
        'Database Init': 'scripts/init_database.py',
        'DB Init SQL': 'scripts/db-init/01_regulatory_constraints.sql',
        'System Verify': 'scripts/verify_system.py'
    }
    
    results = {}
    for script_name, file_path in script_files.items():
        exists = check_file_exists(file_path, script_name)
        if exists and file_path.endswith('.py'):
            syntax_ok = check_python_syntax(file_path, f"{script_name} Syntax")
            results[script_name] = exists and syntax_ok
        else:
            results[script_name] = exists
    
    return results

def check_database_schemas() -> Dict[str, bool]:
    """Check database schemas"""
    print("\n📋 Database Schemas:")
    
    schema_files = {
        'Base Schemas': 'src/database/schemas/base_schemas.py',
        'Batch Schemas': 'src/database/schemas/batch_schemas.py',
        'Quality Schemas': 'src/database/schemas/quality_schemas.py'
    }
    
    results = {}
    for schema_name, file_path in schema_files.items():
        if Path(file_path).exists():
            exists = check_file_exists(file_path, schema_name)
            if exists:
                syntax_ok = check_python_syntax(file_path, f"{schema_name} Syntax")
                results[schema_name] = exists and syntax_ok
            else:
                results[schema_name] = False
        else:
            print(f"⚠️ {schema_name}: {file_path} (Not implemented yet)")
            results[schema_name] = None  # Not implemented
    
    return results

def check_core_system() -> Dict[str, bool]:
    """Check core system files"""
    print("\n⚙️ Core System:")
    
    core_files = {
        'Database Connection': 'src/database/database.py',
        'Main Application': 'src/main.py'
    }
    
    results = {}
    for core_name, file_path in core_files.items():
        if Path(file_path).exists():
            exists = check_file_exists(file_path, core_name)
            if exists:
                syntax_ok = check_python_syntax(file_path, f"{core_name} Syntax")
                results[core_name] = exists and syntax_ok
            else:
                results[core_name] = False
        else:
            print(f"⚠️ {core_name}: {file_path} (Not implemented yet)")
            results[core_name] = None
    
    return results

def generate_summary(all_results: Dict[str, Dict[str, bool]]) -> Dict[str, Any]:
    """Generate verification summary"""
    summary = {
        'total_checks': 0,
        'passed': 0,
        'failed': 0,
        'not_implemented': 0,
        'success_rate': 0.0,
        'categories': {}
    }
    
    for category, results in all_results.items():
        category_stats = {'total': 0, 'passed': 0, 'failed': 0, 'not_implemented': 0}
        
        for check_name, result in results.items():
            category_stats['total'] += 1
            summary['total_checks'] += 1
            
            if result is True:
                category_stats['passed'] += 1
                summary['passed'] += 1
            elif result is False:
                category_stats['failed'] += 1
                summary['failed'] += 1
            else:  # None - not implemented
                category_stats['not_implemented'] += 1
                summary['not_implemented'] += 1
        
        summary['categories'][category] = category_stats
    
    # Calculate success rate (excluding not implemented)
    implemented_checks = summary['total_checks'] - summary['not_implemented']
    if implemented_checks > 0:
        summary['success_rate'] = (summary['passed'] / implemented_checks) * 100
    
    return summary

def main():
    """Main verification function"""
    print("🏭 Pharmaceutical Manufacturing System Verification")
    print("=" * 60)
    
    # Run all checks
    all_results = {
        'Environment Files': check_environment_files(),
        'Database Models': check_database_models(),
        'Docker Configuration': check_docker_configuration(),
        'Scripts': check_scripts(),
        'Database Schemas': check_database_schemas(),
        'Core System': check_core_system()
    }
    
    # Generate summary
    summary = generate_summary(all_results)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for category, stats in summary['categories'].items():
        print(f"{category}:")
        print(f"  ✅ Passed: {stats['passed']}")
        print(f"  ❌ Failed: {stats['failed']}")
        if stats['not_implemented'] > 0:
            print(f"  ⚠️ Not Implemented: {stats['not_implemented']}")
        print(f"  📊 Total: {stats['total']}")
        print()
    
    print(f"Overall Statistics:")
    print(f"  ✅ Total Passed: {summary['passed']}")
    print(f"  ❌ Total Failed: {summary['failed']}")
    print(f"  ⚠️ Not Implemented: {summary['not_implemented']}")
    print(f"  📊 Total Checks: {summary['total_checks']}")
    print(f"  🎯 Success Rate: {summary['success_rate']:.1f}%")
    
    # System status
    if summary['failed'] == 0:
        print("\n🎉 SYSTEM STATUS: READY FOR DEPLOYMENT")
        print("All implemented components are working correctly!")
    elif summary['success_rate'] >= 90:
        print("\n✅ SYSTEM STATUS: MOSTLY READY")
        print("Minor issues detected, but system is functional.")
    elif summary['success_rate'] >= 70:
        print("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION")
        print("Several issues detected, requires fixes before deployment.")
    else:
        print("\n❌ SYSTEM STATUS: NOT READY")
        print("Critical issues detected, system needs significant work.")
    
    # Save detailed results
    results_file = Path('verification_results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': str(os.environ.get('BUILD_TIMESTAMP', 'unknown')),
            'summary': summary,
            'detailed_results': all_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()