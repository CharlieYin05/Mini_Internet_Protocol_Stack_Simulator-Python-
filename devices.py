from config import *
from protocol import Segment, Packet, Frame

# Helper functions to determine which network an IP address belongs to
def is_network_1(ip):
    return ip.startswith(NETWORK_1_PREFIX)

# In this project, we only have two networks, so if it's not in network 1, it must be in network 2.
def is_network_2(ip):
    return ip.startswith(NETWORK_2_PREFIX)

# Helper function to check if two IP addresses are in the same network
def same_network(ip1, ip2):
    return (is_network_1(ip1) and is_network_1(ip2)) or \
           (is_network_2(ip1) and is_network_2(ip2))

'''
Host:
Layer 4: Create DATA / ACK segment, do checksum、seq、ACK
Layer 3: Create IP packet, determine jump to next IP
Layer 2: Create Ethernet-like frame, check MAC, send/receive frame
'''
class Host:
    def __init__(self, name, ip, mac, mac_table, default_gateway_ip, connected_router_interface):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.mac_table = mac_table
        self.default_gateway_ip = default_gateway_ip
        self.connected_router_interface = connected_router_interface

        self.next_seq = 0
        self.expected_seq = 0
        self.last_ack_received = None   #If equal to the sent segment, then the segment is ACKed, otherwise resend
        self.learned_mac_table = {}     #Simulate the L2 learning process, the MAC addresses are fixed and known, so this is not used for forwarding decisions, just for printing the learned MAC addresses.

    def send_application_data(self, data_size, dst_ip, router):
        # e.g. A to B: data_size=1200, dst_ip=10.0.2.2, router=R1
        """
        Application Layer gives data to Layer 4.
        Layer 4 segments data if size > 500 bytes.
        """
        remaining = data_size

        while remaining > 0:
            current_size = min(MAX_SEGMENT_DATA, remaining)
            data = "X" * current_size

            print(f"{self.name}: Layer 4: Data received from Application Layer. Data size={current_size}")

            acked = False

            while not acked:
                segment = Segment(
                    src_port=SRC_PORT,
                    dst_port=DST_PORT,
                    seg_type=DATA,
                    seq=self.next_seq,
                    data=data
                )

                print(f"{self.name}: Layer 4: Checksum computed")
                print(f"{self.name}: Layer 4: Segment created by adding transport layer header (DATA, seq={self.next_seq}) (encapsulation)")

                self.last_ack_received = None

                self.send_segment_to_network(segment, dst_ip, router)

                if self.last_ack_received == self.next_seq:
                    acked = True
                    self.next_seq = 1 - self.next_seq
                else:
                    print(f"{self.name}: Layer 4: Segment retransmitted due to incorrect ACK")

            remaining -= current_size

    def send_segment_to_network(self, segment, dst_ip, router):
        """
        Layer 4 sends segment to Layer 3.
        Layer 3 creates IP-like packet.
        """
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")

        packet = Packet(
            src_ip=self.ip,
            dst_ip=dst_ip,
            ttl=TTL_DEFAULT,
            protocol=PROTOCOL_UDP,
            payload=segment
        )

        print(f"{self.name}: Layer 3: Segment received from Transport Layer: SRC_IP={self.ip}, DST_IP={dst_ip}, TTL={packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {dst_ip}")
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        if same_network(self.ip, dst_ip):
            next_hop_ip = dst_ip
        else:
            next_hop_ip = self.default_gateway_ip

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")
        print(f"{self.name}: Layer 3: Outgoing interface selected")
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        self.send_packet_to_datalink(packet, next_hop_ip, router)

    def send_packet_to_datalink(self, packet, next_hop_ip, router):
        """
        Layer 2 creates Ethernet-like frame.
        """
        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        dst_mac = self.mac_table[next_hop_ip]

        print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP ({next_hop_ip}) → {dst_mac}")

        frame = Frame(
            src_mac=self.mac,
            dst_mac=dst_mac,
            eth_type=ETH_TYPE_IPV4,
            payload=packet
        )

        print(f"{self.name}: Layer 2: Frame created: SRC_MAC={self.mac}, DST_MAC={dst_mac}")
        print(f"{self.name}: Layer 2: Frame sent")

        router.receive_frame(frame, self.connected_router_interface)

  
    def receive_frame(self, frame, router):
        """
        Host receives frame from router.
        Layer 2 receives frame, learns source MAC, and delivers packet to Layer 3.
        """
        print(f"{self.name}: Layer 2: Frame received")

        self.learned_mac_table[frame.src_mac] = True
        print(f"{self.name}: Layer 2: Source MAC learned: {frame.src_mac}")

        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")

        packet = frame.payload
        self.receive_packet(packet, router)

    def receive_packet(self, packet, router):
        """
        Layer 3 receives packet from Layer 2.
        Check if destination IP matches this host's IP, if yes, deliver the segment to Layer 4, otherwise drop the packet.
        """
        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        if packet.dst_ip == self.ip:
            print(f"{self.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.name}: Layer 3: Segment delivered to Transport Layer")

            segment = packet.payload
            self.receive_segment(segment, packet.src_ip, router)
        else:
            print(f"{self.name}: Layer 3: Packet dropped because destination IP does not match this host")


    def receive_segment(self, segment, src_ip, router):
        """
        Layer 4 receives segment from Layer 3.
        Check if the segment is valid by verifying the checksum, if not, discard the segment. If valid, check the segment type, if it's a DATA segment, check the sequence number, if it's the expected sequence number, deliver the data to the application layer and send an ACK segment back to the sender. If it's an ACK segment, check the sequence number and update the last ACK received.
        """
        print(f"{self.name}: Layer 4: Segment received from Network Layer")

        if not segment.is_valid():
            print(f"{self.name}: Layer 4: Segment discarded due to checksum error")
            return

        print(f"{self.name}: Layer 4: Checksum verified")

        if segment.type == DATA:
            if segment.seq == self.expected_seq:
                print(f"{self.name}: Layer 4: DATA segment delivered to Application Layer. Data size={len(segment.data)}")

                ack = Segment(
                    src_port=DST_PORT,
                    dst_port=SRC_PORT,
                    seg_type=ACK,
                    seq=segment.seq,
                    data=""
                )

                print(f"{self.name}: Layer 4: Segment created by adding transport layer header (ACK, seq={segment.seq})")

                self.expected_seq = 1 - self.expected_seq

                self.send_segment_to_network(ack, src_ip, router)

            else:
                print(f"{self.name}: Layer 4: Duplicate DATA segment received")
                print(f"{self.name}: Layer 4: Segment discarded due to duplicate sequence number")

        elif segment.type == ACK:
            print(f"{self.name}: Layer 4: ACK received: seq={segment.seq}")
            self.last_ack_received = segment.seq

