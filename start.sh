#!/bin/bash

green='\033[0;32m'
plain='\033[0m'
generator="[${green} SYS-MONITOR ${plain}]"
DOCKER_COMPOSE=./deployments/docker-compose.yml
DOCKER_COMPOSE_BENCHMARK=./tests/cpu/benchmark/docker-compose.yml
MASTER=./deployments/spark-master.yml
WORKER=./deployments/spark-worker.yml
OS_MONITOR=./deployments/monitor-deployment.yml

rm -rf data/

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
   kubectl delete -f $OS_MONITOR --force
   kubectl delete all --all --force
   sleep 30
}

# Starts spark cluster on kubernetes and submit a spark job
function start_spark_cluster() {    
    echo -e "${generator} Starting Spark cluster on Kubernetes"
    kubectl apply -f $MASTER
    
    sleep 5
    
    kubectl apply -f $WORKER
    
    echo -e "${generator} Waiting for the cluster to be ready"
    sleep 10 # 
   
    echo -e "${generator} Starting Spark jobs"
    POD_MASTER=$(kubectl get pods --field-selector status.phase=Running | grep -Eo "(spark-master\S*)")
    kubectl exec $POD_MASTER -c spark-master -- /bin/bash ./start.sh 2>/dev/null &
    
    sleep 1
    
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
  docker-compose -f $DOCKER_COMPOSE_BENCHMARK up -d --scale benchmark=$1
  ssh root@10.32.1.128 "docker-compose -f /opt/docker-compose.yml up -d --scale benchmark=$1"
  ssh root@10.32.1.138 "docker-compose -f /opt/docker-compose.yml up -d --scale benchmark=$1"
}

function stop_containers() {
  echo -e "${generator} STOPPING $1 CONTAINERS"
  docker-compose -f $DOCKER_COMPOSE_BENCHMARK down -t 0
  ssh root@10.32.1.128 "docker-compose -f /opt/docker-compose.yml down -t 0"
  ssh root@10.32.1.138 "docker-compose -f /opt/docker-compose.yml down -t 0"
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
  SPARK_MONITOR_CSV=$(ls data/$1 | grep spark_monitor)
  for file in $(ls data/$1 | grep -Eo "_[0-9].*" | sort -u); do
    echo -e "${generator} Merging sys_monitor$file with spark_monitor$file"
    python3 ./merge.py "./data/$1/sys_monitor$file" "./data/$1/$SPARK_MONITOR_CSV"
  done
}

function copy_files() {
  echo -e "${generator} Copying tests/cpu/benchmark/docker-compose.yml to node1 and node2"
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.128:/opt/
  scp $DOCKER_COMPOSE_BENCHMARK root@10.32.1.138:/opt/
}

function start_single() { 
  last="test00"
  
  start_collector
  
  start_spark_cluster
  
  sleep $1

  stop_spark_cluster

  stop_collector
  
  merge $last
  
  update_dc $last "test01"
    
  sleep 1
  
  clear
  
  ./test-csv.sh
}

function start() {
  echo -e "${generator} Starting benchmark"
  last="test00"
  for i in {01..24}; do
    actual="test$i"
    
    update_dc $last $actual

    start_collector
    
    start_spark_cluster
    
    start_containers $i
    
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
}

clear
echo -e "${generator} Generating deployments..."
sh setup-scripts/gen_deployment.sh
sleep 1
echo -e "${generator} Interval of $1 seconds..."
sleep 1
trap stop INT
copy_files
start_single $1
start $1
reset_dockercompose
