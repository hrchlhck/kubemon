#!/bin/bash

green='\033[0;32m'
plain='\033[0m'
generator="[${green} SYS-MONITOR ${plain}]"
DOCKER_COMPOSE=./deployments/docker-compose.yml
BENCHMARK=./deployments/benchmark.yaml
MASTER=./deployments/spark-master.yml
WORKER=./deployments/spark-worker.yml
OS_MONITOR=./deployments/monitor-deployment.yml

function reset_dockercompose() {
    sed -i -E "s/(test[0-9]+)/test00/g" $DOCKER_COMPOSE
}

# Updates collector docker-compose file
function update_dc() {
    sed -i "s/$1/$2/g" $DOCKER_COMPOSE
    echo -e "${generator} Updated from $1 to $2"
}

function stop_spark_cluster() {
   echo -e "${generator} Stopping all deployments"
	kubectl delete all --all
}

# Starts spark cluster on kubernetes and submit a spark job
function start_spark_cluster() {    
    echo -e "${generator} Starting Spark cluster on Kubernetes"
    kubectl apply -f $MASTER

    sleep 5

    POD=$(kubectl get pods | grep -Eo "(spark-master\S*)")

    while [[ $(kubectl get pods $POD -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True"  ]]; do
	echo wait for master
	sleep 5	
    done
    
    kubectl apply -f $WORKER
    
    echo -e "${generator} Waiting for the cluster to be ready"
  
    for worker in $(kubectl get pods | grep -Eo "(spark-worker\S*)"); do
        while [[ $(kubectl get pods $worker -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True"  ]]; do
	    echo -e "${generator} Waiting for worker $worker"
	    sleep 1	
        done
    done
    
    sleep 5
}

function stop() {
    echo -e "${generator} STOPPING PROGRAM"
    stop_containers
    stop_spark_cluster
    stop_collector
    reset_dockercompose
    echo -e "${generator} Bye :)"
    exit 0
}

function start_containers() {
  echo -e "${generator} STARTING $1 CONTAINERS"
  kubectl apply -f $BENCHMARK
}

function stop_containers() {
  echo -e "${generator} STOPPING $1 CONTAINERS"
  kubectl delete -f $BENCHMARK
}

function copy_files() {
  echo -e "${generator} Copying tests/cpu/benchmark/docker-compose.yml to node1 and node2"
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.128:/opt/
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.138:/opt/
}

function start() {
  echo -e "${generator} Starting test time"
  last="test00"
  for i in $(seq 0 20); do
    echo -e "${generator} Generating deployments..."
    sh setup-scripts/gen_deployment.sh $(($i * 3))
    actual="test$i"
  
    start_spark_cluster

    POD_MASTER=$(kubectl get pods | grep -Eo "(spark-master\S*)")

    update_dc $last $actual

    if [[ ! -d "time-data" ]]; then
       mkdir "time-data"
    fi
    
    start_containers $i
    
    sleep 10s

    echo -e "${generator} Starting PySpark job"

    START=$SECONDS
    kubectl exec -it $POD_MASTER -- /bin/bash ./start.sh &>/dev/null
    DURATION=$SECONDS
   
    echo $actual, $((DURATION - START)) >> time-data/test-wordcount.csv

    stop_containers 
    
    stop_spark_cluster
    
    last=$actual
	
    sleep 5
    
    clear
    
    done
  
  echo -e "${generator} DONE!"

  reset_dockercompose
}

clear
kubectl delete all --all
sleep 1
trap stop INT
# copy_files
start
