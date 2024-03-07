#!/bin/bash
file="shadowsocks-v1.18.1.x86_64-unknown-linux-musl.tar.xz"
# https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.18.1/shadowsocks-v1.18.1.x86_64-unknown-linux-musl.tar.xz
wget https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.18.1/${file}
tar -xvf ${file}

address="0.0.0.0:443"
./ssserver -s ${address} -m aes-256-gcm -k test123 --dns 8.8.8.8 --dns-cache-size 10000 --tcp-fast-open --tcp-no-delay --worker-threads 2 -d
address="[::]:443"
./ssserver -s ${address} -m aes-256-gcm -k test123 --dns 8.8.8.8 --dns-cache-size 10000 --tcp-fast-open --tcp-no-delay --worker-threads 2 -d
ps -aux | grep ssserver
