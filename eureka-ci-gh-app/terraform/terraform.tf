terraform {
  backend "s3" {
    bucket       = "folio-terraform"
    region       = "us-east-1"
    key          = "eureka-ci-gh-app/terraform.tfstate"
    use_lockfile = true
  }
}