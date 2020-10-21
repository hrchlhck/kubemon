#!/bin/bash

green='\033[0;32m'
plain='\033[0m'
generator="[${green} SYS-MONITOR ${plain}]"
DOCKER_COMPOSE=./deployments/docker-compose.yml
DOCKER_COMPOSE_BENCHMARK=./tests/cpu/benchmark/docker-compose.yml

# Updates collector docker-compose file
function update_dc() {
    sed -i "s/$1/$2/g" $DOCKER_COMPOSE
    echo -e "${generator} Updated from $1 to $2"
}

function stop() {
    echo -e "${generator} STOPPING PROGRAM"
    stop_containers
    stop_k8s_deploy
    stop_collector
    sed -i -E "s/(test[0-9]+)/test0/g" $DOCKER_COMPOSE
    echo -e "${generator} Bye :)"
    exit 0
}

function stop_k8s_deploy() {
    if [ -n "$(kubectl get all | grep -Eo '(cpu)|(monitor)')" ]; then
        echo -e "${generator} Removing existing deployments $deployment"
        kubectl delete all --all --force
    fi;
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

function start_k8s_deploy() {
  echo -e "${generator} Starting OS monitor"
  kubectl apply -f deployments/monitor-deployment.yml

  echo -e "${generator} Starting Spark monitor"
  kubectl apply -f deployments/spark-cpu-deployment.yml
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
  
  start_k8s_deploy
  
  sleep $1

  stop_k8s_deploy

  stop_collector
  
  merge $last
  
  update_dc $last "test1"
  
  sleep 1
  
  clear
}

function start() {
  echo -e "${generator} Starting benchmark"
  last="test0"
  for i in $(seq 1 24); do
    actual="test$i"
    
    update_dc $last $actual

    start_collector

    start_k8s_deploy
    
    start_containers $i
    
    sleep $1

    stop_containers 

    stop_k8s_deploy

    stop_collector

    merge $actual
    
    last=$actual
    
    sleep 1
    
    clear
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
sed -i -E "s/(test[0-9]+)/test0/g" $DOCKER_COMPOSE
