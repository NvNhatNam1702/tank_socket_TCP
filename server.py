import socket
import threading
import time
import math
import tkinter as tk
from tkinter import scrolledtext

# Game state
players = {}  # Store player info {client_socket: {"x": ..., "y": ..., "angle": ...}}
bullets = []  # Store all bullets [{"x": bx, "y": by, "angle": bangle}]

# Server setup
host = '0.0.0.0'
port = 5555
server_socket = None  # Initialize as None for dynamic start/stop

# Tkinter UI setup
root = tk.Tk()
root.title("Tank Shooter Server")

# UI Elements
log_text = scrolledtext.ScrolledText(root, width=50, height=20, state='disabled')
log_text.pack(pady=10)

def log_message(message):
    """Log a message to the UI."""
    log_text.config(state='normal')
    log_text.insert(tk.END, f"{message}\n")
    log_text.see(tk.END)
    log_text.config(state='disabled')

def start_server():
    """Start the server and begin accepting players."""
    global server_socket
    if server_socket is not None:
        log_message("Server is already running!")
        return

    try:
        # Initialize and bind the server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(4)  # Allow up to 4 players
        log_message("Server started. Waiting for players...")

        # Start threads for accepting players and sending updates
        threading.Thread(target=accept_players, daemon=True).start()
        threading.Thread(target=send_updates, daemon=True).start()
    except Exception as e:
        log_message(f"Error starting server: {e}")

def stop_server():
    """Stop the server and disconnect all players."""
    global server_socket, players
    if server_socket is None:
        log_message("Server is not running!")
        return

    try:
        # Close all client connections
        for client_socket in list(players.keys()):
            disconnect_player(client_socket)

        # Close the server socket
        server_socket.close()
        server_socket = None
        log_message("Server stopped.")
    except Exception as e:
        log_message(f"Error stopping server: {e}")

# Disconnect player function
def disconnect_player(client_socket):
    global players
    if client_socket in players:
        del players[client_socket]
        try:
            client_socket.close()
        except:
            pass
        log_message("A player disconnected.")

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
                    log_message(f"Player {list(players.keys()).index(client_socket) + 1} LOST!")
                except:
                    pass

                # Notify the other players of the win
                for other_socket in [s for s in players.keys() if s != client_socket]:
                    try:
                        other_socket.send("WIN".encode())
                        log_message(f"Player {list(players.keys()).index(other_socket) + 1} WON!")
                    except:
                        pass

                # Respawn the hit tank at its default position
                if client_socket in players:
                    # Assign positions based on the order: 
                    # Player 1: (200, 300), Player 2: (600, 300),
                    # Player 3: (200, 500), Player 4: (600, 500)
                    index = list(players.keys()).index(client_socket)
                    if index == 0:
                        players[client_socket] = {"x": 200, "y": 300, "angle": 0}
                    elif index == 1:
                        players[client_socket] = {"x": 600, "y": 300, "angle": 0}
                    elif index == 2:
                        players[client_socket] = {"x": 200, "y": 500, "angle": 0}
                    else:
                        players[client_socket] = {"x": 600, "y": 500, "angle": 0}

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

    # Assign initial positions based on player_id for 4 players
    if player_id == 1:
        players[client_socket] = {"x": 200, "y": 300, "angle": 0}  # Player 1 position
    elif player_id == 2:
        players[client_socket] = {"x": 600, "y": 300, "angle": 0}  # Player 2 position
    elif player_id == 3:
        players[client_socket] = {"x": 200, "y": 500, "angle": 0}  # Player 3 position
    elif player_id == 4:
        players[client_socket] = {"x": 600, "y": 500, "angle": 0}  # Player 4 position
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
                direction = data.split(":")[1]
                if direction == "LEFT":
                    players[client_socket]["x"] -= 5
                    log_message(f"Player {list(players.keys()).index(client_socket) + 1} MOVE LEFT")
                elif direction == "RIGHT":
                    players[client_socket]["x"] += 5
                    log_message(f"Player {list(players.keys()).index(client_socket) + 1} MOVE RIGHT")
                elif direction == "UP":
                    players[client_socket]["y"] -= 5
                    log_message(f"Player {list(players.keys()).index(client_socket) + 1} MOVE UP")
                elif direction == "DOWN":
                    players[client_socket]["y"] += 5
                    log_message(f"Player {list(players.keys()).index(client_socket) + 1} MOVE DOWN")

            # Handle rotation
            elif data.startswith("ROTATE:"):
                try:
                    players[client_socket]["angle"] = float(data.split(":")[1])
                except ValueError:
                    pass

            # Handle shooting
            elif data == "SHOOT":
                px, py, angle = players[client_socket].values()
                offset = 25  # Adjust this based on tank size
                bullet_x = px + offset * math.cos(math.radians(angle))
                bullet_y = py + offset * math.sin(math.radians(angle))
                bullets.append({"x": bullet_x, "y": bullet_y, "angle": angle})

    except ConnectionResetError:
        pass
    except Exception as e:
        log_message(f"Error handling client {player_id}: {e}")

    finally:
        disconnect_player(client_socket)
        log_message(f"Player {player_id} disconnected.")
        if client_socket in players:
            del players[client_socket]  # Ensure key exists before deleting
        client_socket.close()

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

def accept_players():
    player_id = 1
    while True:
        try:
            client_socket, addr = server_socket.accept()

            # Check if the maximum number of players is reached
            if player_id > 4:
                log_message(f"Connection attempt from {addr} rejected: Server full.")
                client_socket.send("FULL".encode())  # Notify the client that the server is full
                client_socket.close()  # Close the connection
                continue

            log_message(f"Player {player_id} connected from {addr}")
            threading.Thread(target=handle_client, args=(client_socket, player_id)).start()
            player_id += 1
        except Exception as e:
            log_message(f"Error accepting players: {e}")
            break

# Add Start and Stop buttons to the UI
start_button = tk.Button(root, text="Start Server", command=start_server, width=20)
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Server", command=stop_server, width=20)
stop_button.pack(pady=5)

# Start the Tkinter main loop
root.mainloop()