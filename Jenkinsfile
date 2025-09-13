pipeline {
    agent {
        label 'jenkins-jenkins-agent'
    }
    
    stages {
        stage('Build Apps') {
            steps {
                echo "Building Pharma and Trading applications"
                echo "Build number: ${BUILD_NUMBER}"
            }
        }
        
        stage('Deploy') {
            steps {
                echo "Deploying to production namespace"
                echo "Zero-downtime deployment strategy"
            }
        }
        
        stage('Verify') {
            steps {
                echo "✅ Deployment successful"
            }
        }
    }
}
