#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
plain='\033[0m'
installer="[${green} INSTALLER ${plain}]"

[[ $EUID -ne 0 ]] && echo -e "[${red} ERROR ${plain}] This script must be run as root" && exit 1

function install_docker {
    
    ## Set up the repository:
    ### Install packages to allow apt to use a repository over HTTPS
    echo -e "${installer} Installing packages"
    apt-get update && apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg2
    
    # Add Docker's official GPG key:
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    
    # Add the Docker apt repository:
    echo -e "${installer} Adding docker apt repository"
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable"
    
    # Install Docker CE
    echo -e "${installer} Installing Docker"
    apt-get update && apt-get install -y \
    containerd.io=1.2.13-2 \
    docker-ce=5:19.03.11~3-0~ubuntu-$(lsb_release -cs) \
    docker-ce-cli=5:19.03.11~3-0~ubuntu-$(lsb_release -cs)
    
    
    # Set up the Docker daemon
    echo -e "${installer} Setting up Docker daemon"
    cat > /etc/docker/daemon.json <<EOF
    {
    "exec-opts": ["native.cgroupdriver=systemd"],
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m"
    },
    "storage-driver": "overlay2"
    }
EOF
    
    mkdir -p /etc/systemd/system/docker.service.d
    
    # Restart Docker
    echo -e "${installer} Restarting docker"
    systemctl daemon-reload
    systemctl restart docker
    
    systemctl enable docker
}

function install_k8s {
    
    swapoff -a
    nano /etc/fstab
    
    echo -e "${installer} Installing Kubernetes"
    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
    sysctl --system
    
    sudo apt-get update && sudo apt-get install -y apt-transport-https curl
    echo -e "${installer} Adding GPG key"
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
    sudo apt-get update
    sudo apt-get install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl
    
}

function uninstall_docker() {
    echo -e "${installer} Uninstalling docker"
    sudo apt-get purge docker docker-engine docker.io containerd runc -y
    sudo apt-get autoremove -y
    sudo apt-get update
    rm -rf /opt/cni /opt/containerd
}

function uninstall_k8s() {
    echo -e "${installer} Uninstalling Kubernetes"
    sudo apt-get purge kube* -y
    sudo apt-get autoremove -y
    sudo apt-get update
}

function uninstall() {
    uninstall_docker
    uninstall_k8s
}

function install() {
    install_docker
    install_k8s
}

uninstall
install