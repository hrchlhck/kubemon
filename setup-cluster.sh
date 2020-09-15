#!/bin/bash

red='\033[0;31m'
green='\033[0;32m'
plain='\033[0m'
installer="[${green} INSTALLER ${plain}]"
kbcfg="$HOME/.kube/config"

[[ $EUID -ne 0 ]] && echo -e "[${red} ERROR ${plain}] This script must be run as root" && exit 1

kubeadm reset
rm -rf $HOME/.kube

kubeadm init

mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "KUBECONFIG=${kbcfg}" >> $HOME/.bashrc

export KUEBCONFIG=kbcfg