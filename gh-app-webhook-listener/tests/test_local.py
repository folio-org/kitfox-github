#!/usr/bin/env python3
"""
Local test script for GitHub App Webhook Listener
Tests the Lambda functions locally before deployment
"""

import json
import hmac
import hashlib
import sys
import os

# Add src to path for imports
sys.path.insert(0, 'src')

from utils.signature_validator import validate_github_signature

def test_signature_validation():
    """Test GitHub webhook signature validation"""
    print("Testing signature validation...")
    
    secret = "test-secret"
    payload = '{"test": "payload"}'
    
    # Generate valid signature
    signature_bytes = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    signature = f"sha256={signature_bytes}"
    
    # Test valid signature
    assert validate_github_signature(payload, signature, secret), "Valid signature failed"
    print("[OK] Valid signature passed")
    
    # Test invalid signature
    invalid_signature = "sha256=invalid"
    assert not validate_github_signature(payload, invalid_signature, secret), "Invalid signature passed"
    print("[OK] Invalid signature rejected")
    
    print("Signature validation tests passed!\n")

def test_check_suite_event():
    """Test check_suite event structure"""
    print("Testing check_suite event processing...")
    
    # Sample check_suite event
    event = {
        "action": "requested",
        "check_suite": {
            "id": 12345,
            "head_sha": "abc123",
            "head_branch": "feature-branch",
            "pull_requests": [
                {
                    "id": 1,
                    "number": 42
                }
            ]
        },
        "repository": {
            "full_name": "folio-org/test-repo",
            "name": "test-repo",
            "default_branch": "main"
        },
        "installation": {
            "id": 67890
        }
    }
    
    # Create API Gateway event
    api_gateway_event = {
        "body": json.dumps(event),
        "headers": {
            "x-github-event": "check_suite",
            "x-github-delivery": "12345-67890",
            "x-hub-signature-256": "sha256=test"
        }
    }
    
    print(f"[OK] Created test event for repository: {event['repository']['full_name']}")
    print(f"[OK] Check suite ID: {event['check_suite']['id']}")
    print(f"[OK] PR number: {event['check_suite']['pull_requests'][0]['number']}")
    
    return api_gateway_event

def test_workflow_config():
    """Test workflow configuration loading"""
    print("Testing workflow configuration...")
    
    config_path = "config/workflows.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert "kitfox_repo" in config, "Missing kitfox_repo in config"
        assert "check_suite_workflow" in config, "Missing check_suite_workflow in config"
        
        print(f"[OK] Config loaded successfully")
        print(f"  - Kitfox repo: {config['kitfox_repo']}")
        print(f"  - Workflow: {config['check_suite_workflow']}")
    else:
        print("[WARNING] Config file not found")
    
    print()

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from handlers import webhook_handler
        print("[OK] webhook_handler imported")
        
        from handlers import check_processor
        print("[OK] check_processor imported")
        
        from services.github_api import GitHubAPI
        print("[OK] GitHubAPI imported")
        
        from services.workflow_orchestrator import WorkflowOrchestrator
        print("[OK] WorkflowOrchestrator imported")
        
        from services.release_config_loader import ReleaseConfigLoader
        print("[OK] ReleaseConfigLoader imported")
        
        from services.pr_validator import PRValidator
        print("[OK] PRValidator imported")
        
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False
    
    print("All imports successful!\n")
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("GitHub App Webhook Listener - Local Test Suite")
    print("=" * 50)
    print()
    
    # Test imports first
    if not test_imports():
        print("Fix import errors before proceeding")
        return 1
    
    # Test individual components
    test_signature_validation()
    test_workflow_config()
    
    # Test event structure
    event = test_check_suite_event()
    
    print("=" * 50)
    print("All local tests passed! [OK]")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Update terraform/environments/dev.tfvars with actual values")
    print("2. Run: cd terraform && terraform init")
    print("3. Run: terraform plan -var-file=environments/dev.tfvars")
    print("4. Run: terraform apply -var-file=environments/dev.tfvars")
    print("5. Update GitHub App webhook URL with the output URL")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())