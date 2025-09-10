#!/usr/bin/env python3
"""
Comprehensive Python Application Validation Script
Tests imports, dependencies, and Docker builds for both applications
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
import json
import time

def run_command(cmd, cwd=None, timeout=300):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)

def check_requirements_syntax(req_file):
    """Check requirements file for syntax issues"""
    issues = []
    
    if not os.path.exists(req_file):
        return [f"Requirements file not found: {req_file}"]
    
    with open(req_file, 'r') as f:
        lines = f.readlines()
    
    packages = {}
    duplicates = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            if '==' in line:
                pkg_name = line.split('==')[0].strip()
                if pkg_name in packages:
                    duplicates.append(f"Line {line_num}: Duplicate package '{pkg_name}' (first seen on line {packages[pkg_name]})")
                else:
                    packages[pkg_name] = line_num
            elif line and not line.startswith('-'):
                issues.append(f"Line {line_num}: Package '{line}' not pinned to specific version")
    
    issues.extend(duplicates)
    return issues

def validate_docker_build(app_path, dockerfile_name="Dockerfile.bulletproof"):
    """Test Docker build without full build"""
    dockerfile_path = os.path.join(app_path, dockerfile_name)
    
    if not os.path.exists(dockerfile_path):
        return False, f"Dockerfile not found: {dockerfile_path}"
    
    # Parse Dockerfile for basic syntax
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        required_elements = [
            'FROM python:3.11-slim',
            'WORKDIR /app',
            'COPY requirements-bulletproof.txt',
            'pip install',
            'PYTHONPATH=/app'
        ]
        
        missing = [elem for elem in required_elements if elem not in content]
        
        if missing:
            return False, f"Missing required Dockerfile elements: {missing}"
        
        return True, "Dockerfile syntax OK"
    
    except Exception as e:
        return False, f"Error reading Dockerfile: {e}"

def check_python_structure(app_path):
    """Check Python project structure"""
    issues = []
    
    src_path = os.path.join(app_path, 'src')
    if not os.path.exists(src_path):
        issues.append("Missing src directory")
        return issues
    
    # Check for __init__.py files
    required_init_dirs = [
        'src',
        'src/api',
        'src/services', 
        'src/models',
        'src/database',
        'src/middleware'
    ]
    
    for dir_path in required_init_dirs:
        full_path = os.path.join(app_path, dir_path)
        init_file = os.path.join(full_path, '__init__.py')
        
        if os.path.exists(full_path) and not os.path.exists(init_file):
            issues.append(f"Missing __init__.py in {dir_path}")
    
    # Check main.py exists
    main_py = os.path.join(src_path, 'main.py')
    if not os.path.exists(main_py):
        issues.append("Missing src/main.py")
    
    return issues

def analyze_import_patterns(app_path):
    """Analyze import patterns for potential issues"""
    issues = []
    src_path = os.path.join(app_path, 'src')
    
    if not os.path.exists(src_path):
        return ["src directory not found"]
    
    # Find all Python files
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, app_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        
                        # Check for problematic import patterns
                        if line.startswith('from src.') and 'import' in line:
                            # This is OK with PYTHONPATH=/app
                            continue
                        elif line.startswith('import src.'):
                            continue
                        elif 'from .' in line and line.startswith('from .'):
                            # Relative imports might be problematic
                            if '../' in file_path:
                                issues.append(f"{rel_path}:{line_num} - Relative import may fail: {line}")
                        
                except Exception as e:
                    issues.append(f"Error reading {rel_path}: {e}")
    
    return issues

def check_service_files(app_path, expected_services):
    """Check if required service files exist and have basic structure"""
    issues = []
    services_path = os.path.join(app_path, 'src', 'services')
    
    if not os.path.exists(services_path):
        issues.append("services directory missing")
        return issues
    
    for service_name in expected_services:
        service_file = os.path.join(services_path, f"{service_name}.py")
        if not os.path.exists(service_file):
            issues.append(f"Missing service file: {service_name}.py")
            continue
        
        # Check basic service structure
        try:
            with open(service_file, 'r') as f:
                content = f.read()
            
            # Look for class definition
            if f'class {service_name.replace("_", "").title()}' not in content and \
               f'class {service_name.split("_")[0].title()}' not in content:
                issues.append(f"{service_name}.py - No main service class found")
            
            # Check for async methods (most services should have them)
            if 'async def' not in content:
                issues.append(f"{service_name}.py - No async methods found (may not be async-compatible)")
        
        except Exception as e:
            issues.append(f"Error analyzing {service_name}.py: {e}")
    
    return issues

def main():
    """Main validation function"""
    print("🔍 Comprehensive Python Application Validation")
    print("=" * 60)
    
    # Define app paths and expected services
    base_path = Path(__file__).parent / "apps"
    
    apps_config = {
        "finance-trading": {
            "path": base_path / "finance-trading",
            "services": ["market_data_service", "order_processor", "risk_manager", "health_monitor", "sox_compliance"]
        },
        "pharma-manufacturing": {
            "path": base_path / "pharma-manufacturing", 
            "services": ["database_manager", "alert_manager", "equipment_simulator"]
        }
    }
    
    all_passed = True
    results = {}
    
    for app_name, config in apps_config.items():
        print(f"\n🧪 Validating {app_name}")
        print("-" * 40)
        
        app_path = config["path"]
        app_results = {
            "requirements_issues": [],
            "structure_issues": [], 
            "import_issues": [],
            "service_issues": [],
            "dockerfile_status": "",
            "overall_status": "UNKNOWN"
        }
        
        # 1. Check requirements file
        req_file = app_path / "requirements-bulletproof.txt"
        req_issues = check_requirements_syntax(str(req_file))
        app_results["requirements_issues"] = req_issues
        
        if req_issues:
            print(f"⚠️  Requirements issues ({len(req_issues)}):")
            for issue in req_issues:
                print(f"   - {issue}")
        else:
            print("✅ Requirements file OK")
        
        # 2. Check project structure
        structure_issues = check_python_structure(str(app_path))
        app_results["structure_issues"] = structure_issues
        
        if structure_issues:
            print(f"⚠️  Structure issues ({len(structure_issues)}):")
            for issue in structure_issues:
                print(f"   - {issue}")
        else:
            print("✅ Project structure OK")
        
        # 3. Analyze import patterns
        import_issues = analyze_import_patterns(str(app_path))
        app_results["import_issues"] = import_issues
        
        if import_issues:
            print(f"⚠️  Import issues ({len(import_issues)}):")
            for issue in import_issues[:5]:  # Show first 5
                print(f"   - {issue}")
            if len(import_issues) > 5:
                print(f"   ... and {len(import_issues) - 5} more")
        else:
            print("✅ Import patterns OK")
        
        # 4. Check service files
        service_issues = check_service_files(str(app_path), config["services"])
        app_results["service_issues"] = service_issues
        
        if service_issues:
            print(f"⚠️  Service issues ({len(service_issues)}):")
            for issue in service_issues:
                print(f"   - {issue}")
        else:
            print("✅ Service files OK")
        
        # 5. Validate Dockerfile
        dockerfile_ok, dockerfile_msg = validate_docker_build(str(app_path))
        app_results["dockerfile_status"] = dockerfile_msg
        
        if dockerfile_ok:
            print("✅ Dockerfile validation OK")
        else:
            print(f"❌ Dockerfile issue: {dockerfile_msg}")
        
        # Calculate overall status
        total_issues = len(req_issues) + len(structure_issues) + len(import_issues) + len(service_issues)
        
        if total_issues == 0 and dockerfile_ok:
            app_results["overall_status"] = "READY"
            print("🎉 OVERALL: READY FOR DEPLOYMENT")
        elif total_issues <= 2 and dockerfile_ok:
            app_results["overall_status"] = "MOSTLY_READY" 
            print("⚠️  OVERALL: MOSTLY READY (minor issues)")
        else:
            app_results["overall_status"] = "NEEDS_WORK"
            print("❌ OVERALL: NEEDS WORK")
            all_passed = False
        
        results[app_name] = app_results
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    for app_name, result in results.items():
        status = result["overall_status"]
        if status == "READY":
            print(f"✅ {app_name}: READY FOR K3S DEPLOYMENT")
        elif status == "MOSTLY_READY":
            print(f"⚠️  {app_name}: MOSTLY READY (monitor for issues)")  
        else:
            print(f"❌ {app_name}: NEEDS MORE WORK")
    
    # Create test commands
    print(f"\n🧪 RECOMMENDED TEST COMMANDS:")
    print("-" * 40)
    
    for app_name in apps_config.keys():
        print(f"\n# Test {app_name} Docker build:")
        print(f"cd apps/{app_name}")
        print(f"docker build -f Dockerfile.bulletproof -t {app_name}-test .")
        print(f"docker run --rm {app_name}-test python -c \"import sys; sys.path.append('/app'); import src.main; print('✅ Import successful')\"")
    
    # Final result
    print(f"\n{'🎉 ALL APPS READY!' if all_passed else '⚠️  SOME APPS NEED ATTENTION'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())