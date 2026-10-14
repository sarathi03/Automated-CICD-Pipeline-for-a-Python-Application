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

        stage('Deploy Application') {
            steps {
                sh '''
                    set -eu

                    APP_NAME="devops-cicd-app"
                    AWS_REGION="ap-south-1"
                    AWS_ACCOUNT_ID="141553305146"
                    ECR_REPOSITORY="devops-cicd-demo"
                    ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

                    echo "Pulling the latest image from ECR..."
                    docker pull "${ECR_IMAGE}:latest"

                    echo "Saving the current image for rollback..."
                    OLD_IMAGE_ID=$(docker inspect --format='{{.Image}}' "$APP_NAME" 2>/dev/null || true)

                    echo "Removing the old container..."
                    docker rm -f "$APP_NAME" || true

                    echo "Starting the new application container..."
                    if ! docker run -d \
                        --name "$APP_NAME" \
                        --restart unless-stopped \
                        -p 5000:5000 \
                        "${ECR_IMAGE}:latest"; then

                        echo "New container failed to start. Rolling back..."
                        if [ -n "$OLD_IMAGE_ID" ]; then
                            docker run -d \
                                --name "$APP_NAME" \
                                --restart unless-stopped \
                                -p 5000:5000 \
                                "$OLD_IMAGE_ID"
                        fi
                        exit 1
                    fi

                    echo "Waiting for the application health check..."
                    HEALTHY=false

                    for attempt in 1 2 3 4 5 6 7 8 9 10; do
                        if curl -fsS http://localhost:5000/health; then
                            HEALTHY=true
                            break
                        fi
                        echo "Health check attempt $attempt failed; retrying..."
                        sleep 3
                    done

                    if [ "$HEALTHY" != "true" ]; then
                        echo "Health check failed. Rolling back..."
                        docker logs "$APP_NAME" || true
                        docker rm -f "$APP_NAME" || true

                        if [ -n "$OLD_IMAGE_ID" ]; then
                            docker run -d \
                                --name "$APP_NAME" \
                                --restart unless-stopped \
                                -p 5000:5000 \
                                "$OLD_IMAGE_ID"
                        fi

                        exit 1
                    fi

                    echo "Deployment successful!"
                '''
            }
        }

        stage('Pipeline Success') {
            steps {
                echo 'Checkout, build, image verification, ECR push, and deployment completed!'
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
