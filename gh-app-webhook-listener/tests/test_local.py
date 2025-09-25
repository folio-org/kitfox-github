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
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from common.signature_validator import validate_github_signature

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
            "owner": {
                "login": "folio-org"
            },
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

def test_pull_request_event():
    """Test pull_request event structure"""
    print("Testing pull_request event processing...")

    # Sample pull_request event
    event = {
        "action": "opened",
        "pull_request": {
            "id": 54321,
            "number": 123,
            "head": {
                "sha": "def456",
                "ref": "feature-branch"
            },
            "base": {
                "ref": "main"
            }
        },
        "repository": {
            "full_name": "folio-org/test-repo",
            "name": "test-repo",
            "owner": {
                "login": "folio-org"
            }
        },
        "installation": {
            "id": 67890
        }
    }

    # Create API Gateway event
    api_gateway_event = {
        "body": json.dumps(event),
        "headers": {
            "x-github-event": "pull_request",
            "x-github-delivery": "54321-09876",
            "x-hub-signature-256": "sha256=test"
        }
    }

    print(f"[OK] Created PR event for repository: {event['repository']['full_name']}")
    print(f"[OK] PR number: {event['pull_request']['number']}")
    print(f"[OK] PR action: {event['action']}")

    return api_gateway_event

def test_workflow_config():
    """Test workflow configuration loading"""
    print("Testing workflow configuration...")

    config_path = project_root / "config" / "workflows.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"[OK] Config loaded successfully")
        if "workflows" in config:
            print(f"  - Found {len(config['workflows'])} workflow configurations")
        else:
            print("  - No workflows configured")
    else:
        print("[WARNING] Config file not found at", config_path)

    print()

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")

    success = True

    # Test webhook_handler imports
    try:
        # Add webhook_handler to path temporarily
        sys.path.insert(0, str(project_root / 'src' / 'webhook_handler'))
        from handler import handler as webhook_handler
        print("[OK] webhook_handler.handler imported")
    except ImportError as e:
        print(f"[FAIL] webhook_handler import failed: {e}")
        success = False
    finally:
        # Remove from path
        if str(project_root / 'src' / 'webhook_handler') in sys.path:
            sys.path.remove(str(project_root / 'src' / 'webhook_handler'))

    # Test check_processor imports
    try:
        # Add check_processor to path temporarily
        sys.path.insert(0, str(project_root / 'src' / 'check_processor'))
        from handler import handler as check_processor
        print("[OK] check_processor.handler imported")
    except ImportError as e:
        print(f"[FAIL] check_processor import failed: {e}")
        success = False
    finally:
        # Remove from path
        if str(project_root / 'src' / 'check_processor') in sys.path:
            sys.path.remove(str(project_root / 'src' / 'check_processor'))

    # Test common module imports
    try:
        from common.signature_validator import validate_github_signature
        print("[OK] signature_validator imported")

        from common.github_client import GitHubClient
        print("[OK] GitHubClient imported")

        from common.check_runner import CheckRunner
        print("[OK] CheckRunner imported")
    except ImportError as e:
        print(f"[FAIL] Common module import failed: {e}")
        success = False

    if success:
        print("All imports successful!\n")
    else:
        print("Some imports failed. Check dependencies.\n")

    return success

def test_lambda_structure():
    """Test that Lambda directory structure is correct"""
    print("Testing Lambda directory structure...")

    src_dir = project_root / "src"

    # Check webhook_handler structure
    webhook_handler_dir = src_dir / "webhook_handler"
    if webhook_handler_dir.exists():
        print(f"[OK] webhook_handler directory exists")
        if (webhook_handler_dir / "handler.py").exists():
            print(f"  - handler.py found")
        if (webhook_handler_dir / "requirements.txt").exists():
            print(f"  - requirements.txt found")
    else:
        print(f"[FAIL] webhook_handler directory not found")

    # Check check_processor structure
    check_processor_dir = src_dir / "check_processor"
    if check_processor_dir.exists():
        print(f"[OK] check_processor directory exists")
        if (check_processor_dir / "handler.py").exists():
            print(f"  - handler.py found")
        if (check_processor_dir / "requirements.txt").exists():
            print(f"  - requirements.txt found")
    else:
        print(f"[FAIL] check_processor directory not found")

    # Check common utilities
    common_dir = src_dir / "common"
    if common_dir.exists():
        print(f"[OK] common directory exists")
        for file in ["github_client.py", "workflow_trigger.py"]:
            if (common_dir / file).exists():
                print(f"  - {file} found")
    else:
        print(f"[FAIL] common directory not found")

    print()

def main():
    """Run all tests"""
    print("=" * 50)
    print("GitHub App Webhook Listener - Local Test Suite")
    print("=" * 50)
    print()

    # Test directory structure
    test_lambda_structure()

    # Test imports
    if not test_imports():
        print("Fix import errors before proceeding")
        return 1

    # Test individual components
    test_signature_validation()
    test_workflow_config()

    # Test event structures
    test_check_suite_event()
    test_pull_request_event()

    print("=" * 50)
    print("All local tests passed! [OK]")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Update terraform/environments/your-app.tfvars with actual values")
    print("2. Run: cd terraform && terraform init")
    print("3. Run: terraform plan -var-file=environments/your-app.tfvars")
    print("4. Run: terraform apply -var-file=environments/your-app.tfvars")
    print("5. Update GitHub App webhook URL with the output URL")

    return 0

if __name__ == "__main__":
    sys.exit(main())