pipeline {
    agent any

    stages {
        stage('Checkout latest code') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/sperzuu-cyber/diary-app.git'
            }
        }

        stage('Install requirements') {
            steps {
                sh '''
                /home/ubuntu/diary-app/venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Deploy with systemd') {
            steps {
                sh '''
                sudo systemctl restart diary-app
                '''
            }
        }

        stage('Check app is running') {
            steps {
                sh '''
                sleep 3
                curl -f http://localhost:5000
                '''
            }
        }
    }
}