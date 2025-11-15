module "sagemaker" {
  source = "./sagemaker"
}

module "lambda" {
  source = "./lambda"
}

module "datalake" {
  source = "./datalake"
}

module "glue" {
  source             = "./glue"
  datalake_bucket    = module.datalake.datalake_bucket_name
  raw_prefix         = module.datalake.raw_prefix
  predictions_prefix = module.datalake.predictions_prefix
}

module "athena" {
  source = "./athena"
}
