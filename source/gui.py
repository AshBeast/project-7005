import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import socket
import threading
import json
from queue import Queue
import sys

# Global variables to hold data for plotting
data_queues = {
    'sender': Queue(),
    'receiver': Queue(),
    'proxy': Queue()
}
time_stamps = []
need_update = {'sender': False, 'receiver': False, 'proxy': False}

def start_server(ip, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ip, port))
        server_socket.listen(5)
        print(f"Server started on {ip}:{port}")

        while True:
            client, addr = server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=handle_client, args=(client,)).start()
    except Exception as e:
        print("Error starting the server", str(e))

def handle_client(client):
    while True:
        data = client.recv(1024).decode()
        if not data:
            break
        print(f"Received data: {data}")  # Debugging line
        data_json = json.loads(data)
        client_id = data_json.get('client_id')
        if client_id in data_queues:
            data_queues[client_id].put(data_json)
            need_update[client_id] = True

def create_client_window(client_id, title):
    window = tk.Toplevel()
    window.title(title)

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().pack()

    # Initialize Statistics lists for plotting
        #sender Statistics
    sent_data_packets = []
    received_ACK_packets = []
        #receiver Statistics
    sent_ACK_packets = []
    received_data_packets = []
    time_stamps = []
        #proxy Statistics
    dropped_ACK_packets = []
    dropped_data_packets = []
    delayed_ACK_packets = []
    delayed_data_packets = []
    total_ACK_packets = []
    total_data_packets = []

    def update_graph():
        nonlocal sent_data_packets, received_ACK_packets, sent_ACK_packets, received_data_packets, \
        dropped_ACK_packets, dropped_data_packets, delayed_ACK_packets, delayed_data_packets, total_ACK_packets, total_data_packets, time_stamps
        try:
            if need_update[client_id]:
                data_queue = data_queues[client_id]
                while not data_queue.empty():
                    data = data_queue.get()
                    print(f"Updating {client_id} graph with data: {data}")  # Debugging line

                    if client_id == 'sender':
                        sent_data_packets.append(data['sent_data_packets'])
                        received_ACK_packets.append(data['received_ACK_packets'])
                        time_stamps.append(len(time_stamps))
                        if time_stamps:
                            ax.clear()
                            ax.plot(time_stamps, sent_data_packets, label='Sent Data Packets')
                            ax.plot(time_stamps, received_ACK_packets, label='Received ACK Packets')
                            ax.legend()
                            ax.set_xlabel('Time (Updates)')
                            ax.set_ylabel('Packet Count')

                    elif client_id == 'receiver':
                        sent_ACK_packets.append(data['sent_ACK_packets'])
                        received_data_packets.append(data['received_data_packets'])
                        time_stamps.append(len(time_stamps))
                        if time_stamps:
                            ax.clear()
                            ax.plot(time_stamps, sent_ACK_packets, label='Sent ACK Packets')
                            ax.plot(time_stamps, received_data_packets, label='Received Data Packets')
                            ax.legend()
                            ax.set_xlabel('Time (Updates)')
                            ax.set_ylabel('Packet Count')

                    elif client_id == 'proxy':
                        dropped_ACK_packets.append(data["dropped_ACK_packets"])
                        dropped_data_packets.append(data["dropped_data_packets"])
                        delayed_ACK_packets.append(data["delayed_ACK_packets"])
                        delayed_data_packets.append(data["delayed_data_packets"])
                        total_ACK_packets.append(data["total_ACK_packets"])
                        total_data_packets.append(data["total_data_packets"])
                        time_stamps.append(len(time_stamps))
                        if time_stamps:
                            ax.clear()
                            ax.plot(time_stamps, dropped_ACK_packets, label='Dropped ACK Packets')
                            ax.plot(time_stamps, dropped_data_packets, label='Dropped Data Packets')
                            ax.plot(time_stamps, delayed_ACK_packets, label='Delayed ACK Packets')
                            ax.plot(time_stamps, delayed_data_packets, label='Delayed Data Packets')
                            ax.plot(time_stamps, total_ACK_packets, label='Total ACK Packets')
                            ax.plot(time_stamps, total_data_packets, label='Total Data Packets')
                            ax.legend()
                            ax.set_xlabel('Time (Updates)')
                            ax.set_ylabel('Packet Count')
                            
                canvas.draw()
                need_update[client_id] = False
        except Exception as e:
            print(f"Error in update_graph for {client_id}: {e}")

        window.after(1000, update_graph)

    window.after(1000, update_graph)
    return window

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gui.py [IP] [Port]")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    sender_window = create_client_window('sender', 'Sender Statistics')
    receiver_window = create_client_window('receiver', 'Receiver Statistics')
    proxy_window = create_client_window('proxy', 'Proxy Statistics')

    threading.Thread(target=start_server, args=(ip, port), daemon=True).start()
    root.mainloop()
