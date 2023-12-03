import json
import socket
import signal
import sys
import datetime
import threading
import time
import argparse
import ipaddress

#statistics
sent_data_packets = 0
received_ACK_packets = 0

# Define global variables
proxy_ip = None
proxy_port = None
sock = None
    #gui variables
gui_ip = None
gui_port = None
gui_socket = None

def sender_init():
    global proxy_ip, proxy_port, sock

    try:
        args = arg_handler()

        proxy_ip = args.proxy_ip[0]
        proxy_port = args.proxy_port[0]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # connect_to_gui = input("Do you want to connect to the GUI? (yes/no): ").lower()
        
        # if connect_to_gui == "yes":
        #     if setup_gui_connection() == 0:
        #         threading.Thread(target=send_statistics_to_gui, daemon=True).start()
            
        handler()
    except Exception as e:
        error(e, "sender_init")


# Parses and handles all commandline arguments
def arg_handler():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "proxy_ip",
        nargs=1,
        type=valid_ip,
        help="Enter a valid IPv4 or IPv6 address"
    )
    parser.add_argument(
        "proxy_port",
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

def send_statistics_to_gui():
    global sent_data_packets, received_ACK_packets, gui_socket
    try:
        while True:
            if gui_socket:
                stats = {
                    "client_id": "sender",
                    "sent_data_packets": sent_data_packets,
                    "received_ACK_packets": received_ACK_packets
                }
                gui_socket.sendall(json.dumps(stats).encode())
            time.sleep(1)  # Delay to prevent overwhelming the network
    except Exception as e:
        print(f"Error in sending statistics to GUI: {e}")
        gui_socket.close()
        gui_socket = None

def send_message(message):
    global proxy_ip, proxy_port, sock, sent_data_packets

    try:
        if not message:
            raise ValueError("No message entered")
        sent_data_packets += 1
        sock.sendto(message.encode(), (proxy_ip, proxy_port))
    except Exception as e:
        error(e, "make_message_state")

def wait_for_ACK(sequence):
    global sock, received_ACK_packets
    try:
        sock.settimeout(1.0)  # Set timeout for ACK
        data, server = sock.recvfrom(4096)
        data = data.decode().strip()
        if (data== str(sequence)+":ACK"):
            received_ACK_packets += 1
            print(f"Received ACK: {data}")
            return 0
        print(f"broke: {data} \nneed: " + str(sequence)+":ACK")
        return 1
    except socket.timeout:
        print("No ACK received.\n")
        return 1
    except Exception as e:
        error(e, "wait_for_ACK")

def handler():
    sequence = 0
    message_buffer = ''
    max_chunk_size = 3000  # Maximum chunk size in bytes

    for line in sys.stdin:
        if line:  # Only add non-empty lines
            message_buffer += line

            # Check if the buffer size is at least 3000 bytes
            while len(message_buffer.encode('utf-8')) >= max_chunk_size:
                # Split the buffer into a chunk and the remainder
                chunk, message_buffer = message_buffer[:max_chunk_size], message_buffer[max_chunk_size:]
                sequence += 1
                send_message(f"{sequence}:{chunk}")
                while wait_for_ACK(sequence) != 0:
                    print("Resending message...")
                    send_message(f"{sequence}:{chunk}")

    # Send any remaining part of the message
    if message_buffer:
        sequence += 1
        send_message(f"{sequence}:{message_buffer}")
        while wait_for_ACK(sequence) != 0:
            print("Resending message...")
            send_message(f"{sequence}:{message_buffer}")

    print("End of input reached or no more input.")
    destroy()



def error(message, stateName):
    print(f"\nError Message: {message}\nState: {stateName}")
    destroy()

def handle_sigint(signum, frame):
    print("\nInterrupt signal received. Shutting down...")
    destroy()

def destroy():
    print("Closing the sender...")
    #if socket exists close it
    if sock:
        print("Closing the socket...")
        send_message("0:end")
        count = 1
        while (wait_for_ACK(0) != 0):
            if (count == 5):
                print("failed send \"end\" please close receiver")
                break
            send_message("0:end")
            count += 1
        sock.close()

    print("statistics\n")
    print(f"sent data packets: {sent_data_packets}")
    print(f"received ACK packets: {received_ACK_packets}")

    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write statistics to a file
    with open("statisticsSender.txt", "a") as file:
        file.write(f"Statistics as of {current_date_time}\n\n")
        file.write(f"sent data packets: {sent_data_packets}\n")
        file.write(f"received ACK packets: {received_ACK_packets}\n=========================\n")

    print("Statistics saved to statisticsSender.txt")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    sender_init()
