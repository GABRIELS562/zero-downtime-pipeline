pipeline {
    agent any
    
    stages {
        stage('Deploy') {
            steps {
                sh '''
                    echo "Triggering deployment"
                    kubectl rollout restart deployment pharma-app finance-app frontend-dashboard -n production
                    kubectl rollout status deployment pharma-app -n production --timeout=60s || true
                '''
            }
        }
    }
}
