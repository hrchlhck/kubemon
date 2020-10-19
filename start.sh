#!/bin/bash

green='\033[0;32m'
plain='\033[0m'
generator="[${green} SYS-MONITOR ${plain}]"

echo -e "${generator} Generating deployments..."

sh setup-scripts/gen_deployment.sh

sleep 1

cd deployments/

if [ -n "$(kubectl get all | grep -Eo '(cpu)|(monitor)')" ]; then
    echo -e "${generator} Removing existing deployments $deployment"
    kubectl delete all --all --force
fi;

if [ -n "$(docker-compose ps | grep collector)" ]; then
    echo -e "${generator} Restarting collector"
    docker-compose down -t 0
fi; 

echo -e "${generator} Starting collector"
docker-compose up -d

echo -e "${generator} Copying tests/cpu/benchmark/docker-compose.yml to node1 and node2"
scp ../tests/cpu/benchmark/docker-compose.yml root@10.32.1.128:/opt/
scp ../tests/cpu/benchmark/docker-compose.yml root@10.32.1.138:/opt/

echo -e "${generator} Starting benchmark"
for i in $(seq 1 24); do
  echo -e "${generator} Starting OS monitor"
  kubectl apply -f monitor-deployment.yml

  echo -e "${generator} Starting Spark monitor"
  kubectl apply -f spark-cpu-deployment.yml

  echo -e "${generator} STARTING $i CONTAINERS"
  docker-compose -f ../tests/cpu/benchmark/docker-compose.yml up -d --scale benchmark=$i
  ssh root@10.32.1.128 "docker-compose -f /opt/docker-compose.yml up -d --scale benchmark=$i"
  ssh root@10.32.1.138 "docker-compose -f /opt/docker-compose.yml up -d --scale benchmark=$i"
  
  sleep 600 # sleeps for 10 minutes

  echo -e "${generator} STOPPING $i CONTAINERS"
  docker-compose -f ../tests/cpu/benchmark/docker-compose.yml down -t 0
  ssh root@10.32.1.128 "docker-compose -f /opt/docker-compose.yml down -t 0"
  ssh root@10.32.1.138 "docker-compose -f /opt/docker-compose.yml down -t 0"

  kubectl delete all --all --force
done

echo -e "${generator} DONE!"