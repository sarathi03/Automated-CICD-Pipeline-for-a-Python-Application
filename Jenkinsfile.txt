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

        stage('Pipeline Success') {
            steps {
                echo 'GitHub checkout and pipeline execution completed!'
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
