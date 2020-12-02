#!/bin/bash

CLUSTER_IP=`kubectl get nodes -o wide --selector='node-role.kubernetes.io/master' | grep -Eo "[0-9]{2}\.[0-9]{2}\.[0-9]{1}\.[0-9]{3}"`
MONITOR_PORT=9822
WORKER_COUNT=`expr $(kubectl get nodes | wc -l) - 1`
MASTER_NAME=`kubectl get nodes --selector='node-role.kubernetes.io/master' -o jsonpath='{..name}'`

echo $MASTER_NAME

cat > deployments/monitor-deployment.yml <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
    name: monitor-dpl
    labels:
        app: sys-monitor
spec:
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

cat > deployments/spark-worker.yml <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: spark-worker
  labels:
    app: spark-worker
spec:
  selector:
    matchLabels:
      name: spark-worker
  template:
    metadata:
      labels:
        name: spark-worker
    spec:
      containers:
      - name: spark-worker
        image: vpemfh7/spark-worker:latest
        ports:
        - containerPort: 8081
      - name: spark-monitor
        image: vpemfh7/sys-monitor:latest
        args: ["spark_monitor", "$CLUSTER_IP", "$MONITOR_PORT"]
        ports:
        - containerPort: $MONITOR_PORT
EOF

cat > deployments/benchmark.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: benchmark 
  labels:
    app: benchmark
spec:
  replicas: $1
  selector:
    matchLabels:
      name: benchmark
  template:
    metadata:
      labels:
        name: benchmark
    spec:
      containers:
      - name: benchmark
        image: vpemfh7/cpu-stress:latest
EOF

cat > deployments/spark-master.yml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: spark-master
spec:
  selector:
    app: spark-master
  ports:
  - name: web-ui
    protocol: TCP
    port: 8080
    targetPort: 8080
  - name: master
    protocol: TCP
    port: 7077
    targetPort: 7077
  - name: master-rest
    protocol: TCP
    port: 6066
    targetPort: 6066
  - name: rest-master
    protocol: TCP
    port: 4040
    targetPort: 4040
  clusterIP: None
---
apiVersion: v1
kind: Service
metadata:
  name: spark-client
spec:
  selector:
    app: spark-client
  clusterIP: None
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-master
  labels:
    app: spark-master
spec:
  selector:
    matchLabels:
      app: spark-master
  template:
    metadata:
      labels:
        app: spark-master
    spec:
      containers:
      - name: spark-master
        image: vpemfh7/spark-master:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        - containerPort: 7077
        - containerPort: 6066
        - containerPort: 4040
      nodeName: $MASTER_NAME

EOF
