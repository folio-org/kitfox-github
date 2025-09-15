terraform {
  backend "s3" {
    bucket       = "folio-terraform"
    region       = "us-east-1"
    key          = "gh-app-webhook-listener/terraform.tfstate"
    use_lockfile = true
  }
}