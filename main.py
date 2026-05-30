import sys

from config import *
from devices import Host, Router


def main():
    # Check command-line argument
    if len(sys.argv) != 2:
        print("Usage: python main.py <message_size_in_bytes>")
        print("Example: python main.py 100")
        return

    try:
        message_size = int(sys.argv[1])
    except ValueError:
        print("Error: message size must be an integer.")
        return

    if message_size <= 0:
        print("Error: message size must be greater than 0.")
        return

    # Create Host A
    host_a = Host(
        name="Host A",
        ip=HOST_A_IP,
        mac=HOST_A_MAC,
        mac_table=MAC_TABLE_A,
        default_gateway_ip=R1_IF1_IP,
        connected_router_interface="if1"
    )

    # Create Host B
    host_b = Host(
        name="Host B",
        ip=HOST_B_IP,
        mac=HOST_B_MAC,
        mac_table=MAC_TABLE_B,
        default_gateway_ip=R1_IF2_IP,
        connected_router_interface="if2"
    )

    # Create Router R1
    router = Router(name="Router R1")

    # Connect router interfaces to hosts
    router.connect("if1", host_a)
    router.connect("if2", host_b)

    # Start sending application data from Host A to Host B
    host_a.send_application_data(
        data_size=message_size,
        dst_ip=HOST_B_IP,
        router=router
    )


if __name__ == "__main__":
    main()