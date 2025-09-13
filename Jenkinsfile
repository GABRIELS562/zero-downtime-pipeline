pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                sh '''
                    ssh jaime@192.168.50.100 "cd /home/jaime/zero-downtime-pipeline && docker build -t localhost:5000/pharma-app:${BUILD_NUMBER} -f apps/pharma-manufacturing/Dockerfile.flask apps/pharma-manufacturing/ && docker push localhost:5000/pharma-app:${BUILD_NUMBER}"
                    ssh jaime@192.168.50.100 "cd /home/jaime/zero-downtime-pipeline && docker build -t localhost:5000/finance-app:${BUILD_NUMBER} -f apps/finance-trading/Dockerfile.flask apps/finance-trading/ && docker push localhost:5000/finance-app:${BUILD_NUMBER}"
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                sh '''
                    kubectl set image deployment/pharma-app pharma-app=localhost:5000/pharma-app:${BUILD_NUMBER} -n production || true
                    kubectl set image deployment/finance-app finance-app=localhost:5000/finance-app:${BUILD_NUMBER} -n production || true
                '''
            }
        }
    }
}
