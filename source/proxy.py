import datetime
import json
import random
import signal
import socket
import sys
import threading
import re
import time
import argparse
import ipaddress

senderAddr = None
receiver_ip = None
receiver_port = None
sock_listen = None

#statistics
dropped_ACK_packets = 0
dropped_data_packets = 0
delayed_ACK_packets = 0
delayed_data_packets = 0
sent_ACK_packets = 0
sent_data_packets = 0

# Define probabilities
drop_data_prob = 0.1  # 10% chance to drop data
drop_ack_prob = 0.1   # 10% chance to drop ack
delay_data_prob = 0.1      # 10% chance to delay data packet
delay_ack_prob = 0.1      # 10% chance to delay ack packet
max_delay = 4         # Maximum delay in seconds

def get_valid_percentage(prompt):
    while True:
        input_value = input(prompt)
        try:
            # Remove '%' if present and convert to float
            if input_value.endswith('%'):
                input_value = input_value[:-1]
            value = float(input_value)

            if 0 <= value <= 100:
                return value / 100  # Convert percentage to a probability (0-1)
            else:
                print("Please enter a value between 0 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def proxy_init():
    try: 
        global receiver_ip, receiver_port, listen_port, sock_listen, drop_data_prob, drop_ack_prob, delay_data_prob, delay_ack_prob
        args = arg_handler()

        receiver_ip = args.receiver_ip[0]
        receiver_port = args.receiver_port[0]
        listen_port = args.listener_port[0]
        sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_listen.bind(('', listen_port))

        connect_to_gui = input("Do you want to connect to the GUI? (yes/no): ").lower()
        if connect_to_gui == "yes":
            if setup_gui_connection() == 0:
                threading.Thread(target=send_statistics_to_gui, daemon=True).start()

        # User input for probabilities
        drop_data_prob = get_valid_percentage("Enter percentage to drop data (0-100): ")
        drop_ack_prob = get_valid_percentage("Enter percentage to drop ACK (0-100): ")
        delay_data_prob = get_valid_percentage("Enter percentage to delay data packets (0-100): ")
        delay_ack_prob = get_valid_percentage("Enter percentage to delay ACK packets (0-100): ")

        threading.Thread(target=dynamicProb, daemon=True).start()

        handler()
    except Exception as e:
        error(e, "proxy_init")

# Parses and handles all commandline arguments
def arg_handler():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip",
        nargs=1,
        type=valid_ip,
        help="Enter a valid IPv4 or IPv6 address"
    )
    parser.add_argument(
        "receiver_port",
        nargs=1,
        type=valid_port,
        help="Enter a port between 1024 and 65535"
    )
    parser.add_argument(
        "listener_port",
        nargs=1,
        type=valid_port,
        help="Enter a port between 1024 and 65535"
    )
    return parser.parse_args()

# Check for valid ipv4 or ipv6
def valid_ip(host):
    try:
        ipaddress.ip_address(host)
    except ValueError:
        raise argparse.ArgumentTypeError("Not a valid IPv4 or IPv6 address")
    return host


# Check for valid port
def valid_port(port):
    try:
        p = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError('Port must be an integer between 1024 and 65535')
    if p < 1024 or p > 65535:
        raise argparse.ArgumentTypeError('Port must be between 1024 and 65535')
    return p

def dynamicProb():
    global drop_data_prob, drop_ack_prob, delay_data_prob, delay_ack_prob
    while True:
        print("\nChoose a probability to change:")
        print("1: Drop Data Probability")
        print("2: Drop ACK Probability")
        print("3: Delay Data Probability")
        print("4: Delay ACK Probability")        

        choice = input("Enter your choice (1-5):\n")

        if choice == "1":
            drop_data_prob = get_valid_percentage("Enter new Drop Data Probability (0-100): ")
        elif choice == "2":
            drop_ack_prob = get_valid_percentage("Enter new Drop ACK Probability (0-100): ")
        elif choice == "3":
            delay_data_prob = get_valid_percentage("Enter new Delay Data Probability (0-100): ")
        elif choice == "4":
            delay_ack_prob = get_valid_percentage("Enter new Delay ACK Probability (0-100): ")
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

