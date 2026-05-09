#!/usr/bin/env python3
"""
Script to perform system health checks for the mutual fund data pipeline.
"""
import json
import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta
import traceback


def check_file_system_health():
    """Check file system and directory structure."""
    print("Checking File System Health")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Required directories
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
    
    # Create missing directories
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                checks["issues"].append(f"Failed to create directory {dir_path}: {e}")
                checks["status"] = "failed"
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            checks["issues"].append(f"Missing directory: {dir_path}")
            checks["status"] = "failed"
        else:
            # Check if directory is writable
            try:
                import os
                if not os.access(path, os.W_OK):
                    checks["issues"].append(f"Directory not writable: {dir_path}")
                    checks["status"] = "warning"
                
                # Count files
                file_count = len(list(path.rglob("*")))
                checks["details"][dir_path] = {
                    "exists": True,
                    "file_count": file_count,
                    "writable": os.access(path, os.W_OK)
                }
            except Exception as e:
                checks["issues"].append(f"Error checking directory {dir_path}: {e}")
                checks["status"] = "warning"
    
    # Check disk space (skip on Windows)
    try:
        import platform
        if platform.system() == 'Windows':
            # Skip disk space check on Windows
            checks["details"]["disk_space"] = {"skipped": True, "reason": "Windows platform"}
        else:
            stat = os.statvfs(".")
            free_space = stat.f_frsize * stat.f_bavail
            total_space = stat.f_frsize * stat.f_blocks
            free_percent = (free_space / total_space) * 100
            
            checks["details"]["disk_space"] = {
                "free_gb": round(free_space / (1024**3), 2),
                "total_gb": round(total_space / (1024**3), 2),
                "free_percent": round(free_percent, 2)
            }
            
            if free_percent < 10:
                checks["issues"].append(f"Low disk space: {free_percent:.1f}% free")
                checks["status"] = "warning"
            
    except Exception as e:
        checks["issues"].append(f"Error checking disk space: {e}")
        checks["status"] = "warning"
    
    print(f"File System Health: {checks['status'].upper()}")
    return checks


def check_data_freshness():
    """Check if data is fresh and up-to-date."""
    print("Checking Data Freshness")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Check last update info
    last_update_file = Path("cache/last_update_info.json")
    
    if not last_update_file.exists():
        checks["issues"].append("No last update information found")
        checks["status"] = "warning"
        return checks
    
    try:
        with open(last_update_file, 'r') as f:
            last_update = json.load(f)
        
        last_update_time = datetime.fromisoformat(last_update.get('timestamp', ''))
        time_since_update = datetime.now() - last_update_time
        
        checks["details"]["last_update"] = {
            "timestamp": last_update.get('timestamp'),
            "hours_ago": time_since_update.total_seconds() / 3600,
            "update_type": last_update.get('update_type', 'unknown')
        }
        
        # Check if data is stale (older than 48 hours)
        if time_since_update > timedelta(hours=48):
            checks["issues"].append(f"Data is stale: {time_since_update.total_seconds() / 3600:.1f} hours old")
            checks["status"] = "warning"
        
        # Check if data is very old (older than 7 days)
        if time_since_update > timedelta(days=7):
            checks["issues"].append(f"Data is very old: {time_since_update.days} days old")
            checks["status"] = "failed"
            
    except Exception as e:
        checks["issues"].append(f"Error reading last update info: {e}")
        checks["status"] = "failed"
    
    print(f"Data Freshness: {checks['status'].upper()}")
    return checks


def check_external_connectivity():
    """Check connectivity to external data sources."""
    print("Checking External Connectivity")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Test URLs to check
    test_urls = [
        {
            "name": "HDFC Mutual Fund",
            "url": "https://hdfcfund.com/",
            "timeout": 10
        },
        {
            "name": "Groww",
            "url": "https://groww.in/",
            "timeout": 10
        }
    ]
    
    for site in test_urls:
        try:
            response = requests.get(site["url"], timeout=site["timeout"])
            
            checks["details"][site["name"]] = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "accessible": response.status_code == 200
            }
            
            if response.status_code != 200:
                checks["issues"].append(f"{site['name']} returned status {response.status_code}")
                checks["status"] = "warning"
                
        except requests.exceptions.Timeout:
            checks["issues"].append(f"{site['name']} timeout after {site['timeout']}s")
            checks["details"][site["name"]] = {
                "error": "timeout",
                "accessible": False
            }
            checks["status"] = "warning"
            
        except Exception as e:
            checks["issues"].append(f"{site['name']} connection error: {e}")
            checks["details"][site["name"]] = {
                "error": str(e),
                "accessible": False
            }
            checks["status"] = "failed"
    
    print(f"External Connectivity: {checks['status'].upper()}")
    return checks


