pipeline {
    agent any
    
    stages {
        stage('Update K8s Manifests') {
            steps {
                echo 'Updating Kubernetes manifests for ArgoCD to sync...'
                sh '''
                    # ArgoCD will auto-sync from the k8s/ directory
                    echo "Manifests in k8s/ directory will be synced by ArgoCD"
                    ls -la k8s/ || echo "k8s directory not found"
                '''
            }
        }
        
        stage('Trigger ArgoCD Sync') {
            steps {
                echo 'ArgoCD auto-sync is enabled - no manual trigger needed'
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully - ArgoCD will sync changes'
        }
        failure {
            echo 'Pipeline failed - check logs'
        }
    }
}
