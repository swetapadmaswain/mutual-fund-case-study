#!/usr/bin/env python3
"""
Test script to verify scheduler can run with minimal configuration
"""
import os
import sys
from pathlib import Path

def test_minimal_scheduler():
    """Test if scheduler can work with minimal secrets"""
    print("Testing minimal scheduler configuration...")
    
    # Check if essential files exist
    required_files = [
        ".github/workflows/scheduler.yml",
        "scripts/health_check.py",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"FAIL: {file_path} missing")
            return False
    
    print("SUCCESS: All essential files present")
    
    # Test health check script can run (without API calls)
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append('scripts'); from health_check import check_file_system_health; check_file_system_health()"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("SUCCESS: Health check script can execute")
            return True
        else:
            print(f"FAIL: Health check error - {result.stderr}")
            return False
            
    except Exception as e:
        print(f"FAIL: Health check test failed - {e}")
        return False

def main():
    """Main test function"""
    print("Testing Scheduler Readiness\n")
    
    if test_minimal_scheduler():
        print("SUCCESS: Scheduler is ready for testing!")
        print("\nNext Steps:")
        print("1. Configure GitHub secrets (see SECRETS_CHECKLIST.md)")
        print("2. Test manual workflow trigger in GitHub Actions")
        print("3. Monitor first execution")
        return 0
    else:
        print("\nScheduler needs fixes before testing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
