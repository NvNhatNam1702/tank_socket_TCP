import socket
import threading
import math
from bullet import Bullet  # Import Bullet class

# Server Setup
host = '127.0.0.1'
port = 5555

clients = {}  # Stores client sockets
tanks = {}  # Stores tank positions
bullets = []  # Stores active bullets

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
        self.angle = angle

    def shoot(self):
        """Create a bullet from the tank's position."""
        bullet = Bullet(self.x, self.y, self.angle)
        bullets.append(bullet)

    def serialize(self):
        return f"{self.x},{self.y},{self.angle}"

# Handle client connections
def handle_client(client_socket, client_id):
    print(f"New connection: {client_id}")
    tanks[client_id] = Tank(400, 300)

    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            # Process movement
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

            # Process rotation
            elif data.startswith('ROTATE'):
                angle = float(data.split(":")[1])
                tanks[client_id].rotate(angle)

            # Process shooting
            elif data.startswith('SHOOT'):
                tanks[client_id].shoot()

            # Update bullets
            for bullet in bullets[:]:
                bullet.move()
                if bullet.is_out_of_bounds():
                    bullets.remove(bullet)

            # Send updated game state
            game_state = "\n".join([f"{client}:{tank.serialize()}" for client, tank in tanks.items()])
            bullet_state = "\n".join([f"BULLET:{b.x},{b.y},{b.angle}" for b in bullets])
            full_state = game_state + "\n" + bullet_state

            for c_id, c_socket in clients.items():
                try:
                    c_socket.send(full_state.encode())
                except:
                    pass  # Ignore disconnected clients

        except:
            break

    # Clean up on disconnect
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
        client_id = f"Player{client_id_counter}"
        clients[client_id] = client_socket
        client_id_counter += 1
        threading.Thread(target=handle_client, args=(client_socket, client_id)).start()

# Start the server
start_server()
