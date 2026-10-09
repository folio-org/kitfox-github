data "aws_ssm_parameter" "github_app_id" {
  count = var.github_app_id_ssm_parameter != "" ? 1 : 0
  name  = var.github_app_id_ssm_parameter
}

data "aws_ssm_parameter" "github_installation_id" {
  count = var.github_installation_id_ssm_parameter != "" ? 1 : 0
  name  = var.github_installation_id_ssm_parameter
}

locals {
  use_secrets_manager  = var.credentials_store == "secretsmanager"
  create_lambda_role   = var.lambda_execution_role_arn == ""
  create_apigw_cw_role = var.api_gateway_cloudwatch_role_arn == ""

  github_app_id          = var.github_app_id_ssm_parameter != "" ? data.aws_ssm_parameter.github_app_id[0].value : var.github_app_id
  github_installation_id = var.github_installation_id_ssm_parameter != "" ? data.aws_ssm_parameter.github_installation_id[0].value : var.github_installation_id

  lambda_role_arn   = local.create_lambda_role ? one(aws_iam_role.lambda_execution_role[*].arn) : var.lambda_execution_role_arn
  apigw_cw_role_arn = local.create_apigw_cw_role ? one(aws_iam_role.api_gateway_cloudwatch[*].arn) : var.api_gateway_cloudwatch_role_arn

  github_private_key = var.github_private_key != "" ? var.github_private_key : (var.github_private_key_path != "" ? file(var.github_private_key_path) : "")

  webhook_secret_ssm_parameter = coalesce(var.github_webhook_secret_ssm_parameter, "/${var.app_name}/webhook-secret")
  private_key_ssm_parameter    = coalesce(var.github_private_key_ssm_parameter, "/${var.app_name}/github-app-private-key")

  write_webhook_secret_ssm = !local.use_secrets_manager && nonsensitive(var.github_webhook_secret != "")
  write_private_key_ssm    = !local.use_secrets_manager && nonsensitive(local.github_private_key != "")

  ssm_parameter_arn_prefix         = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter"
  webhook_secret_ssm_parameter_arn = "${local.ssm_parameter_arn_prefix}/${trimprefix(local.webhook_secret_ssm_parameter, "/")}"
  private_key_ssm_parameter_arn    = "${local.ssm_parameter_arn_prefix}/${trimprefix(local.private_key_ssm_parameter, "/")}"
  credential_ssm_parameter_arns    = [local.webhook_secret_ssm_parameter_arn, local.private_key_ssm_parameter_arn]

  credential_env_webhook = local.use_secrets_manager ? tomap({
    WEBHOOK_SECRET_ARN     = one(aws_secretsmanager_secret.webhook_secret[*].arn)
    GITHUB_PRIVATE_KEY_ARN = one(aws_secretsmanager_secret.github_private_key[*].arn)
    }) : tomap({
    WEBHOOK_SECRET_SSM_PARAMETER = local.webhook_secret_ssm_parameter
  })

  credential_env_processor = local.use_secrets_manager ? tomap({
    GITHUB_PRIVATE_KEY_ARN = one(aws_secretsmanager_secret.github_private_key[*].arn)
    }) : tomap({
    GITHUB_PRIVATE_KEY_SSM_PARAMETER = local.private_key_ssm_parameter
  })
}
