# Morpheus AWS Deployment

This Terraform configuration deploys the Morpheus application on AWS using:

- **ECS Fargate** for container orchestration
- **RDS PostgreSQL** for the database
- **ElastiCache Redis** for caching
- **Application Load Balancer** for traffic distribution

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (>= 1.0)
3. Docker image pushed to ECR or Docker Hub

## Deployment

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your values:
   - Set your Docker image URL
   - Set secure database password
   - Set OpenAI API key

3. Initialize and deploy:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Accessing the Application

After deployment, the application will be available at the load balancer URL shown in the outputs.

## Clean Up

To destroy all resources:
```bash
terraform destroy
```