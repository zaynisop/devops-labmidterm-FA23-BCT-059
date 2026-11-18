#!/bin/bash
# EC2 user data (Ubuntu 24.04): SSH key for setup + 2 GB swap so Jenkins, training and Docker fit on a micro instance
set -eux
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIcvhuXOeCwqiAUjUdAOF4JKeuv83mpbsJJk2Llnj3wR midterm-ec2' >> /home/ubuntu/.ssh/authorized_keys
chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
