pipeline {
    agent any

    stages {
        stage('Checkout latest code') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/sperzuu-cyber/diary-app.git'
            }
        }

        stage('Deploy code to app folder') {
            steps {
                sh '''
                rsync -av --delete \
                --exclude 'venv' \
                --exclude 'diary.db' \
                --exclude 'static/uploads' \
                ./ /home/ubuntu/diary-app/
                '''
            }
        }

        stage('Restart app with systemd') {
            steps {
                sh '''
                sudo /bin/systemctl restart diary-app
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