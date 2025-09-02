# Verify Application Workflow

**Workflow**: `verify-application.yml`  
**Purpose**: Application descriptor validation and registry operations  
**Type**: Reusable workflow (`workflow_call`)

## 🎯 Overview

This workflow handles application descriptor validation and registry operations. It validates the generated application descriptor against FOLIO standards, checks module dependencies, and uploads the descriptor to the FOLIO Application Registry (FAR) for distribution.

## 📋 Workflow Interface

### Inputs

| Input                      | Description                                   | Required | Type    | Default |
|----------------------------|-----------------------------------------------|----------|---------|---------|
| `app_name`                 | Application name                              | Yes      | string  | -       |
| `app_descriptor_file`      | Path to generated application descriptor file | Yes      | string  | -       |
| `app_descriptor_file_name` | Name of application descriptor file           | Yes      | string  | -       |
| `rely_on_FAR`              | Use FAR for dependency validation             | No       | boolean | `false` |
| `dry_run`                  | Skip actual registry operations               | No       | boolean | `false` |
| `skip_upload`              | Skip FAR upload even if not dry-run           | No       | boolean | `false` |

### Outputs

| Output               | Description                                 |
|----------------------|---------------------------------------------|
| `app_descriptor_url` | URL of uploaded application descriptor      |
| `validation_status`  | Status of validation (success/failure)      |
| `validation_errors`  | Any validation errors encountered           |

### Secrets

| Secret | Description                       | Required |
|--------|-----------------------------------|----------|
| None   | Uses inherited workflow secrets   | -        |

## 🔄 Workflow Execution Flow

### 1. Download Application Descriptor
- Retrieves generated descriptor from artifacts
- Validates file existence and format
- Prepares for validation steps

### 2. Platform Descriptor Integration
- Downloads platform descriptor artifact (if available)
- Provides context for cross-application validation
- Enables dependency resolution checks

### 3. Module Interface Validation
- Validates module interface integrity via FAR API
- Checks module compatibility
- Ensures all required interfaces are satisfied
- Reports interface conflicts or missing dependencies

### 4. Application Dependency Validation
- Validates application-level dependencies
- Checks for circular dependencies
- Verifies version compatibility
- Uses FAR dependency resolver when `rely_on_FAR=true`

### 5. Registry Upload
- **Conditional**: Skipped if `dry_run=true` or `skip_upload=true`
- Uploads validated descriptor to FAR
- Makes application available for deployment
- Returns registry URL for reference

## 🛡️ Validation Types

### Structure Validation
- JSON schema compliance
- Required fields presence
- Version format validation
- Module reference integrity

### Interface Validation
```json
POST /validate
{
  "modules": [...],
  "interfaces": [...],
  "dependencies": [...]
}
```

### Dependency Validation
- **Local validation**: Using downloaded platform descriptor
- **FAR validation**: Using registry's dependency resolver
- **Cross-application**: Checking inter-application dependencies

## 📊 Usage Examples

### Basic Validation and Upload
```yaml
- uses: ./.github/workflows/verify-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    app_descriptor_file: ${{ needs.update.outputs.app_descriptor_file }}
    app_descriptor_file_name: ${{ needs.update.outputs.app_descriptor_file_name }}
```

### Validation with FAR Dependencies
```yaml
- uses: ./.github/workflows/verify-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    app_descriptor_file: descriptor.json
    app_descriptor_file_name: app-example-1.0.0.json
    rely_on_FAR: true
```

### Dry Run Validation Only
```yaml
- uses: ./.github/workflows/verify-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    app_descriptor_file: descriptor.json
    app_descriptor_file_name: app-example-1.0.0.json
    dry_run: true  # Skip upload
```

### Validation Without Upload
```yaml
- uses: ./.github/workflows/verify-application.yml
  with:
    app_name: ${{ inputs.app_name }}
    app_descriptor_file: descriptor.json
    app_descriptor_file_name: app-example-1.0.0.json
    skip_upload: true  # Validate only, no upload
```

## 🔍 FAR API Integration

### Validation Endpoint
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  --data-binary @descriptor.json \
  "$FAR_API_URL/validate"
```

### Upload Endpoint
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  --data-binary @descriptor.json \
  "$FAR_API_URL/applications"
```

### Dependency Resolution
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"applicationDescriptors": [...]}' \
  "$FAR_API_URL/validate-descriptors"
```

## 🚨 Error Handling

### Validation Failures
- **Schema errors**: Invalid JSON structure
- **Missing modules**: Referenced modules not found
- **Interface conflicts**: Incompatible module interfaces
- **Dependency issues**: Unresolved or circular dependencies

### Upload Failures
- **Network errors**: FAR unavailable
- **Duplicate versions**: Version already exists
- **Permission denied**: Invalid credentials
- **Size limits**: Descriptor too large

### Error Reporting
```yaml
outputs:
  validation_status: 'failed'
  validation_errors: |
    - Missing required interface: okapi.interface
    - Module version conflict: mod-users
    - Circular dependency detected
```

## 🧪 Testing Strategy

### Dry Run Behavior
When `dry_run: true`:
- ✅ All validation steps execute
- ✅ Errors are reported normally
- ❌ Registry upload is skipped
- ✅ Validation results available in outputs

### Test Scenarios
1. **Valid descriptor**: Should pass all validations
2. **Missing dependencies**: Should report specific missing items
3. **Interface conflicts**: Should identify conflicting modules
4. **Network failures**: Should handle gracefully with retry

## 📈 Performance Considerations

- **Caching**: Platform descriptor cached as artifact
- **Parallel validation**: Multiple checks run concurrently
- **Retry logic**: Automatic retry for transient failures
- **Timeout handling**: Reasonable timeouts for API calls

## 🔧 Troubleshooting

### Common Issues

**Validation timeout**:
```
Error: Validation request timed out
Solution: Check FAR API status and network connectivity
```

**Invalid descriptor format**:
```
Error: JSON parsing failed
Solution: Validate JSON structure and encoding
```

**Missing platform context**:
```
Warning: Platform descriptor not found, limited validation
Solution: Ensure platform descriptor artifact is available
```

**Upload permission denied**:
```
Error: 403 Forbidden from FAR
Solution: Check authentication tokens and permissions
```

## 📚 Related Documentation

- **[update-application.md](update-application.md)**: Module update workflow
- **[app-update.md](app-update.md)**: Orchestrator workflow
- **[FAR Documentation](https://wiki.folio.org/display/DD/FOLIO+Application+Registry)**: Registry details

---

**Last Updated**: September 2025  
**Workflow Version**: 1.0  
**Compatibility**: All FOLIO application repositories
