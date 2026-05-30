# Two hosts: Host A and Host B
HOST_A_IP = "10.0.1.10"
HOST_B_IP = "10.0.2.20"

# Router R1 has two interfaces: IF1 and IF2
R1_IF1_IP = "10.0.1.1"
R1_IF2_IP = "10.0.2.1"

# 4 NIC with MAC addresses
HOST_A_MAC = "AA:AA:AA:AA:AA:AA"
R1_IF1_MAC = "BB:BB:BB:BB:BB:BB"
R1_IF2_MAC = "CC:CC:CC:CC:CC:CC"
HOST_B_MAC = "DD:DD:DD:DD:DD:DD"

NETWORK_1_PREFIX = "10.0.1."
NETWORK_2_PREFIX = "10.0.2."

TTL_DEFAULT = 100           # L3: Time to live for packets: 100 hops
MAX_SEGMENT_DATA = 500      # L4: maximum application data per segment = 500 bytes

ETH_TYPE_IPV4 = 0x0800      # L2: 0x0800 is IPv4, 0x0806 is ARP, 0x86DD is IPv6, 0x8100 is VLAN
PROTOCOL_UDP = 17           # L3: 17 is UDP, 1 is ICMP, 6 is TCP   

DATA = 0                    # L4: define 0 is data segment
ACK = 1                     # L4: define 1 is ACK segment        

SRC_PORT = 5000             # L4: source port for UDP segments, can be any value between 1024 and 65535
DST_PORT = 80               # L4: destination port for UDP segments, can be any value between 1024 and 65535

# IP → MAC, but project does not require ARP, so I can hardcode the MAC addresses for the IP addresses in this project
MAC_TABLE_A = {
    R1_IF1_IP: R1_IF1_MAC
}

MAC_TABLE_B = {
    R1_IF2_IP: R1_IF2_MAC
}

MAC_TABLE_R1_IF1 = {
    HOST_A_IP: HOST_A_MAC
}

MAC_TABLE_R1_IF2 = {
    HOST_B_IP: HOST_B_MAC
}