#!/usr/bin/python3
import os
import re
from argparse import ArgumentParser

"""
自动配置wireguard服务
"""
# 服务端的通信网卡
SERVER_NET_NAME = "eth0"
LOCAL_ADDRESS = "10.0.8.x"
# 服务器端公网ip
SERVER_ENDPOINT = "xg.yumolab.cn"
WIREGUARD_CONFIG = "wgserver.conf"
DNS = "8.8.8.8"

# 生成密钥对
def gen_key_pair(name: str):
    if not os.path.exists("{name}-pub.key") and not os.path.exists(f"{name}-private.key"):
        cmd = f"wg genkey | tee {name}-private.key | wg pubkey > {name}-pub.key"
        os.system(cmd)
        
    pub = open(f"{name}-pub.key", "r").read()
    pri = open(f"{name}-private.key", "r").read()
    return pub, pri

def stripe_multiline(s: str):
    return "\n".join([l.strip() for l in s.split("\n") if len(l) > 0])

class GenConfig:
    def __init__(self,server_endpoint:str = SERVER_ENDPOINT,server_port: int = 51820,
        server_net: str = SERVER_NET_NAME,
        local_adress: str = LOCAL_ADDRESS) -> None:
        # self.server_public_key = open(f"{server_route_name}-pub.key", "r").read()
        # self.server_private_key = open(f"{server_route_name}-private.key", "r").read()
        server_route_name = "server"
        self.server_public_key, self.server_private_key = gen_key_pair(f"{server_route_name}")
        self.server_endpoint = server_endpoint
        self.server_port = server_port
        self.server_net = server_net
        self.server_route = server_route_name
        self.ip_address = local_adress

    def gen_server_interface(self):
        wiregurad_name = re.findall(r"^(.+).conf$", WIREGUARD_CONFIG)[0]
        ip_address = self.ip_address.replace("x", "1")
        net = self.server_net
        server_interface = f"""
            [Interface]
            PrivateKey = {self.server_private_key}
            Address = {ip_address}/24
            ListenPort = {self.server_port}
            PostUp = iptables -A FORWARD -i {wiregurad_name} -j ACCEPT; iptables -t nat -A POSTROUTING -o {net} -j MASQUERADE; ip6tables -A FORWARD -i {wiregurad_name} -j ACCEPT; ip6tables -t nat -A POSTROUTING -o {net} -j MASQUERADE
            PostDown = iptables -D FORWARD -i {wiregurad_name} -j ACCEPT; iptables -t nat -D POSTROUTING -o {net} -j MASQUERADE; ip6tables -D FORWARD -i {wiregurad_name} -j ACCEPT; ip6tables -t nat -D POSTROUTING -o {net} -j MASQUERADE
            """
        return stripe_multiline(server_interface)

    def gen_server_pair(self,index:int):
        """生成序号为index的客户端配置"""
        if index < 1:
            index = 1
        client_public_key, client_private_key = gen_key_pair(f"client{index}")
        ip_index = 1 + index
        ip = self.ip_address.replace("x", str(ip_index))
        server_peer = f"""
        [Peer]
        PublicKey = {client_public_key}
        AllowedIPs = {ip}/32
        """
        client_config = f"""
        [Interface]
        PrivateKey = {client_private_key}
        Address = {ip}/24
        DNS = {DNS}
        # MTU = 1420
        Table = off

        [Peer]
        PublicKey = {self.server_public_key}
        AllowedIPs = 0.0.0.0/0
        Endpoint = {self.server_endpoint}:{self.server_port}
        PersistentKeepalive = 25
        """
        return stripe_multiline(server_peer),stripe_multiline(client_config)
    def gen_client(self, index: int,name:str = "wg-client"):
        """生成序号为index的客户端配置"""
        if not os.path.exists(WIREGUARD_CONFIG):
            server_interface = self.gen_server_interface()
            with open(WIREGUARD_CONFIG, "w") as f:
                f.write(server_interface)
                f.write("\n")

        server_peer, client_config = self.gen_server_pair(index)
        with open(WIREGUARD_CONFIG, "a") as f:
            f.write(server_peer)
            f.write("\n")
        with open(f"{name}{index}.conf", "w") as f:
            f.write(client_config)

def run():
    ap = ArgumentParser()
    ap.add_argument("-i", "--index", type=int, default=1)
    ap.add_argument("-n", "--name", type=str, default="client")
    ap.add_argument("-e","--endpoint", type=str, default="xg.yumolab.cn", help="服务端地址")
    ap.add_argument("-p","--port", default=51820, type=int,help="服务端口")
    ap.add_argument("--net", type=str, default=SERVER_NET_NAME,help="服务的可以访问公网的网卡")
    ap.add_argument("--local",type=str,default=LOCAL_ADDRESS,help="局域网网段，默认: 10.0.8.x")
    args = ap.parse_args()
    GenConfig(server_endpoint=args.endpoint,server_port=args.port,server_net=args.net,local_adress=args.local).gen_client(args.index, args.name)
    print(f"生成{args.name}{args.index}号客户端配置")
    print(f"服务器是：{args.endpoint}")
    print("提示：请在服务端开启ipv4/ipv6内核转发,以及配置好防火墙")
    print("sudo sysctl -w net.ipv4.ip_forward=1")
    print("sudo sysctl -w net.ipv6.conf.all.forwarding=1")
    print("sudo sysctl -p")
    # 如果服务器配置了防火墙，需要打开端口
    print(f"ufw allow {args.port}/udp")

if __name__ == "__main__":
    run()
