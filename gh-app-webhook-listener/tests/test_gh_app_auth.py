import os
import json
import jwt   # PyJWT
import time
import requests
import base64
from pathlib import Path

# Values should be stored securely in AWS Secrets Manager or env vars
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH", "~/.ssh/key.pem")

# If you stored a base64-encoded PEM (one-liner), set this to "true"
GITHUB_PRIVATE_KEY_BASE64 = os.getenv("GITHUB_PRIVATE_KEY_BASE64", "false").lower() == "true"

def load_private_key_from_file() -> str:
    path = Path(GITHUB_PRIVATE_KEY_PATH)
    if not path.exists():
        raise FileNotFoundError(f"GitHub App private key file not found: {path}")

    data = path.read_bytes()
    if GITHUB_PRIVATE_KEY_BASE64:
        try:
            data = base64.b64decode(data)
        except Exception as e:
            raise ValueError(f"Failed to base64-decode private key from {path}: {e}")

    pem = data.decode("utf-8")
    if "-----BEGIN" not in pem:
        # Helpful guard: you likely forgot to set GITHUB_PRIVATE_KEY_BASE64=true
        raise ValueError("Private key doesn't look like a PEM. "
                         "If you stored it base64-encoded, set GITHUB_PRIVATE_KEY_BASE64=true.")
    return pem

def get_jwt() -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        # issued at time
        "iat": now,
        # JWT expiration time (max 10 min)
        "exp": now + 9 * 60,
        # GitHub App's identifier
        "iss": GITHUB_APP_ID
    }
    private_key_pem = load_private_key_from_file()
    return jwt.encode(payload, private_key_pem, algorithm="RS256")

def get_installation_token(jwt_token: str) -> str:
    """Exchange JWT for an installation access token."""
    url = f"https://api.github.com/app/installations/{GITHUB_INSTALLATION_ID}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["token"]

# Step 1: Create JWT
app_jwt = get_jwt()

# Step 2: Get installation access token
installation_token = get_installation_token(app_jwt)

# Step 3: Use the token to call GitHub API
url = "https://api.github.com/repos/octocat/Hello-World"
headers = {
    "Authorization": f"token {installation_token}",
    "Accept": "application/vnd.github+json"
}
repo_info = requests.get(url, headers=headers).json()

response = {
    "statusCode": 200,
    "body": json.dumps({
        "repository": repo_info.get("full_name"),
        "private": repo_info.get("private"),
    })
}

print(f"body: {response}")
