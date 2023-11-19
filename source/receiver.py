import socket
import signal
import sys
import datetime

#statistics
sent_ACK_packets = 0
received_data_packets = 0

# Define global variables
sock = None

def receiver():
    global sock, sent_ACK_packets
    try: 
        if len(sys.argv) != 2:
            print("Usage: python receiver.py [Port]")
            sys.exit(1)

        port = int(sys.argv[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        
        while True:
            addr = wait_for_data()

            # Sending ACK
            ack_message = "ACK"
            sent_ACK_packets += 1
            sock.sendto(ack_message.encode(), addr)

    except Exception as e:
        error(e, "receiver")

def wait_for_data():
    global sock, received_data_packets
    try:
        data, addr = sock.recvfrom(4096)
        if not data:
            raise ValueError(f"Interesting data {data.decode()}") 

        received_data_packets += 1
        print(f"Received: {data.decode()}")
        return addr
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
    
    print("statistics\n")
    print(f"sent ACK packets: {sent_ACK_packets}")
    print(f"received data packets: {received_data_packets}")

    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Write statistics to a file
    with open("statisticsReceiver.txt", "a") as file:
        file.write(f"Statistics as of {current_date_time}\n\n")
        file.write(f"sent ACK packets: {sent_ACK_packets}\n")
        file.write(f"received data packets: {received_data_packets}\n=========================\n\n")

    print("Statistics saved to statisticsReceiver.txt")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    receiver()
