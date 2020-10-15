#!/bin/bash

sh gen_deployment.sh

sleep 1

for deployment in $(ls deployments/) do
    kubectl apply -f "deployment/$deployment"
done