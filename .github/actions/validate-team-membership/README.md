# Validate Team Membership

A security-focused GitHub Action for validating user membership in specific GitHub teams. This action provides team-based authorization for sensitive workflows, ensuring only authorized team members can trigger critical operations like release preparation or infrastructure changes.

## Features

- **Team-based authorization**: Validate user membership in GitHub teams
- **Flexible organization support**: Works with any GitHub organization
- **Secure API integration**: Uses GitHub CLI for reliable team membership checks
- **Clear authorization feedback**: Detailed success/failure notifications
- **FOLIO workflow integration**: Designed for FOLIO's team-based access control

## Usage

### Basic Example

```yaml
- name: Validate User Authorization
  id: auth-check
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: kitfox
    token: ${{ secrets.GITHUB_TOKEN }}

- name: Proceed if Authorized
  if: steps.auth-check.outputs.authorized == 'true'
  run: echo "User is authorized to proceed"

- name: Block Unauthorized Access
  if: steps.auth-check.outputs.authorized != 'true'
  run: |
    echo "::error::Unauthorized access attempt"
    exit 1
```

### FOLIO Release Preparation Example

```yaml
name: Release Preparation
on:
  workflow_dispatch:
    inputs:
      previous_release_branch:
        required: true
      new_release_branch:
        required: true

jobs:
  authorize:
    runs-on: ubuntu-latest
    outputs:
      authorized: ${{ steps.team-check.outputs.authorized }}
    steps:
      - name: Validate Kitfox Team Membership
        id: team-check
        uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
          organization: folio-org
          team: kitfox
          token: ${{ secrets.GITHUB_TOKEN }}

  release-preparation:
    needs: authorize
    if: needs.authorize.outputs.authorized == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Execute Release Preparation
        run: echo "Starting release preparation..."
```

### Multi-Team Authorization

```yaml
- name: Check Platform Team Access
  id: platform-auth
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: platform-team
    token: ${{ secrets.GITHUB_TOKEN }}

- name: Check Kitfox Team Access
  id: kitfox-auth
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: kitfox
    token: ${{ secrets.GITHUB_TOKEN }}

- name: Proceed with Any Team Access
  if: steps.platform-auth.outputs.authorized == 'true' || steps.kitfox-auth.outputs.authorized == 'true'
  run: echo "User has required team access"
```

### Different Organization Example

```yaml
- name: Validate External Organization Access
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    organization: my-org
    team: developers
    token: ${{ secrets.CROSS_ORG_TOKEN }}
```

## Inputs

| Input          | Description                                     | Required  | Default     |
|----------------|-------------------------------------------------|-----------|-------------|
| `username`     | GitHub username to check team membership for    | ✅         | -           |
| `organization` | GitHub organization name                        | ❌         | `folio-org` |
| `team`         | Team name to check membership for               | ❌         | `kitfox`    |
| `token`        | GitHub token with organization read permissions | ✅         | -           |

## Outputs

| Output       | Description                    | Values            |
|--------------|--------------------------------|-------------------|
| `authorized` | Whether the user is authorized | `true` or `false` |

## How It Works

1. **API Authentication**: Uses the provided GitHub token for API access
2. **Team Membership Query**: Calls GitHub API to check user's team membership
3. **Status Validation**: Verifies the membership status is "active"
4. **Authorization Response**: Returns boolean result for workflow decision making

## Requirements

### GitHub CLI
This action uses the GitHub CLI (`gh`) which is pre-installed on GitHub runners.

### Permissions
The GitHub token needs appropriate permissions:

```yaml
permissions:
  contents: read        # Basic repository access
  organization: read    # To read team memberships
```

### Team Visibility
- **Public teams**: Any token with org read access can check membership
- **Private teams**: Token must belong to a team member or org admin

## Security Considerations

### Token Security
- **Use secrets**: Always pass tokens via `${{ secrets.TOKEN_NAME }}`
- **Minimal permissions**: Use tokens with only required permissions
- **Token rotation**: Regularly rotate tokens used for authorization

### Team Privacy
- **Private teams**: Membership checks respect team privacy settings
- **Audit trails**: All authorization attempts are logged in workflow runs
- **Least privilege**: Only grant team access to users who need it

### Authorization Patterns
```yaml
# ✅ GOOD: Fail securely
- name: Check Authorization
  id: auth
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    token: ${{ secrets.GITHUB_TOKEN }}

- name: Critical Operation
  if: steps.auth.outputs.authorized == 'true'
  run: echo "Authorized operation"

# ❌ BAD: Fails open
- name: Critical Operation  
  if: steps.auth.outputs.authorized != 'false'  # Allows on failure!
  run: echo "Potentially unauthorized operation"
```

