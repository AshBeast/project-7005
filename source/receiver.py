import socket
import sys

def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    
    while True:
        data, addr = sock.recvfrom(4096)
        if not data:
            break
        print(f"Received: {data.decode()}")

        # Sending ACK
        ack_message = "ACK"
        sock.sendto(ack_message.encode(), addr)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python receiver.py [Port]")
        sys.exit(1)

    port = int(sys.argv[1])
    main(port)
