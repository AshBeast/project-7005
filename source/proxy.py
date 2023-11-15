import socket
import sys

def main(receiver_ip, receiver_port, listen_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', listen_port))

    while True:
        data, addr = sock.recvfrom(4096)
        if not data:
            break
        print(f"Proxy received from {addr}: {data.decode()}")

        # Forwarding data to receiver
        sock.sendto(data, (receiver_ip, receiver_port))

        # Receiving ACK from receiver and forwarding it back to the sender
        ack_data, receiver_addr = sock.recvfrom(4096)
        sock.sendto(ack_data, addr)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python proxy.py [Receiver IP] [Receiver Port] [Listen Port]")
        sys.exit(1)

    receiver_ip = sys.argv[1]
    receiver_port = int(sys.argv[2])
    listen_port = int(sys.argv[3])
    main(receiver_ip, receiver_port, listen_port)
