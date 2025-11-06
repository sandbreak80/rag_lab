#!/usr/bin/env python3
"""
Quick frontend test to check for console errors
"""
import subprocess
import sys
import time

def test_frontend():
    """Test if frontend loads without errors"""
    print("🧪 Testing Frontend...")
    
    # Check if frontend container is running
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=rag-frontend", "--format", "{{.Status}}"],
        capture_output=True,
        text=True
    )
    
    if "Up" not in result.stdout:
        print("❌ Frontend container not running!")
        return False
    
    print("✅ Frontend container is running")
    
    # Check if homepage returns HTML
    result = subprocess.run(
        ["curl", "-s", "http://localhost:3000"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if "<div id=\"root\"></div>" not in result.stdout:
        print("❌ Homepage doesn't contain root div!")
        return False
    
    print("✅ Homepage returns valid HTML")
    
    # Check if JS file exists
    result = subprocess.run(
        ["curl", "-s", "-I", "http://localhost:3000/assets/index-CdkHdshw.js"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if "200 OK" not in result.stdout:
        print("❌ JavaScript file not found!")
        return False
    
    print("✅ JavaScript file exists")
    
    print("\n⚠️  Cannot check browser console errors without browser")
    print("   Manual test required: Open http://localhost:3000 and check F12 console")
    
    return True

if __name__ == "__main__":
    success = test_frontend()
    sys.exit(0 if success else 1)

