#!/usr/bin/env python3
"""
Script to check for data changes and decide if update pipeline should run.
"""
import argparse
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta
import sys


def get_last_update_info():
    """Get information about the last successful update."""
    last_update_file = Path("cache/last_update_info.json")
    
    if not last_update_file.exists():
        return None
    
    try:
        with open(last_update_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def check_hdfc_website_changes():
    """Check if HDFC website has been updated."""
    try:
        # Check key HDFC fund pages
        urls = [
            "https://hdfcfund.com/",
            "https://hdfcfund.com/mutual-funds",
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund"
        ]
        
        changes_detected = False
        current_hashes = {}
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    content_hash = hashlib.md5(response.content).hexdigest()
                    current_hashes[url] = content_hash
                    
                    # Compare with stored hash
                    hash_file = Path(f"cache/hashes/{hashlib.md5(url.encode()).hexdigest()}.txt")
                    
                    if hash_file.exists():
                        with open(hash_file, 'r') as f:
                            stored_hash = f.read().strip()
                        
                        if stored_hash != content_hash:
                            changes_detected = True
                            print(f"Changes detected in: {url}")
                    else:
                        changes_detected = True
                        print(f"First time checking: {url}")
                    
                    # Save current hash
                    hash_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(hash_file, 'w') as f:
                        f.write(content_hash)
                        
            except Exception as e:
                print(f"Error checking {url}: {e}")
                continue
        
        return changes_detected, current_hashes
        
    except Exception as e:
        print(f"Error checking HDFC website: {e}")
        return False, {}


def check_data_freshness():
    """Check if existing data is still fresh enough."""
    last_update = get_last_update_info()
    
    if not last_update:
        return True  # No previous data, need update
    
    try:
        last_update_time = datetime.fromisoformat(last_update.get('timestamp', ''))
        time_since_update = datetime.now() - last_update_time
        
        # Consider data stale after 24 hours
        if time_since_update > timedelta(hours=24):
            print(f"Data is {time_since_update.total_seconds() / 3600:.1f} hours old")
            return True
        
        print(f"Data is {time_since_update.total_seconds() / 3600:.1f} hours old (fresh)")
        return False
        
    except Exception as e:
        print(f"Error checking data freshness: {e}")
        return True  # Err on side of updating


def check_local_data_changes():
    """Check if local data files have changed."""
    data_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("cache/phase1_results"),
        Path("cache/phase2_1_results"),
        Path("cache/vector_db")
    ]
    
    changes_detected = False
    current_hashes = {}
    
    for data_dir in data_dirs:
        if not data_dir.exists():
            continue
        
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        current_hashes[str(file_path)] = file_hash
                        
                        # Compare with stored hash
                        hash_file = Path(f"cache/hashes/{hashlib.md5(str(file_path).encode()).hexdigest()}.txt")
                        
                        if hash_file.exists():
                            with open(hash_file, 'r') as f:
                                stored_hash = f.read().strip()
                            
                            if stored_hash != file_hash:
                                changes_detected = True
                                print(f"Local file changed: {file_path}")
                        else:
                            changes_detected = True
                            print(f"New local file: {file_path}")
                        
                        # Save current hash
                        hash_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(hash_file, 'w') as f:
                            f.write(file_hash)
                            
                except Exception as e:
                    print(f"Error hashing {file_path}: {e}")
                    continue
    
    return changes_detected, current_hashes


def main():
    parser = argparse.ArgumentParser(description="Check for data changes")
    parser.add_argument("--type", choices=["full", "incremental", "embeddings_only", "validation_only"], 
                       default="full", help="Type of update to check for")
    parser.add_argument("--force", action="store_true", help="Force update regardless of changes")
    
    args = parser.parse_args()
    
    print(f"Checking for data changes (type: {args.type})")
    
    changes_detected = False
    update_reasons = []
    
    # Check different types of changes
    if args.type in ["full", "incremental"]:
        # Check website changes
        website_changes, _ = check_hdfc_website_changes()
        if website_changes:
            changes_detected = True
            update_reasons.append("HDFC website updated")
        
        # Check data freshness
        data_stale = check_data_freshness()
        if data_stale:
            changes_detected = True
            update_reasons.append("Data is stale")
    
    # Check local changes
    local_changes, _ = check_local_data_changes()
    if local_changes:
        changes_detected = True
        update_reasons.append("Local data changed")
    
    # Force update
    if args.force:
        changes_detected = True
        update_reasons.append("Force update requested")
    
    # Output results for GitHub Actions
    if changes_detected:
        print(f"✅ Changes detected: {', '.join(update_reasons)}")
        print("has_changes=true")
        
        # Save update info
        update_info = {
            "timestamp": datetime.now().isoformat(),
            "update_type": args.type,
            "reasons": update_reasons,
            "changes_detected": True
        }
        
        Path("cache").mkdir(exist_ok=True)
        with open("cache/last_update_info.json", 'w') as f:
            json.dump(update_info, f, indent=2)
        
        sys.exit(0)
    else:
        print("❌ No changes detected")
        print("has_changes=false")
        sys.exit(1)


if __name__ == "__main__":
    main()
