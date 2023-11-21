import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import socket
import threading
import json
from queue import Queue
import sys

# Global variables to hold data for plotting
sent_data_packets = []
received_ACK_packets = []
time_stamps = []

def start_server(ip, port, data_queue):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ip, port))
        server_socket.listen(5)
        print(f"Server started on {ip}:{port}")

        while True:
            client, addr = server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=handle_client, args=(client, data_queue)).start()
    except Exception as e:
        print("Error starting the server", str(e))

def handle_client(client, data_queue):
    while True:
        data = client.recv(1024).decode()
        if not data:
            break
        print(f"Received data: {data}")  # Debugging line
        data_queue.put(json.loads(data))

def update_graph(data_queue, ax, canvas, fig):
    global sent_data_packets, received_ACK_packets, time_stamps
    while not data_queue.empty():
        data = data_queue.get()
        print(f"Updating graph with data: {data}")  # Debugging line
        # Append new data to the lists
        sent_data_packets.append(data["sent_data_packets"])
        received_ACK_packets.append(data["received_ACK_packets"])
        time_stamps.append(len(time_stamps))  # Assuming each update is at a regular interval

    # Clear the current plot
    ax.clear()

    # Plot new data
    if time_stamps:
        ax.plot(time_stamps, sent_data_packets, label='Sent Data Packets')
        ax.plot(time_stamps, received_ACK_packets, label='Received ACK Packets')
        ax.legend()

        # Redraw the canvas
        canvas.draw()

    # Schedule the next update
    root.after(1000, update_graph, data_queue, ax, canvas, fig)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gui.py [IP] [Port]")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    root = tk.Tk()
    data_queue = Queue()

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()

    threading.Thread(target=start_server, args=(ip, port, data_queue), daemon=True).start()
    root.after(1000, update_graph, data_queue, ax, canvas, fig)
    root.mainloop()
