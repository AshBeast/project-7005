import socket
import signal
import sys

# Define global variables
proxy_ip = None
proxy_port = None
sock = None

def sender_init():
    global proxy_ip, proxy_port, sock

    try:
        if len(sys.argv) != 3:
            raise ValueError("Usage: python sender.py [Proxy IP] [Proxy Port]")

        proxy_ip = sys.argv[1]
        proxy_port = int(sys.argv[2])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        handler()
    except Exception as e:
        error(e, "sender_init")

def send_message(message):
    global proxy_ip, proxy_port, sock

    try:
        if not message:
            raise ValueError("No message entered")
        sock.sendto(message.encode(), (proxy_ip, proxy_port))
    except Exception as e:
        error(e, "make_message_state")

def wait_for_ACK():
    global sock
    try:
        sock.settimeout(2.0)  # Set timeout for ACK
        data, server = sock.recvfrom(4096)
        print(f"Received ACK: {data.decode()}")
        return 0
    except socket.timeout:
        print("No ACK received.\n")
        return 1
    except Exception as e:
        error(e, "wait_for_ACK")

def handler():
    while True:
        message = input("Enter message to send: ")
        send_message(message)
        while (wait_for_ACK() != 0):
            print("Resending message...")
            send_message(message)

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
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    sender_init()

