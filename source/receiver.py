import socket
import signal
import sys

# Define global variables
sock = None

def receiver():
    global sock
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
            sock.sendto(ack_message.encode(), addr)

    except Exception as e:
        error(e, "receiver")

def wait_for_data():
    global sock
    try:
        data, addr = sock.recvfrom(4096)
        if not data:
            raise ValueError(f"Interesting data {data.decode()}") 

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
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    receiver()
