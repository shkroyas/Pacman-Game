data "aws_vpc" "default" {
  id = "vpc-0659de47ff54322ba"
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Use the exact AMI currently running on the instance
data "aws_ami" "app" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "image-id"
    values = ["ami-0b5358cc8c5df0b02"]
  }
}
