import json
import socket
import signal
import sys
import datetime
import threading
import time

#statistics
sent_ACK_packets = 0
received_data_packets = 0

# Define global variables
sock = None
    #gui variables
gui_ip = None
gui_port = None
gui_socket = None

received_sequences = 0  # To keep track of received sequence numbers

def receiver():
    global sock, sent_ACK_packets
    try: 
        if len(sys.argv) != 2:
            raise ValueError("Usage: python receiver.py [Port]")
        
        port = int(sys.argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))

        connect_to_gui = input("Do you want to connect to the GUI? (yes/no): ").lower()
        if connect_to_gui == "yes":
            if setup_gui_connection() == 0:
                threading.Thread(target=send_statistics_to_gui, daemon=True).start()
        
        while True:
            addr, sequence = wait_for_data()
            # Sending ACK
            ack_message = f"{sequence}:ACK"
            sent_ACK_packets += 1
            sock.sendto(ack_message.encode(), addr)

    except Exception as e:
        error(e, "receiver")

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
    global gui_socket
    try:
        while True:
            if gui_socket:
                stats = {
                    "client_id": "receiver",
                    "sent_ACK_packets": sent_ACK_packets,
                    "received_data_packets": received_data_packets
                }
                gui_socket.sendall(json.dumps(stats).encode())
            time.sleep(1)  # Delay to prevent overwhelming the network
    except Exception as e:
        print(f"Error in sending statistics to GUI: {e}")
        gui_socket.close()
        gui_socket = None



def wait_for_data():
    global sock, received_data_packets, received_sequences

    try:
        data, addr = sock.recvfrom(4096)
        if not data:
            raise ValueError("No data received.")

        # Decode the bytes to a string
        data_str = data.decode()

        sequence, message = data_str.split(':', 1)
        sequence = int(sequence)

        if sequence <= received_sequences and sequence != 0:
            print("Duplicate message ignored.")
            return addr, sequence

        received_sequences = sequence  # Add sequence number to the set of received sequences
        received_data_packets += 1
        print(f"{message}")


        if (data_str == "0:end"):
            received_sequences = 0
            print(f"test{sequence}")

        return addr, sequence
    except Exception as e:
        error(e, "wait_for_data")


        
    
def error(message, stateName):
    print(f"\nError Message: {message}\nState: {stateName}")
    destroy()

def handle_sigint(signum, frame):
    print("\nInterrupt signal received. Shutting down...")
    destroy()

def destroy():
    print("Closing the receiver...")
    #if socket exists close it
    if sock:
        print("Closing the socket...")
        sock.close()
    
    print("\nstatistics")
    print(f"sent ACK packets: {sent_ACK_packets}")
    print(f"received data packets: {received_data_packets}")

    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Write statistics to a file
    with open("statisticsReceiver.txt", "a") as file:
        file.write(f"Statistics as of {current_date_time}\n\n")
        file.write(f"sent ACK packets: {sent_ACK_packets}\n")
        file.write(f"received data packets: {received_data_packets}\n=========================\n")

    print("Statistics saved to statisticsReceiver.txt")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    receiver()
