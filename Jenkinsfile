pipeline {
    agent any

    stages {
        stage('Pull Code') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh 'pip3 install -r requirements.txt'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                sudo fuser -k 5000/tcp || true
                nohup python3 app.py > app.log 2>&1 &
                '''
            }
        }
    }
}