## FOLIO Integration

### Team Structure
This action integrates with FOLIO's team-based access control:

- **Kitfox Team**: Infrastructure and DevOps operations
- **Platform Teams**: Core platform development
- **Domain Teams**: Application-specific development
- **Release Managers**: Release coordination and approval

### Common Use Cases

#### Release Preparation Authorization
```yaml
- name: Authorize Release Preparation
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: kitfox
    token: ${{ secrets.GITHUB_TOKEN }}
```

#### Infrastructure Changes
```yaml
- name: Authorize Infrastructure Changes
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: kitfox
    token: ${{ secrets.GITHUB_TOKEN }}
```

#### Application Deployment
```yaml
- name: Authorize Production Deployment
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    team: ${{ inputs.responsible_team }}
    token: ${{ secrets.GITHUB_TOKEN }}
```

## Error Handling

### Common Scenarios

**User Not in Team**
```yaml
- name: Handle Authorization Failure
  if: steps.auth.outputs.authorized != 'true'
  run: |
    echo "::error::Access denied. Contact team lead for access."
    echo "Required team: ${{ inputs.team }}"
    echo "User: ${{ github.actor }}"
    exit 1
```

**API Errors**
```yaml
- name: Validate Team Membership
  id: auth
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    token: ${{ secrets.GITHUB_TOKEN }}
  continue-on-error: true

- name: Handle API Failure
  if: steps.auth.outcome == 'failure'
  run: |
    echo "::error::Unable to verify team membership. Check token permissions."
    exit 1
```

## Best Practices

### Security-First Design
- **Fail closed**: Default to denying access on errors
- **Clear messaging**: Provide clear authorization failure messages
- **Audit logging**: Ensure all authorization attempts are logged
- **Regular reviews**: Periodically review team memberships

### Workflow Integration
```yaml
# Separate authorization job for clarity
jobs:
  authorize:
    runs-on: ubuntu-latest
    outputs:
      authorized: ${{ steps.check.outputs.authorized }}
    steps:
      - name: Check Team Membership
        id: check
        uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
          token: ${{ secrets.GITHUB_TOKEN }}

  protected-operation:
    needs: authorize
    if: needs.authorize.outputs.authorized == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Execute Protected Operation
        run: echo "Authorized operation"
```

### Token Management
```yaml
# Use organization-scoped tokens for team checks
- name: Check Membership
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    token: ${{ secrets.ORG_READ_TOKEN }}  # Dedicated token for team checks
```

## Troubleshooting

### Common Issues

**Permission Denied**
- Verify token has `org:read` permissions
- Check if the team is private and token user has access
- Ensure organization name is correct

**User Not Found**
- Verify username spelling and case
- Check if user exists in the organization
- Confirm user hasn't left the organization

**Team Not Found**
- Verify team name spelling and case
- Check if team exists in the specified organization
- Ensure team hasn't been renamed or deleted

**API Rate Limiting**
- Use authenticated tokens to increase rate limits
- Implement retry logic for critical workflows
- Consider caching results for repeated checks

### Debugging Tips

**Enable Debug Logging**
```yaml
- name: Debug Team Check
  uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
  with:
    username: ${{ github.actor }}
    token: ${{ secrets.GITHUB_TOKEN }}
  env:
    ACTIONS_STEP_DEBUG: true
```

**Manual API Testing**
```bash
# Test team membership manually
gh api "orgs/folio-org/teams/kitfox/memberships/username" --jq '.state'
```

## Integration Examples

### With Workflow Dispatch
```yaml
on:
  workflow_dispatch:
    inputs:
      target_environment:
        type: choice
        options: [staging, production]

jobs:
  authorize-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Authorize Production Deployment
        if: inputs.target_environment == 'production'
        uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
        with:
          username: ${{ github.actor }}
          team: kitfox
          token: ${{ secrets.GITHUB_TOKEN }}
```

### With Matrix Strategies
```yaml
strategy:
  matrix:
    team: [kitfox, platform-team, domain-team]
steps:
  - name: Check Team Access
    id: auth-${{ matrix.team }}
    uses: folio-org/kitfox-github/.github/actions/validate-team-membership@main
    with:
      username: ${{ github.actor }}
      team: ${{ matrix.team }}
      token: ${{ secrets.GITHUB_TOKEN }}
```

## Contributing

This action is part of the FOLIO Kitfox infrastructure. For issues or improvements:

1. Create an issue in the kitfox-github repository
2. Follow FOLIO security review processes for authorization changes
3. Include Kitfox team members in security-related reviews
4. Test authorization logic thoroughly before deployment

## License

Apache License 2.0 - See the LICENSE file in the repository root. 