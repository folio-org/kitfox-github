# prevent_destroy: run `terraform state rm` on a parameter before destroying the stack or before no longer passing
# its value; the parameter then stays in Parameter Store.

resource "aws_ssm_parameter" "webhook_secret" {
  count = local.write_webhook_secret_ssm ? 1 : 0

  name             = local.webhook_secret_ssm_parameter
  description      = "GitHub webhook secret for signature validation"
  type             = "SecureString"
  key_id           = var.ssm_kms_key_arn != "" ? var.ssm_kms_key_arn : null
  value_wo         = var.github_webhook_secret
  value_wo_version = parseint(substr(sha256(var.github_webhook_secret), 0, 12), 16)
  overwrite        = true

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ssm_parameter" "github_private_key" {
  count = local.write_private_key_ssm ? 1 : 0

  name             = local.private_key_ssm_parameter
  description      = "GitHub App private key for authentication"
  type             = "SecureString"
  key_id           = var.ssm_kms_key_arn != "" ? var.ssm_kms_key_arn : null
  value_wo         = local.github_private_key
  value_wo_version = parseint(substr(sha256(local.github_private_key), 0, 12), 16)
  overwrite        = true

  tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}

ephemeral "aws_ssm_parameter" "webhook_secret_existing" {
  count = !local.use_secrets_manager && !local.write_webhook_secret_ssm ? 1 : 0

  arn             = local.webhook_secret_ssm_parameter_arn
  with_decryption = false
}

ephemeral "aws_ssm_parameter" "github_private_key_existing" {
  count = !local.use_secrets_manager && !local.write_private_key_ssm ? 1 : 0

  arn             = local.private_key_ssm_parameter_arn
  with_decryption = false
}
