import socket
import sys

def main(proxy_ip, proxy_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        message = input("Enter message to send: ")
        if not message:
            break
        sock.sendto(message.encode(), (proxy_ip, proxy_port))

        # Waiting for ACK
        try:
            sock.settimeout(2.0)  # Set timeout for ACK
            data, server = sock.recvfrom(4096)
            print(f"Received ACK: {data.decode()}")
        except socket.timeout:
            print("No ACK received. Resending the message.")
            continue

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sender.py [Proxy IP] [Proxy Port]")
        sys.exit(1)

    proxy_ip = sys.argv[1]
    proxy_port = int(sys.argv[2])
    main(proxy_ip, proxy_port)
