import socket
import signal
import sys

receiver_ip = None
receiver_port = None
listen_port = None
sock = None

def proxy_init():
    try: 
        if len(sys.argv) != 4:
            raise ValueError("Usage: python proxy.py [Receiver IP] [Receiver Port] [Listen Port]")

        global receiver_ip, receiver_port, listen_port, sock

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
            data_to_receiver(data)

            # Receiving ACK from receiver and forwarding it back to the sender
            ACK_to_sender(addr)

    except Exception as e: 
        error(e, "handler")

def data_to_receiver(data):
    global sock
    try:
        sock.sendto(data, (receiver_ip, receiver_port))
    except Exception as e:
        error(e, "data_to_receiver")

def ACK_to_sender(addr):
    try:
        ack_data, receiver_addr = sock.recvfrom(4096)
        sock.sendto(ack_data, addr)
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
