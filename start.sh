#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
plain='\033[0m'
generator="[${green} SYS-MONITOR ${plain}]"

echo -e "${generator} Generating deployments..."

sh gen_deployment.sh

sleep 1

cd deployments/

if [ -n "$(kubectl get all | grep -Eo '(cpu)|(monitor)')" ]; then
    echo -e "${generator} Removing existing deployments $deployment"
    kubectl delete all --all --force
fi;

for deployment in $(ls); do
    if [ $deployment = "docker-compose.yml" ]; then
        if [ -n "$(docker-compose ps | grep collector)" ]; then
            echo -e "${generator} Restarting collector"
            docker-compose down -t 0
        fi; 

        echo -e "${generator} Starting collector"
        docker-compose up -d
    else
        echo -e "${generator} Starting $deployment"
        kubectl apply -f "$deployment"
    fi;
done