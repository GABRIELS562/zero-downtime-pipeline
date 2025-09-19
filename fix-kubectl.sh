#!/bin/bash
# Fix kubectl for Jenkins
docker exec jenkins-standalone sh -c "
    sed -i 's|server: https://127.0.0.1:6443|server: https://192.168.50.100:6443|g' /var/jenkins_home/.kube/config
    kubectl get nodes
"
