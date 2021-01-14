#!/bin/bash

### Resets cluster and some garbage
sudo kubeadm reset <<< y # Accept reset
sudo rm -rf $HOME/.kube
sudo rm -rf /etc/cni/net.d

### Initiate Kubernetes master
sudo kubeadm init --pod-network-cidr=10.0.1.0/24 

### Allows to execute kubectl as a regular user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

### Saves the config to bashrc and reload it
if [[ ! $(grep -R "KUBECONFIG" $HOME/.bashrc) ]]; then
    echo "KUBECONFIG=${HOME}/.kube/config" >> $HOME/.bashrc
    . $HOME/.bashrc
fi

### Apply Weave Net CNI
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')&env.IPALLOC_RANGE=10.0.1.0/24"

### Untaint master node 
# kubectl taint nodes $(hostname) node-role.kubernetes.io/master-
