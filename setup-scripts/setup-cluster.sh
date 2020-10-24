#!/bin/bash

CLUSTER_IP=`ip route get 1 | awk {'print $7;exit'}`
kbcfg="$HOME/.kube/config"

kubeadm reset
rm -rf $HOME/.kube
rm -rf /etc/cni/net.d

kubeadm init --pod-network-cidr=10.244.0.0/24 

mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "KUBECONFIG=${kbcfg}" >> $HOME/.bashrc

export KUEBCONFIG=kbcfg

kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')&env.IPALLOC_RANGE=10.244.0.0/24"

kubectl taint nodes $(hostname) node-role.kubernetes.io/master-
