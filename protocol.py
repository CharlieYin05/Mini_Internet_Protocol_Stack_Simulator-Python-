from config import *

class Segment:
    HEADER_SIZE = 10  # 2+2+2+2+1+1

    # L4 segment header fields
    def __init__(self, src_port, dst_port, seg_type, seq, data=""):
        self.src_port = src_port                        #Real world UDP header
        self.dst_port = dst_port                        #Real world UDP header
        self.type = seg_type                            #Project-specific header, define 0 is data segment, 1 is ACK segment
        self.seq = seq                                  #Project-specific header, define the seq number for data segments
        self.data = data                                #Application data
        self.length = self.HEADER_SIZE + len(data)      #Real world UDP header
        self.checksum = self.compute_checksum()         #Real world UDP header

    # L4 segment checksum
    def compute_checksum(self):
        total = self.src_port + self.dst_port + self.length + self.type + self.seq
        for character in self.data:
            total = total + ord(character)
        return total % 65536

    # L4 segment checksum verification
    def is_valid(self):
        return self.checksum == self.compute_checksum()
        # Left: The result of the Host A create a segment.
        # Right: The result of the Host B receive the segment and compute the checksum again.


class Packet:
    HEADER_SIZE = 12  # 4+4+1+1+2

    # L3 packet header fields
    def __init__(self, src_ip, dst_ip, ttl, protocol, payload):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ttl = ttl
        self.protocol = protocol
        self.payload = payload
        self.total_length = self.HEADER_SIZE + payload.length


class Frame:

    # L2 frame header fields
    HEADER_SIZE = 14  # 6+6+2

    def __init__(self, src_mac, dst_mac, eth_type, payload):
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.eth_type = eth_type
        self.payload = payload
        '''
        Real world internet has FCS (Frame Check Sequence) or CRC (Cyclic Redundancy Check) for error detection at Layer 2.
        '''
        self.fcs = None
        self.crc = None