import socket
import threading
import math

# Server Setup
host = '127.0.0.1'
port = 5555

# Game Data
clients = {}
tanks = {}

# Tank class
class Tank:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 5

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def rotate(self, angle):
        self.angle = angle  # Set angle instead of incrementing

    def serialize(self):
        return f"{self.x},{self.y},{self.angle}"

# Handle client connections
def handle_client(client_socket, client_id):
    print(f"New connection: {client_id}")

    # Initialize a tank for the client
    tanks[client_id] = Tank(400, 300)

    while True:
        try:
            # Receive data from the client (player's input)
            data = client_socket.recv(1024).decode()
            if not data:
                break

            # Process the input (e.g., moving or rotating the tank)
            if data.startswith('MOVE'):
                direction = data.split(":")[1]
                if direction == "LEFT":
                    tanks[client_id].move(-tanks[client_id].speed, 0)
                elif direction == "RIGHT":
                    tanks[client_id].move(tanks[client_id].speed, 0)
                elif direction == "UP":
                    tanks[client_id].move(0, -tanks[client_id].speed)
                elif direction == "DOWN":
                    tanks[client_id].move(0, tanks[client_id].speed)

            elif data.startswith('ROTATE'):
                angle = float(data.split(":")[1])
                tanks[client_id].rotate(angle)

            # Send updated positions of all tanks back to all clients
            game_state = "\n".join([f"{client}:{tank.serialize()}" for client, tank in tanks.items()])
            for c_id, c_socket in clients.items():
                try:
                    c_socket.send(game_state.encode())
                except:
                    pass  # Ignore disconnected clients
        except:
            break

    # Remove client and its tank when they disconnect
    print(f"Connection closed: {client_id}")
    del clients[client_id]
    del tanks[client_id]
    client_socket.close()

# Server main loop
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server started. Waiting for clients to connect...")

    client_id_counter = 1
    while True:
        client_socket, addr = server_socket.accept()
        client_id = f"Player{client_id_counter}"  # Assign unique ID
        clients[client_id] = client_socket
        client_id_counter += 1
        threading.Thread(target=handle_client, args=(client_socket, client_id)).start()

# Start the server
start_server()