#GUI connect
def setup_gui_connection():
    global gui_ip, gui_port, gui_socket
    try:
        gui_ip = input("Enter the GUI IP address: ")
        gui_port = int(input("Enter the GUI port: "))
        gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gui_socket.connect((gui_ip, gui_port))
        return 0
    except Exception as e:
        print(f"{e}\nGUI not connected")
        return 1

#GUI send data
def send_statistics_to_gui():
    global sent_data_packets, received_ACK_packets, gui_socket
    try:
        while True:
            if gui_socket:
                stats = {
                    "client_id": "proxy",
                    "dropped_ACK_packets": dropped_ACK_packets,
                    "dropped_data_packets": dropped_data_packets,
                    "delayed_ACK_packets": delayed_ACK_packets,
                    "delayed_data_packets": delayed_data_packets,
                    "total_ACK_packets": dropped_ACK_packets+sent_ACK_packets,
                    "total_data_packets": dropped_data_packets+sent_data_packets
                }
                gui_socket.sendall(json.dumps(stats).encode())
            time.sleep(1)  # Delay to prevent overwhelming the network
    except Exception as e:
        print(f"Error in sending statistics to GUI: {e}")
        gui_socket.close()
        gui_socket = None

def handler():
    global senderAddr, drop_data_prob, drop_ack_prob, delay_data_prob, delay_ack_prob, max_delay
    count = 0
    while True:
        data, Addr = sock_listen.recvfrom(4096)
        if (count == 0):
            senderAddr = Addr
            count += 1
        
        if (re.search(r'(?:\d+|end):ACK', data.decode())):
            # Acknowledgement packet received from client
            threading.Thread(target=send_sender, args=(data,), daemon=True).start()
        else:
            # Data packet received from client
            senderAddr = Addr
            threading.Thread(target=send_receiver, args=(data, (receiver_ip, receiver_port)), daemon=True).start()

def send_sender(ACK):
    global dropped_ACK_packets, delayed_ACK_packets, sent_ACK_packets
    try: 
        # Randomly drop ACK
        if random.random() < drop_ack_prob:
            print("Dropping ACK packet.")
            dropped_ACK_packets += 1
            return

        # Randomly delay ACK
        if random.random() < delay_ack_prob:
            print(f"sleeping ACK packet for up to {max_delay}")
            delayed_ACK_packets += 1
            time.sleep(random.uniform(0, max_delay))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(ACK, senderAddr)
        sent_ACK_packets += 1
        # sock.close()
    except Exception as e:
        error(e, "send_sender")

def send_receiver(data, receiverAddr):
    global dropped_data_packets, delayed_data_packets, sent_data_packets
    try:
        # Randomly drop data packet
        if random.random() < drop_data_prob:
            print("Dropping data packet.")
            dropped_data_packets += 1
            return 1

        # Randomly delay data packet
        if random.random() < delay_data_prob:
            print(f"sleeping data packet for up to {max_delay}")
            delayed_data_packets += 1
            time.sleep(random.uniform(0, max_delay))
        sock_listen.sendto(data, receiverAddr)
        sent_data_packets += 1
    except Exception as e:
        error(e, "send_receiver")

def error(message, stateName):
    print(f"\nError Message: {message}\nState: {stateName}")
    destroy()

def handle_sigint(signum, frame):
    print("\nInterrupt signal received. Shutting down...")
    destroy()

def destroy():
    print("Closing the proxy...")
    #if socket exists close it
    if sock_listen:
        print("Closing the socket...")
        sock_listen.close()

    # Get current date and time
    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write statistics to a file
    with open("statisticsProxy.txt", "a") as file:
        file.write(f"Statistics as of {current_date_time}\n\n")
        file.write(f"dropped_ACK_packets: {dropped_ACK_packets}\n")
        file.write(f"dropped_data_packets: {dropped_data_packets}\n")
        file.write(f"delayed_ACK_packets: {delayed_ACK_packets}\n")
        file.write(f"delayed_data_packets: {delayed_data_packets}\n")
        file.write(f"total_ACK_packets: {sent_ACK_packets + dropped_ACK_packets}\n")
        file.write(f"total_data_packets: {sent_data_packets + dropped_data_packets}\n")
        file.write(f"sent_ACK_packets: {sent_ACK_packets}\n")
        file.write(f"sent_data_packets: {sent_data_packets}\n=========================\n")

    print("Statistics saved to statisticsProxy.txt")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    proxy_init()