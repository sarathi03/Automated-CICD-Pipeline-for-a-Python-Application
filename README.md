# Project 1 – Automated CI/CD Pipeline

## Project Overview

This project demonstrates an end-to-end CI/CD workflow for a single Python web application. The goal is to automate the process of retrieving application code from GitHub, building a Docker image, publishing it to Amazon Elastic Container Registry (ECR), and deploying the application through Jenkins.

GitHub Webhooks are used to trigger the pipeline automatically when changes are pushed to the repository, reducing the need for manual builds and deployments.

## Technologies Used

- **Python** – Developed a lightweight web application with a health-check endpoint.
- **Git & GitHub** – Source code management and version control.
- **GitHub Webhooks** – Automatically trigger Jenkins builds when code changes are pushed.
- **Jenkins** – Automates the CI/CD pipeline.
- **Docker** – Packages the application into a container image.
- **Amazon ECR** – Stores and manages Docker images privately.
- **Amazon EC2** – Hosts Jenkins and runs the deployed application.
- **AWS IAM** – Provides permissions for Jenkins to interact with AWS services.
- **Linux & Bash** – Used for server administration and pipeline commands.

## Key Features

- Automated pipeline execution through GitHub Webhooks.
- Docker image building and verification.
- Automated image publishing to Amazon ECR.
- Container deployment on an EC2 instance.
- Application health-check verification after deployment.
- Pipeline success and failure reporting.

## What I Learned

This project provided hands-on experience with CI/CD automation, containerization, AWS container image management, IAM permissions, webhook integration, Linux server administration, and deployment troubleshooting.

It also helped me understand how source code changes can move through a pipeline and become a running application with minimal manual intervention.

## Detailed Documentation

For the complete implementation steps, commands, configuration details, troubleshooting notes, and project walkthrough, refer to [`Complete CICD - 1.md`](./Complete%20CICD%20-%201.md).
