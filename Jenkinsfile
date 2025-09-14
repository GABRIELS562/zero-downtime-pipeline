pipeline {
    agent any
    
    environment {
        REGISTRY = 'localhost:5000'
    }
    
    stages {
        stage('Build Pharma App') {
            steps {
                sh '''
                    echo "Building Pharma app..."
                    cd apps/pharma-manufacturing
                    docker build -t ${REGISTRY}/pharma-app:${BUILD_NUMBER} -f Dockerfile.flask .
                    docker push ${REGISTRY}/pharma-app:${BUILD_NUMBER}
                '''
            }
        }
        
        stage('Build Finance App') {
            steps {
                sh '''
                    echo "Building Finance app..."
                    cd apps/finance-trading
                    docker build -t ${REGISTRY}/finance-app:${BUILD_NUMBER} -f Dockerfile.flask .
                    docker push ${REGISTRY}/finance-app:${BUILD_NUMBER}
                '''
            }
        }
        
        stage('Deploy Apps') {
            steps {
                sh '''
                    echo "Deploying to Kubernetes..."
                    kubectl set image deployment/pharma-app pharma-app=${REGISTRY}/pharma-app:${BUILD_NUMBER} -n production
                    kubectl set image deployment/finance-app finance-app=${REGISTRY}/finance-app:${BUILD_NUMBER} -n production
                    
                    kubectl rollout status deployment/pharma-app -n production
                    kubectl rollout status deployment/finance-app -n production
                '''
            }
        }
    }
}