'''
Recieve frame
↓
Extract IP packet
↓
Check distination IP
↓
TTL - 1
↓
Check which interface to forward to
↓
Re-encapsulation frame
↓
Forward frame to next host
'''
class Router:
    def __init__(self, name):
        self.name = name

        self.interfaces = {
            "if1": {
                "ip": R1_IF1_IP,
                "mac": R1_IF1_MAC,
                "mac_table": MAC_TABLE_R1_IF1   #Real world router would learn the MAC addresses dynamically: ARP request/reply. Check by "arp -a"
            },
            "if2": {
                "ip": R1_IF2_IP,
                "mac": R1_IF2_MAC,
                "mac_table": MAC_TABLE_R1_IF2
            }
        }
        self.links = {}
        self.learned_mac_table = {}
        '''
        Real world router would have at least two interface: WAN and LAN
        e.g.

        Check by "ip addr" command

        WAN interface (connected to ISP):
        12: eth0: <BROADCAST,MULTICAST,ALLMULTI,UP,LOWER_UP> mtu 1500 qdisc htb state UP group default qlen 1000
            link/ether 38:94:ed:6a:c3:aa brd ff:ff:ff:ff:ff:ff                  #MAC address of the WAN interface (can be the same as LAN NIC if it's a software bridge)
            inet 125.XXX.XXX.XX/21 brd 125.XXX.XXX.XXX scope global eth0        #Public IP address assigned by ISP
            valid_lft forever preferred_lft forever

        LAN Bridge interface (connected to local devices):
        24: br0: <BROADCAST,MULTICAST,ALLMULTI,UP,LOWER_UP> mtu 1500 qdisc htb state UP group default 
            link/ether 38:94:ed:6a:c3:aa brd ff:ff:ff:ff:ff:ff                  #MAC address of the LAN interface (can be the same as WAN interface if it's a software bridge)
            inet 192.168.XX.1/24 brd 192.168.XX.255 scope global br0            #Router's IP address on the LAN side, also the default gateway for local devices
            valid_lft forever preferred_lft forever
        '''     

    def connect(self, interface_name, host):
        # e.g. router.connect("if1", hostA)
        self.links[interface_name] = host

    def receive_frame(self, frame, incoming_interface):
        """
        Router receives frame on one interface, then extract the L3 packet and forward it to the interface towards the destination IP.
        """
        interface_label = "Interface 1" if incoming_interface == "if1" else "Interface 2"
        print(f"{self.name}: Layer 2: Frame received on {interface_label}")

        self.learned_mac_table[frame.src_mac] = incoming_interface
        print(f"{self.name}: Layer 2: Source MAC learned: {frame.src_mac} on {interface_label}")
        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")
        #-----------
        packet = frame.payload                              # Key point: extract frame，get IP address these info，handover to L3
        self.receive_packet(packet, incoming_interface)     # Key point: Router needs to know from which interface
        #-----------

    def receive_packet(self, packet, incoming_interface):
        """
        Router Layer 3 receives packet and forwards it.
        """
        print(f"{self.name}: Layer 3: Packet received from Data Link Layer: SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}")
        print(f"{self.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        # Key point: TTL - 1
        old_ttl = packet.ttl
        packet.ttl = packet.ttl - 1

        print(f"{self.name}: Layer 3: TTL decremented: {old_ttl} → {packet.ttl}")

        # Key point: check if TTL <= 0, if yes, drop the packet, otherwise continue to forward the packet
        if packet.ttl <= 0:
            print(f"{self.name}: Layer 3: Packet dropped due to TTL expiry")
            return

        print(f"{self.name}: Layer 3: Routing table lookup performed")

        # Key point: check the destination IP to determine which interface to forward. To interace if1 or if2
        if is_network_1(packet.dst_ip):
            outgoing_interface = "if1"
            next_hop_ip = packet.dst_ip

        elif is_network_2(packet.dst_ip):
            outgoing_interface = "if2"
            next_hop_ip = packet.dst_ip

        else:
            print(f"{self.name}: Layer 3: Packet dropped because no route was found")
            return

        interface_label = "Interface 1" if outgoing_interface == "if1" else "Interface 2"

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")
        print(f"{self.name}: Layer 3: Outgoing interface selected ({interface_label})")
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")

        # Key point: create a new frame for the next local link
        self.send_packet_to_datalink(packet, next_hop_ip, outgoing_interface)

        '''
        Real world router routing table lookup would be more complex, it would check the longest prefix match for the destination IP in the RT to determine the outgoing interface and next-hop IP. 
        
        Check by "ip route" command
        
        e.g.
        default via 125.XXX.XXX.1 dev eth0                                              # next-hop router: for all destination IPs that are not in the routing table, forward to the ISP router via eth0
        1.0.0.2 via 125.XXX.XXX.1 dev eth0  metric 1 
        1.1.1.2 via 125.XXX.XXX.1 dev eth0  metric 1 
        125.XXX.XXX.0/21 dev eth0  proto kernel  scope link  src 125.XXX.XXX.XX         # If the destination IP is in the 125.XXX.XXX.0/21 subnet, then forward to eth0 interface (upload)
        125.XXX.XXX.1 dev eth0  proto kernel  scope link 
        127.0.0.0/8 dev lo  scope link 
        192.168.XX.0/24 dev br0  proto kernel  scope link  src 192.168.XX.1             # If the destination IP is in the 192.168.XX.0/24 subnet, then forward to br0 interface (download or local delivery)
        '''

    def send_packet_to_datalink(self, packet, next_hop_ip, outgoing_interface):
        """
        Router Layer 2 creates a new frame for the next local link.
        """
        interface = self.interfaces[outgoing_interface]

        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        dst_mac = interface["mac_table"][next_hop_ip]       #Key point: The destination MAC address is determined by looking up the next-hop IP in the MAC table of the outgoing interface. Real world requires ARP to learn the MAC address for next-hop IP.
        src_mac = interface["mac"]                          #Key point: The source MAC address from current interace

        print(f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP ({next_hop_ip}) → {dst_mac}")

        frame = Frame(
            src_mac=src_mac,
            dst_mac=dst_mac,
            eth_type=ETH_TYPE_IPV4,
            payload=packet
        )

        print(f"{self.name}: Layer 2: Frame created: SRC_MAC={src_mac}, DST_MAC={dst_mac}")

        interface_label = "Interface 1" if outgoing_interface == "if1" else "Interface 2"
        print(f"{self.name}: Layer 2: Frame forwarded on {interface_label}")

        next_host = self.links[outgoing_interface]
        next_host.receive_frame(frame, self)