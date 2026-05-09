#!/usr/bin/env python3
"""
Test script to verify scheduler functionality
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def test_yaml_syntax():
    """Test YAML syntax of scheduler file"""
    print("Testing YAML syntax...")
    try:
        import yaml
        with open('.github/workflows/scheduler.yml', 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print("PASS YAML syntax is valid")
        return True
    except Exception as e:
        print(f"FAIL YAML syntax error: {e}")
        return False

def test_script_existence():
    """Test if all required scripts exist"""
    print("Testing script existence...")
    required_scripts = [
        'scripts/check_data_changes.py',
        'scripts/generate_update_report.py', 
        'scripts/health_check.py',
        'scripts/run_performance_tests.py',
        'scripts/validate_data.py'
    ]
    
    all_exist = True
    for script in required_scripts:
        if Path(script).exists():
            print(f"PASS {script} exists")
        else:
            print(f"FAIL {script} missing")
            all_exist = False
    
    return all_exist

def test_script_syntax():
    """Test Python syntax of all scripts"""
    print("Testing script syntax...")
    scripts = [
        'scripts/check_data_changes.py',
        'scripts/generate_update_report.py',
        'scripts/health_check.py', 
        'scripts/run_performance_tests.py',
        'scripts/validate_data.py'
    ]
    
    all_valid = True
    for script in scripts:
        try:
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', script
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"PASS {script} syntax valid")
            else:
                print(f"FAIL {script} syntax error: {result.stderr}")
                all_valid = False
        except Exception as e:
            print(f"FAIL {script} error: {e}")
            all_valid = False
    
    return all_valid

def test_directory_structure():
    """Test required directory structure"""
    print("Testing directory structure...")
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/documents', 
        'cache',
        'cache/phase1_results',
        'cache/phase2_1_results',
        'cache/phase2_2_results',
        'cache/phase2_3_results',
        'cache/vector_db',
        'logs',
        'scripts',
        '.github/workflows'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"PASS {dir_path} exists")
        else:
            print(f"WARN {dir_path} missing (will be created)")
            # Create missing directories
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"CREATED Created {dir_path}")
            except Exception as e:
                print(f"FAIL Failed to create {dir_path}: {e}")
                all_exist = False
    
    return all_exist

def test_requirements():
    """Test if requirements files exist"""
    print("Testing requirements files...")
    req_files = [
        'requirements.txt',
        'requirements-api.txt'
    ]
    
    all_exist = True
    for req_file in req_files:
        if Path(req_file).exists():
            print(f"PASS {req_file} exists")
        else:
            print(f"FAIL {req_file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("Starting Scheduler Tests\n")
    
    tests = [
        ("YAML Syntax", test_yaml_syntax),
        ("Script Existence", test_script_existence),
        ("Script Syntax", test_script_syntax),
        ("Directory Structure", test_directory_structure),
        ("Requirements Files", test_requirements)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results[test_name] = test_func()
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Scheduler is ready.")
        return 0
    else:
        print("Some tests failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
