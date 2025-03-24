import socket
import threading
import time
import math

# Game state
players = {}  # Store player info {client_socket: {"x": 400, "y": 300, "angle": 0}}
bullets = []  # Store all bullets [{"x": bx, "y": by, "angle": bangle}]

# Server setup
host = '0.0.0.0'
port = 5555
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(2)  # Allow only 2 players

print("Waiting for players...")

# Bullet update logic
def update_bullets():
    global bullets
    for bullet in bullets[:]:
        # Update bullet position based on its angle
        rad = math.radians(bullet["angle"])
        bullet["x"] += 10 * math.cos(rad)
        bullet["y"] -= 10 * math.sin(rad)

        # Remove bullets that go out of bounds
        if bullet["x"] < 0 or bullet["x"] > 800 or bullet["y"] < 0 or bullet["y"] > 600:
            bullets.remove(bullet)

# Handle player commands
def handle_client(client_socket, player_id):
    global players, bullets

    players[client_socket] = {"x": 400, "y": 300, "angle": 0}  # Default position

    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            if data.startswith("MOVE:"):
                direction = data.split(":")[1]
                if direction == "LEFT":
                    players[client_socket]["x"] -= 5
                elif direction == "RIGHT":
                    players[client_socket]["x"] += 5
                elif direction == "UP":
                    players[client_socket]["y"] -= 5
                elif direction == "DOWN":
                    players[client_socket]["y"] += 5

            elif data.startswith("ROTATE:"):
                players[client_socket]["angle"] = float(data.split(":")[1])

            elif data == "SHOOT":
                px, py, angle = players[client_socket].values()
                bullets.append({"x": px, "y": py, "angle": angle})

        except:
            break

    print(f"Player {player_id} disconnected.")
    del players[client_socket]
    client_socket.close()

# Broadcast game state to all players
def send_updates():
    while True:
        time.sleep(1 / 60)  # 60 FPS

        # Update bullets
        update_bullets()

        # Prepare game state
        game_state = ""
        for client, tank in players.items():
            game_state += f"PLAYER:{tank['x']},{tank['y']},{tank['angle']}\n"

        for bullet in bullets:
            game_state += f"BULLET:{bullet['x']},{bullet['y']},{bullet['angle']}\n"

        # Send game state to all clients
        for client in players.keys():
            try:
                client.send(game_state.encode())
            except:
                pass

# Start accepting players
threading.Thread(target=send_updates, daemon=True).start()

player_id = 1
while len(players) < 2:
    client_socket, addr = server_socket.accept()
    print(f"Player {player_id} connected from {addr}")
    threading.Thread(target=handle_client, args=(client_socket, player_id)).start()
    player_id += 1