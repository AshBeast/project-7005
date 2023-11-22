import json
import socket
import signal
import sys
import datetime
import threading
import time

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
        if len(sys.argv) != 3:
            raise ValueError("Usage: python sender.py [Proxy IP] [Proxy Port]")

        proxy_ip = sys.argv[1]
        proxy_port = int(sys.argv[2])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        connect_to_gui = input("Do you want to connect to the GUI? (yes/no): ").lower()
        if connect_to_gui == "yes":
            if setup_gui_connection() == 0:
                threading.Thread(target=send_statistics_to_gui, daemon=True).start()
            
        handler()
    except Exception as e:
        error(e, "sender_init")


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
        sock.settimeout(2.0)  # Set timeout for ACK
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
    while True:
        message = input("Enter message to send: ")
        sequence += 1
        send_message(f"{sequence}" + ":"+ message)
        while (wait_for_ACK(sequence) != 0):
            print("Resending message...")
            send_message(f"{sequence}" + ":"+ message)

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
