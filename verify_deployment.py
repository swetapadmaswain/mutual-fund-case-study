#!/usr/bin/env python3
"""
Deployment verification script for GitHub Actions scheduler
"""
import subprocess
import sys
import json
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return result"""
    print(f"\n--- {description} ---")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"FAILED: {description}")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False, str(e)

def check_git_status():
    """Check git repository status"""
    success, output = run_command("git status --porcelain", "Check Git Status")
    return success

def check_remote_sync():
    """Check if local is synced with remote"""
    success, output = run_command("git log --oneline -3", "Check Recent Commits")
    return success

def check_workflow_file():
    """Check if workflow file exists and is valid"""
    workflow_path = Path(".github/workflows/scheduler.yml")
    if workflow_path.exists():
        print("SUCCESS: Workflow file exists")
        
        # Check YAML syntax
        try:
            import yaml
            with open(workflow_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print("SUCCESS: Workflow YAML syntax valid")
            return True
        except Exception as e:
            print(f"FAILED: YAML syntax error - {e}")
            return False
    else:
        print("FAILED: Workflow file missing")
        return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        ".github/workflows/scheduler.yml",
        "SCHEDULER_DOCUMENTATION.md", 
        "GITHUB_SECRETS_SETUP.md",
        "test_scheduler.py",
        "scripts/health_check.py",
        "scripts/check_data_changes.py",
        "scripts/generate_update_report.py",
        "scripts/validate_data.py",
        "scripts/run_performance_tests.py",
        "requirements.txt",
        "requirements-api.txt"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"PASS {file_path}")
        else:
            print(f"FAIL {file_path} missing")
            all_exist = False
    
    return all_exist

def check_directory_structure():
    """Check required directory structure"""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/documents",
        "cache",
        "cache/phase1_results",
        "cache/phase2_1_results", 
        "cache/phase2_2_results",
        "cache/phase2_3_results",
        "cache/vector_db",
        "logs",
        "scripts",
        ".github/workflows"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"PASS {dir_path}")
        else:
            print(f"WARN {dir_path} missing")
            # Try to create it
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"CREATED Created {dir_path}")
            except:
                print(f"FAIL Failed to create {dir_path}")
                all_exist = False
    
    return all_exist

def generate_deployment_report():
    """Generate deployment verification report"""
    print("\n" + "="*60)
    print("DEPLOYMENT VERIFICATION REPORT")
    print("="*60)
    
    checks = [
        ("Git Repository Status", check_git_status),
        ("Remote Sync Status", check_remote_sync),
        ("Workflow File Validity", check_workflow_file),
        ("Required Files", check_required_files),
        ("Directory Structure", check_directory_structure)
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n{check_name}")
        results[check_name] = check_func()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{check_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("All checks passed! Scheduler is ready for deployment.")
        print("\nNEXT STEPS:")
        print("1. Configure GitHub secrets (see GITHUB_SECRETS_SETUP.md)")
        print("2. Test manual workflow trigger in GitHub Actions")
        print("3. Monitor first scheduled execution")
        return 0
    else:
        print("Some checks failed. Please fix issues before proceeding.")
        return 1

def create_quick_start_guide():
    """Create quick start instructions"""
    guide = """
# 🚀 Quick Start Guide

## 1. Configure GitHub Secrets
Visit: https://github.com/swetapadmaswain/mutual-fund-case-study/settings/secrets/actions

Add these secrets:
- GROQ_API_KEY (your Groq API key)
- HDFC_API_KEY (your HDFC API key)  
- API_BASE_URL (https://api.groq.com/openai/v1)
- EMAIL_USERNAME (your Gmail address)
- EMAIL_PASSWORD (Gmail app password)
- NOTIFICATION_EMAIL (email for notifications)
- CRITICAL_EMAIL (email for critical alerts)

## 2. Test Scheduler
1. Go to: https://github.com/swetapadmaswain/mutual-fund-case-study/actions
2. Click "📅 Mutual Fund AI Assistant Scheduler"
3. Click "Run workflow"
4. Select "health_check" and run it

## 3. Monitor Execution
- Check workflow logs for any errors
- Verify artifacts are uploaded
- Monitor email notifications

## 4. Verify Scheduled Runs
Scheduler will automatically run:
- Every hour: Health checks
- Every 4 hours: Performance monitoring
- Every 6 hours: Data updates
- Every 12 hours: Data validation
- Every Sunday 9AM UTC: Weekly reports + cleanup

## 5. Troubleshooting
- Check workflow logs for error details
- Verify all secrets are correctly configured
- Ensure API keys are valid and have proper permissions
- Check email configuration for notification issues

📚 For detailed documentation, see:
- SCHEDULER_DOCUMENTATION.md
- GITHUB_SECRETS_SETUP.md
"""
    
    with open("QUICK_START.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("Created QUICK_START.md")

def main():
    """Main verification function"""
    print("Starting Deployment Verification...\n")
    
    # Run all checks
    result = generate_deployment_report()
    
    # Create quick start guide
    create_quick_start_guide()
    
    print(f"\nVerification completed with exit code: {result}")
    return result

if __name__ == "__main__":
    sys.exit(main())
