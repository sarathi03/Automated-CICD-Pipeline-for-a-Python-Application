pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout Verification') {
            steps {
                echo 'Jenkins has loaded the pipeline.'
                sh 'whoami'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Application Check') {
            steps {
                sh 'python3 --version || true'
                sh 'cat app.py'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t devops-cicd-demo:latest .'
            }
        }

        stage('Docker Image Verification') {
            steps {
                sh 'docker image inspect devops-cicd-demo:latest'
                sh 'docker image ls devops-cicd-demo:latest'
            }
        }

        stage('Push Image to Amazon ECR') {
            steps {
                sh '''
                    set -eu

                    AWS_REGION="ap-south-1"
                    AWS_ACCOUNT_ID="141553305146"
                    ECR_REPOSITORY="devops-cicd-demo"
                    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                    ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}"

                    /usr/local/bin/aws ecr get-login-password \
                        --region "$AWS_REGION" \
                    | docker login \
                        --username AWS \
                        --password-stdin "$ECR_REGISTRY"

                    docker tag devops-cicd-demo:latest "${ECR_IMAGE}:latest"
                    docker tag devops-cicd-demo:latest "${ECR_IMAGE}:${BUILD_NUMBER}"

                    docker push "${ECR_IMAGE}:latest"
                    docker push "${ECR_IMAGE}:${BUILD_NUMBER}"
                '''
            }
        }


        stage('Pipeline Success') {
            steps {
                echo 'Checkout, application check, Docker build, verification, and ECR push completed!'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
    }
}