def check_pipeline_integrity():
    """Check integrity of pipeline components."""
    print("Checking Pipeline Integrity")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Check if this is initial setup (no pipeline runs yet)
    pipeline_runs = 0
    
    # Check Phase 1 results
    phase1_file = Path("cache/phase1_results/collection_results.json")
    if phase1_file.exists():
        pipeline_runs += 1
        try:
            with open(phase1_file, 'r') as f:
                phase1_data = json.load(f)
            
            checks["details"]["phase1"] = {
                "exists": True,
                "success": phase1_data.get("success", False),
                "documents_collected": phase1_data.get("documents_collected", 0),
                "funds_processed": len(phase1_data.get("fund_results", {}))
            }
            
            if not phase1_data.get("success", False):
                checks["issues"].append("Phase 1 collection was not successful")
                checks["status"] = "warning"
                
        except Exception as e:
            checks["issues"].append(f"Error reading Phase 1 results: {e}")
            checks["details"]["phase1"] = {"exists": True, "error": str(e)}
            checks["status"] = "failed"
    else:
        checks["details"]["phase1"] = {"exists": False, "note": "No pipeline runs yet"}
    
    # Check Phase 2.1 results
    phase2_1_file = Path("cache/phase2_1_results/chunking_results.json")
    if phase2_1_file.exists():
        pipeline_runs += 1
        try:
            with open(phase2_1_file, 'r') as f:
                phase2_1_data = json.load(f)
            
            checks["details"]["phase2_1"] = {
                "exists": True,
                "success": phase2_1_data.get("success", False),
                "chunks_generated": phase2_1_data.get("chunks_generated", 0)
            }
            
            if not phase2_1_data.get("success", False):
    # Check Phase 2.2 results
    phase2_2_file = Path("cache/phase2_2_results/phase2_2_results.json")
    if phase2_2_file.exists():
        try:
            with open(phase2_2_file, 'r') as f:
                phase2_2_data = json.load(f)
            
            checks["details"]["phase2_2"] = {
                "exists": True,
                "success": phase2_2_data.get("success", False),
                "step_count": len(phase2_2_data.get("step_results", {}))
            }
            
            if not phase2_2_data.get("success", False):
                checks["issues"].append("Phase 2.2 vector store setup was not successful")
                checks["status"] = "warning"
                
        except Exception as e:
            checks["issues"].append(f"Error reading Phase 2.2 results: {e}")
            checks["details"]["phase2_2"] = {"exists": True, "error": str(e)}
            checks["status"] = "failed"
    else:
        checks["issues"].append("Phase 2.2 results file not found")
        checks["details"]["phase2_2"] = {"exists": False}
        checks["status"] = "failed"
    
    # Check Phase 2.3 results
    phase2_3_file = Path("cache/phase2_3_results/phase2_3_results.json")
    if phase2_3_file.exists():
        try:
            with open(phase2_3_file, 'r') as f:
                phase2_3_data = json.load(f)
            
            checks["details"]["phase2_3"] = {
                "exists": True,
                "success": phase2_3_data.get("success", False),
                "step_count": len(phase2_3_data.get("step_results", {}))
            }
            
            if not phase2_3_data.get("success", False):
                checks["issues"].append("Phase 2.3 retrieval system was not successful")
                checks["status"] = "warning"
                
        except Exception as e:
            checks["issues"].append(f"Error reading Phase 2.3 results: {e}")
            checks["details"]["phase2_3"] = {"exists": True, "error": str(e)}
            checks["status"] = "failed"
    else:
        checks["issues"].append("Phase 2.3 results file not found")
        checks["details"]["phase2_3"] = {"exists": False}
        checks["status"] = "failed"
    
    print(f"Pipeline Integrity: {checks['status'].upper()}")
    return checks


def check_performance_benchmarks():
    """Check if performance benchmarks are met."""
    print("Checking Performance Benchmarks")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Load latest performance report
    performance_file = Path("performance_reports/latest_performance_report.json")
    
    if not performance_file.exists():
        checks["issues"].append("No performance report found")
        checks["status"] = "warning"
        return checks
    
    try:
        with open(performance_file, 'r') as f:
            perf_data = json.load(f)
        
        # Performance targets
        targets = {
            "query_processing": 1.0,    # 1 second
            "search_engine": 0.5,       # 0.5 seconds
            "context_builder": 0.5,     # 0.5 seconds
            "end_to_end": 2.0           # 2 seconds total
        }
        
        if "summary" in perf_data and "targets_met" in perf_data["summary"]:
            targets_met = perf_data["summary"]["targets_met"]
            
            for target_name, target_data in targets_met.items():
                if target_name in targets:
                    actual = target_data.get("actual", 0)
                    target = targets[target_name]
                    met = target_data.get("met", False)
                    
                    checks["details"][target_name] = {
                        "target": target,
                        "actual": actual,
                        "met": met
                    }
                    
                    if not met:
                        checks["issues"].append(f"{target_name} performance not met: {actual:.3f}s > {target:.1f}s")
                        checks["status"] = "warning"
        
        # Check success rates
        if "summary" in perf_data and "success_rates" in perf_data["summary"]:
            success_rates = perf_data["summary"]["success_rates"]
            
            for test_name, success_rate in success_rates.items():
                checks["details"][f"{test_name}_success_rate"] = success_rate
                
                if success_rate < 0.8:  # 80% success rate threshold
                    checks["issues"].append(f"{test_name} success rate low: {success_rate:.1%}")
                    checks["status"] = "warning"
        
    except Exception as e:
        checks["issues"].append(f"Error reading performance report: {e}")
        checks["status"] = "failed"
    
    print(f"Performance Benchmarks: {checks['status'].upper()}")
    return checks


