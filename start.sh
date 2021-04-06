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
    sed -i -E "s/(test[0-9]+)/test0/g" $DOCKER_COMPOSE
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

    sleep 3    

    POD_MASTER=$(kubectl get pods | grep -Eo "(spark-master\S*)")

    while [[ $(kubectl get pods $POD_MASTER -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True"  ]]; do
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

    sleep 10 

    echo -e "${generator} Starting Spark jobs"
    kubectl exec $POD_MASTER -c spark-master -- /bin/bash ./start.sh &>/dev/null & 

    sleep 5
     
    echo -e "${generator} Starting OS monitor"
    kubectl apply -f $OS_MONITOR
   
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

function stop_collector() {
    echo -e "${generator} Stopping collector"
    docker-compose -f $DOCKER_COMPOSE down -t 0
}

function start_collector() {
  echo -e "${generator} Starting collector"
  docker-compose -f $DOCKER_COMPOSE up -d
}

function merge() {
  # SPARK_MONITOR_CSV=$(ls data/$1 | grep spark_monitor)
  for file in $(ls data/$1 | grep -Eo "_[0-9].*" | sort -u); do
    echo -e "${generator} Merging sys_monitor$file with spark_monitor$file"
    python3 ./merge.py "./data/$1/sys_monitor$file" "./data/$1/spark_monitor$file"
  done
}

function copy_files() {
  echo -e "${generator} Copying tests/cpu/benchmark/docker-compose.yml to node1 and node2"
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.128:/opt/
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.138:/opt/
}

function start_single() { 
  last="test0"
  
  start_collector
  
  start_spark_cluster
  
  sleep $1

  stop_spark_cluster

  stop_collector
  
  merge $last
  
  update_dc $last "test1"
    
  sleep 1
  
  clear
  
  ./test-csv.sh
}

function start() {
  echo -e "${generator} Starting benchmark"
  last="test0"
  for i in {1..20}; do
    actual="test$i"
   
    echo -e "${generator} Generating deployments..."
    sh setup-scripts/gen_deployment.sh $(($i * 3))

    update_dc $last $actual

    start_collector
    
    start_containers $i

    start_spark_cluster
        
    sleep $1

    stop_containers 

    stop_spark_cluster

    stop_collector

    merge $actual
    
    last=$actual
    
    sleep 1
    
    clear
    
    ./test-csv.sh
  done
  echo -e "${generator} DONE!"
  echo $(date)
}

reset_dockercompose
sleep 1
echo -e "${generator} Interval of $1 seconds..."
sleep 1
trap stop INT
echo -e "${generator} Generating deployments..."
sh setup-scripts/gen_deployment.sh 0
start_single $1
start $1
reset_dockercompose
