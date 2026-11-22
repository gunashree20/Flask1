
pipeline {
    agent any

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
                echo 'GitHub source code downloaded!'
            }
        }

        stage('Verify Project Files') {
            steps {
                sh '''
                    test -f day2/app.py
                    test -f day2/requirements.txt
                    test -f day2/Dockerfile
                    test -f day2/templates/base.html
                    test -f day2/templates/index.html
                    test -f day2/templates/students.html
                    test -f day2/static/style.css
                '''

                echo 'All project files are available!'
            }
        }

        stage('Validate Flask Source') {
            steps {
                sh '''
                    grep -q "Flask" day2/app.py
                    grep -q "def dashboard" day2/app.py
                    grep -q "def add_student" day2/app.py
                    grep -q "def students_api" day2/app.py
                '''

                echo 'Flask source validation successful!'
            }
        }

        stage('Validate Docker Configuration') {
            steps {
                sh '''
                    grep -q "FROM python:3.11-slim" day2/Dockerfile
                    grep -q "EXPOSE 5000" day2/Dockerfile
                '''

                echo 'Docker configuration validation successful!'
            }
        }

        stage('Build Completed') {
            steps {
                echo 'MEVI Flask Management Portal validation completed!'
            }
        }
    }

    post {
        success {
            echo 'MEVI FLASK CI PIPELINE SUCCESS!'
        }

        failure {
            echo 'MEVI FLASK CI PIPELINE FAILED!'
        }
    }
}
