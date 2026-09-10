resource "aws_s3_bucket" "raw_data" {
    bucket = "supply-chain-analysis-raw-data"
    tags = {
        Name = "supply-chain-analysis-raw-data"
        Environment = "production"
    }
}