def check_github_actions_status():
    """Check GitHub Actions workflow status."""
    print("Checking GitHub Actions Status")
    
    checks = {
        "status": "passed",
        "issues": [],
        "details": {}
    }
    
    # Check if workflow files exist
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        checks["issues"].append("GitHub workflows directory not found")
        checks["status"] = "failed"
        return checks
    
    workflow_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
    
    checks["details"]["workflow_count"] = len(workflow_files)
    
    if len(workflow_files) == 0:
        checks["issues"].append("No GitHub workflow files found")
        checks["status"] = "warning"
    
    # Check for data update pipeline
    data_pipeline_file = workflow_dir / "data-update-pipeline.yml"
    if not data_pipeline_file.exists():
        checks["issues"].append("Data update pipeline workflow not found")
        checks["status"] = "failed"
    else:
        checks["details"]["data_pipeline_workflow"] = True
    
    # Check workflow syntax (basic)
    for workflow_file in workflow_files:
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Basic syntax checks
            if "name:" not in content:
                checks["issues"].append(f"Workflow {workflow_file.name} missing name")
                checks["status"] = "warning"
            
            if "on:" not in content:
                checks["issues"].append(f"Workflow {workflow_file.name} missing trigger")
                checks["status"] = "warning"
                
        except Exception as e:
            checks["issues"].append(f"Error reading workflow {workflow_file.name}: {e}")
            checks["status"] = "warning"
    
    print(f"GitHub Actions Status: {checks['status'].upper()}")
    return checks


def generate_health_report():
    """Generate comprehensive health report."""
    print("Generating System Health Report")
    print("=" * 60)
    
    # Run all health checks
    health_checks = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {}
    }
    
    checks_to_run = [
        ("file_system", check_file_system_health),
        ("data_freshness", check_data_freshness),
        ("external_connectivity", check_external_connectivity),
        ("pipeline_integrity", check_pipeline_integrity),
        ("performance_benchmarks", check_performance_benchmarks),
        ("github_actions", check_github_actions_status)
    ]
    
    for check_name, check_func in checks_to_run:
        try:
            check_result = check_func()
            health_checks["checks"][check_name] = check_result
            
            # Update overall status
            if check_result["status"] == "failed":
                health_checks["overall_status"] = "unhealthy"
            elif check_result["status"] == "warning" and health_checks["overall_status"] != "unhealthy":
                health_checks["overall_status"] = "degraded"
                
        except Exception as e:
            print(f"Health check {check_name} failed: {e}")
            health_checks["checks"][check_name] = {
                "status": "failed",
                "issues": [f"Health check error: {e}"],
                "details": {}
            }
            health_checks["overall_status"] = "unhealthy"
    
    # Save health report
    health_dir = Path("cache/health_reports")
    health_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    health_file = health_dir / f"health_report_{timestamp}.json"
    
    with open(health_file, 'w') as f:
        json.dump(health_checks, f, indent=2)
    
    # Also save latest
    latest_file = health_dir / "latest_health_report.json"
    with open(latest_file, 'w') as f:
        json.dump(health_checks, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Overall System Health: {health_checks['overall_status'].upper()}")
    
    for check_name, check_result in health_checks["checks"].items():
        status_emoji = "PASS" if check_result["status"] == "passed" else "WARN" if check_result["status"] == "warning" else "FAIL"
        print(f"{status_emoji} {check_name.replace('_', ' ').title()}: {check_result['status'].upper()}")
        
        if check_result["issues"]:
            for issue in check_result["issues"]:
                print(f"   - {issue}")
    
    print(f"Health report saved: {health_file}")
    
    return health_checks


def main():
    """Main function to run health checks."""
    try:
        health_report = generate_health_report()
        
        # Exit with appropriate code
        if health_report["overall_status"] == "unhealthy":
            print("System health check FAILED")
            sys.exit(1)
        elif health_report["overall_status"] == "degraded":
            print("System health check completed with WARNINGS")
            sys.exit(0)
        else:
            print("System health check PASSED")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during health check: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
