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

def disconnect_player(client_socket):
    global players
    if client_socket in players:
        del players[client_socket]
        try:
            client_socket.close()
        except:
            pass
        print("A player lost and was disconnected.")

# Bullet update logic
def update_bullets():
    global bullets
    for bullet in bullets[:]:
        # Update bullet position based on its angle
        rad = math.radians(bullet["angle"])
        bullet["x"] += 10 * math.cos(rad)
        bullet["y"] += 10 * math.sin(rad)

        # Remove bullets that go out of bounds
        if not (0 <= bullet["x"] <= 800 and 0 <= bullet["y"] <= 600):
            bullets.remove(bullet)
            continue

        # Check for collision with tanks
        for client_socket, tank in list(players.items()):
            if check_collision(bullet, tank):
                try:
                    # Notify the hit player
                    client_socket.send("LOSE".encode())
                except:
                    pass

                # Notify the other player of the win
                for other_socket in [s for s in players.keys() if s != client_socket]:
                    try:
                        other_socket.send("WIN".encode())
                    except:
                        pass

                # Respawn the hit tank at its default position
                if client_socket in players:
                    players[client_socket] = {"x": 200, "y": 300, "angle": 0} if client_socket == list(players.keys())[0] else {"x": 600, "y": 300, "angle": 0}

                bullets.remove(bullet)
                break

def check_collision(bullet, tank):
    bullet_radius = 5  # Same as drawing radius
    tank_width, tank_height = 40, 40  # Assumed tank dimensions
    # For simplicity, use center distance collision:
    distance = math.sqrt((bullet["x"] - tank["x"]) ** 2 + (bullet["y"] - tank["y"]) ** 2)
    return distance < (tank_width / 2 + bullet_radius)

def handle_client(client_socket, player_id):
    global players, bullets

    # Assign different initial positions based on player_id
    if player_id == 1:
        players[client_socket] = {"x": 200, "y": 300, "angle": 0}  # Tank 1 position
    elif player_id == 2:
        players[client_socket] = {"x": 600, "y": 300, "angle": 0}  # Tank 2 position
    else:
        client_socket.close()  # Invalid player ID, reject connection
        return

    try:
        while True:
            data = client_socket.recv(4096).decode()
            if not data:
                break

            # Handle movement
            if data.startswith("MOVE:"):
                print(f"Received MOVE: {data}")
                direction = data.split(":")[1]
                if direction == "LEFT":
                    players[client_socket]["x"] -= 5
                elif direction == "RIGHT":
                    players[client_socket]["x"] += 5
                elif direction == "UP":
                    players[client_socket]["y"] -= 5
                elif direction == "DOWN":
                    players[client_socket]["y"] += 5

            # Handle rotation
            elif data.startswith("ROTATE:"):
                try:
                    players[client_socket]["angle"] = float(data.split(":")[1])
                except ValueError:
                    print(f"Invalid ROTATE value: {data}")

            # Handle shooting
            elif data == "SHOOT":
                print(f"Received SHOOT from {client_socket}")
                px, py, angle = players[client_socket].values()
                offset = 25  # Adjust this based on tank size
                bullet_x = px + offset * math.cos(math.radians(angle))
                bullet_y = py + offset * math.sin(math.radians(angle))
                bullets.append({"x": bullet_x, "y": bullet_y, "angle": angle})
                print(f"Player {client_socket} fired a bullet from ({bullet_x}, {bullet_y}) at angle {angle}")

    except ConnectionResetError:
        print(f"Client {client_socket} forcibly closed the connection.")
    except Exception as e:
        print(f"Error handling client {client_socket}: {e}")

    finally:
        disconnect_player(client_socket)
        print(f"Player {player_id} disconnected.")
        if client_socket in players:
            del players[client_socket]  # Ensure key exists before deleting
        client_socket.close()


# Broadcast game state to all players
def send_updates():
    while True:
        time.sleep(1 / 120)  # 60 FPS

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