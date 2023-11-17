import socket
import signal
import random
import time
import sys

# Define probabilities
drop_data_prob = 0.1  # 10% chance to drop data
drop_ack_prob = 0.1   # 10% chance to drop ack
delay_prob = 0.1      # 10% chance to delay packet
max_delay = 4         # Maximum delay in seconds

# Define global variables
receiver_ip = None
receiver_port = None
listen_port = None
sock = None

def proxy_init():
    try: 
        global receiver_ip, receiver_port, listen_port, sock
        if len(sys.argv) != 4:
            # raise ValueError("Usage: python proxy.py [Receiver IP] [Receiver Port] [Listen Port]")
            receiver_ip = "10.0.0.210"
            receiver_port = 12345
            listen_port = 1234
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', listen_port))
            handler()
            

        receiver_ip = sys.argv[1]
        receiver_port = int(sys.argv[2])
        listen_port = int(sys.argv[3])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', listen_port))

        handler()
    except Exception as e:
        error(e, "proxy_init")

def handler():
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            if not data:
                #this is dumb idk what to do lol
                raise ValueError(f"Interesting data {data.decode()}")
            print(f"Proxy received from {addr}: {data.decode()}")

            # Forwarding data to receiver
            data_to_receiver(data, addr)

            # Receiving ACK from receiver and forwarding it back to the sender
            ACK_to_sender(addr)

    except Exception as e: 
        error(e, "handler")

def data_to_receiver(data, sender_addr):
    global sock
    try:
        # Randomly drop data packet
        if random.random() < drop_data_prob:
            print("Dropping data packet.")
            return

        # Randomly delay data packet
        if random.random() < delay_prob:
            print(f"sleeping data packet for up to {max_delay}")
            time.sleep(random.uniform(0, max_delay))

        # Forwarding data to receiver
        sock.sendto(data, (receiver_ip, receiver_port))

    except Exception as e:
        error(e, "data_to_receiver")

def ACK_to_sender(sender_addr):
    global sock
    try:
        ack_data, receiver_addr = sock.recvfrom(4096)

        # Randomly drop ACK
        if random.random() < drop_ack_prob:
            print("Dropping ACK packet.")
            return

        # Randomly delay ACK
        if random.random() < delay_prob:
            print(f"sleeping ACK packet for up to {max_delay}")
            time.sleep(random.uniform(0, max_delay))

        # Forwarding ACK back to sender
        sock.sendto(ack_data, sender_addr)

    except Exception as e:
        error(e, "ACK_to_sender")

def error(message, stateName):
    print(f"\nError Message: {message}\nState: {stateName}")
    destroy()

def handle_sigint(signum, frame):
    print("\nInterrupt signal received. Shutting down...")
    destroy()

def destroy():
    print("Closing the proxy...")
    #if socket exists close it
    if sock:
        print("Closing the socket...")
        sock.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    proxy_init()
