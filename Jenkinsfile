pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5000'
    }
    
    stages {
        stage('Build Pharma App') {
            steps {
                sh """
                    echo "Building Pharma app..."
                    cd apps/pharma-manufacturing
                    docker build -t ${DOCKER_REGISTRY}/pharma-app:${BUILD_NUMBER} -f Dockerfile.flask .
                    docker push ${DOCKER_REGISTRY}/pharma-app:${BUILD_NUMBER}
                """
            }
        }
        
        stage('Build Finance App') {
            steps {
                sh """
                    echo "Building Finance app..."
                    cd apps/finance-trading
                    docker build -t ${DOCKER_REGISTRY}/finance-app:${BUILD_NUMBER} -f Dockerfile.flask .
                    docker push ${DOCKER_REGISTRY}/finance-app:${BUILD_NUMBER}
                """
            }
        }
        
        stage('Deploy Apps') {
            steps {
                sh """
                    echo "Deploying to Kubernetes..."
                    # Direct deployment (keeping what works)
                    kubectl set image deployment/pharma-app pharma-app=${DOCKER_REGISTRY}/pharma-app:${BUILD_NUMBER} -n production
                    kubectl set image deployment/finance-app finance-app=${DOCKER_REGISTRY}/finance-app:${BUILD_NUMBER} -n production
                    kubectl rollout status deployment/pharma-app -n production
                    kubectl rollout status deployment/finance-app -n production
                """
            }
        }
        
        stage('Update Manifests for ArgoCD') {
            steps {
                sh """
                    echo "Updating k8s manifests for ArgoCD tracking..."
                    # Update the deployment.yaml with new image tags
                    if [ -f k8s/deployment.yaml ]; then
                        sed -i "s|image: ${DOCKER_REGISTRY}/pharma-app:.*|image: ${DOCKER_REGISTRY}/pharma-app:${BUILD_NUMBER}|g" k8s/deployment.yaml
                        sed -i "s|image: ${DOCKER_REGISTRY}/finance-app:.*|image: ${DOCKER_REGISTRY}/finance-app:${BUILD_NUMBER}|g" k8s/deployment.yaml
                        
                        git config user.name "Jenkins CI" || true
                        git config user.email "jenkins@jagdevops.co.za" || true
                        git add k8s/deployment.yaml || true
                        git commit -m "Update images to build ${BUILD_NUMBER}" || true
                        echo "Manifest updated (git push disabled for safety)"
                    else
                        echo "No k8s/deployment.yaml found - ArgoCD sync skipped"
                    fi
                """
            }
        }
    }
    
    post {
        success {
            echo "✅ Zero-Downtime Pipeline succeeded! Pharma and Finance apps deployed."
        }
    }
}
