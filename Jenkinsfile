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

        stage('Pipeline Success') {
            steps {
                echo 'Checkout, application check, and Docker build completed!'
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
