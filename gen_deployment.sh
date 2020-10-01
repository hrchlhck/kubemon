#!/bin/bash

# Get kubernetes cluster ip from any node based on 6443 port
CLUSTER_IP=`netstat -tn 2>/dev/null | grep 6443 | head -n 1 | cut -d: -f2 | awk '{print $2}'`
MONITOR_PORT=9822
WORKER_COUNT=`expr $(kubectl get nodes -l node-role.kubernetes.io/worker=worker | wc -l) - 1`

cat > deployment.yml <<EOF
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