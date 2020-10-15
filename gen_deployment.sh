#!/bin/bash

# Get kubernetes cluster ip from any node based on 6443 port
CLUSTER_IP=`kubectl get svc/collector -o jsonpath={'.spec.clusterIP'}`
MONITOR_PORT=9822
WORKER_COUNT=`kubectl get nodes | grep node | wc -l`

cat > deployments/sys-monitor-deployment.yml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
    name: monitor-dpl
    labels:
        app: sys-monitor
spec:
    replicas: $WORKER_COUNT
    selector:
        matchLabels:
            app: sys-monitor
    template:
        metadata:
            labels:
                app: sys-monitor
        spec:
            containers:
            - name: sys-monitor
              image: vpemfh7/sys-monitor:latest
              args: ["monitor", "$CLUSTER_IP", "$MONITOR_PORT"]
              ports:
              - containerPort: $MONITOR_PORT
EOF

cat deployments/spark-monitor-deployment.yml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
    name: monitor-dpl
    labels:
        app: spark-monitor
spec:
    replicas: $WORKER_COUNT
    selector:
        matchLabels:
            app: spark-monitor
    template:
        metadata:
            labels:
                app: spark-monitor
        spec:
            containers:
            - name: spark-monitor
              image: vpemfh7/spark-monitor:latest
              args: ["spark-monitor", "$CLUSTER_IP", "$MONITOR_PORT"]
              ports:
              - containerPort: $MONITOR_PORT
EOF