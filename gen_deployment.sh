#!/bin/bash

CLUSTER_IP=`kubectl get nodes -o wide --selector='node-role.kubernetes.io/master' | grep -Eo "[0-9]{2}\.[0-9]{2}\.[0-9]{1}\.[0-9]{3}"`
MONITOR_PORT=9822
WORKER_COUNT=`expr $(kubectl get nodes --selector='!node-role.kubernetes.io/master' | wc -l) - 1`

cat > deployments/monitor-deployment.yml <<EOF
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

cat > deployments/spark-cpu-deployment.yml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
    name: cpu-test
    labels:
        app: spark-cpu-test
spec:
    replicas: $WORKER_COUNT
    selector:
        matchLabels:
            app: spark-cpu-test
    template:
        metadata:
            labels:
                app: spark-cpu-test
        spec:
            containers:
            - name: spark-cpu-test
              image: vpemfh7/spark-cpu-test:latest
              ports:
                - containerPort: 4040
            - name: spark-monitor
              image: vpemfh7/sys-monitor:latest
              args: ["spark_monitor", "$CLUSTER_IP", "$MONITOR_PORT"]
              ports:
              - containerPort: $MONITOR_PORT
EOF