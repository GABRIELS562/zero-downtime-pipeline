# Zero-Downtime Pipeline Terraform Infrastructure

This directory contains Terraform configurations for deploying a cost-optimized, zero-downtime pipeline on AWS ECS with comprehensive monitoring and security features.

## Architecture Overview

### Core Components
- **ECS Fargate Cluster** with Spot instance support for cost optimization
- **Application Load Balancer** with SSL termination and WAF protection
- **CodePipeline** for automated CI/CD with GitHub integration
- **CloudWatch** monitoring with business impact metrics
- **Security** with least privilege IAM roles and security groups

### Applications
- **Finance Trading System** - High-frequency trading with sub-50ms latency requirements
- **Pharma Manufacturing** - FDA-compliant manufacturing control system

## Cost Optimization Features

### Infrastructure Optimization
- **Spot Instances**: Up to 70% cost savings with mixed instance types
- **Single NAT Gateway**: For non-production environments
- **VPC Endpoints**: Reduce NAT Gateway usage for AWS services
- **Intelligent Tiering**: S3 lifecycle policies for log storage
- **Scheduled Scaling**: Business hours-aware scaling

### Resource Optimization
- **Fargate Spot**: Cost-effective container execution
- **Build Caching**: Faster CI/CD with S3-based caching
- **Log Retention**: Environment-specific retention policies
- **Container Insights**: Production-only detailed monitoring

### Environment-Specific Settings
- **Development**: Minimal resources, Spot instances, short retention
- **Staging**: Balanced resources, some Spot instances
- **Production**: High availability, On-Demand instances, full monitoring

## Security Features

### Network Security
- **Security Groups**: Least privilege access rules
- **Network ACLs**: Additional subnet-level protection
- **VPC Endpoints**: Private connectivity to AWS services
- **WAF**: Application-level protection

### Compliance & Audit
- **AWS Security Hub**: Centralized security findings
- **GuardDuty**: Threat detection and monitoring
- **CloudTrail**: API activity logging
- **VPC Flow Logs**: Network traffic monitoring

### Data Protection
- **Encryption at Rest**: All storage encrypted
- **Encryption in Transit**: TLS for all communications
- **Secrets Management**: AWS Secrets Manager integration
- **Access Control**: IAM roles with least privilege

## Business Impact Monitoring

### Executive Dashboards
- Deployment success rates and MTTR
- Business impact scoring
- Cost optimization metrics
- Compliance status

### Application-Specific Metrics
- **Finance**: Revenue impact, trading volume, P&L tracking
- **Pharma**: Manufacturing efficiency, batch integrity, FDA compliance

### Operational Intelligence
- Error rate analysis
- Performance trending
- Deployment correlation
- Business hours compliance

## Quick Start

### Prerequisites
1. AWS CLI configured with appropriate permissions
2. Terraform >= 1.5 installed
3. GitHub personal access token stored in AWS Secrets Manager

### Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd zero-downtime-pipeline/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your specific values
vim terraform.tfvars

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the infrastructure
terraform apply
```

### Environment-Specific Deployment
```bash
# Development environment
terraform apply -var-file="environments/dev.tfvars"

# Staging environment
terraform apply -var-file="environments/staging.tfvars"

# Production environment
terraform apply -var-file="environments/production.tfvars"
```

## Configuration

### Required Variables
- `project_name`: Project identifier
- `environment`: Environment name (dev/staging/production)
- `github_repo`: GitHub repository for source code
- `github_token_secret`: AWS Secrets Manager secret name for GitHub token

### Cost Optimization Variables
- `enable_spot_instances`: Use Spot instances for cost savings
- `enable_cost_optimization`: Enable additional cost optimization features
- `schedule_based_scaling`: Enable business hours-based scaling

### Application Configuration
Configure CPU, memory, and scaling parameters for each application:
```hcl
finance_app_config = {
  cpu                = 1024
  memory             = 2048
  desired_count      = 3
  min_capacity       = 2
  max_capacity       = 10
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = true
}
```

## Monitoring and Alerting

### CloudWatch Dashboards
- Executive overview with business metrics
- Application-specific performance dashboards
- Cost optimization tracking

### Alerts and Notifications
- CPU and memory utilization
- Application error rates
- Business impact metrics
- Compliance violations

### Log Analysis
- Centralized logging with CloudWatch
- Log Insights queries for troubleshooting
- Business impact correlation

## CI/CD Pipeline

### Pipeline Features
- **GitHub Integration**: Automatic builds on code changes
- **Multi-Stage**: Source → Build → Deploy
- **Security Scanning**: Container image vulnerability scanning
- **Approval Gates**: Manual approval for production pharma deployments
- **Rollback**: Automated rollback on failure

### Build Optimization
- **Caching**: S3-based build artifact caching
- **Parallel Builds**: Separate pipelines for each application
- **Resource Scaling**: Environment-appropriate build resources

## Cost Management

### Cost Estimation
Use `terraform plan` to estimate infrastructure costs before deployment.

### Cost Monitoring
- CloudWatch billing alarms
- Resource tagging for cost allocation
- Environment-specific cost tracking

### Optimization Recommendations
1. **Use Spot Instances**: Enable for non-production workloads
2. **Schedule Scaling**: Configure business hours scaling
3. **Right-Size Resources**: Monitor and adjust CPU/memory allocation
4. **Log Retention**: Use appropriate retention periods
5. **Reserved Instances**: Consider for predictable production workloads

## Compliance and Audit

### FDA 21 CFR Part 11 Compliance (Pharma)
- Electronic records with digital signatures
- Audit trail integrity
- 7-year data retention
- Access control and user authentication

### SOX Compliance (Finance)
- Change control documentation
- Segregation of duties
- Audit logging and monitoring
- Data integrity controls

### Security Standards
- AWS Security Hub compliance
- CIS Benchmarks
- AWS Well-Architected Framework
- Industry best practices

## Troubleshooting

### Common Issues
1. **Build Failures**: Check CodeBuild logs and IAM permissions
2. **Service Startup**: Verify health check endpoints and security groups
3. **DNS Resolution**: Ensure Route53 hosted zone configuration
4. **SSL Issues**: Verify ACM certificate validation

### Monitoring Tools
- CloudWatch Logs for application logs
- X-Ray for distributed tracing
- CloudWatch Insights for log analysis
- AWS Config for compliance monitoring

### Support
- Check AWS Service Health Dashboard
- Review CloudWatch alarms and metrics
- Use CloudWatch Insights for log analysis
- Contact AWS Support for infrastructure issues

## Contributing

### Code Standards
- Follow Terraform best practices
- Use consistent naming conventions
- Include comprehensive documentation
- Test in development environment first

### Security Requirements
- Least privilege IAM policies
- Encrypt sensitive data
- Regular security reviews
- Compliance validation

## License

This project is licensed under the MIT License - see the LICENSE file for details.