import socket
import threading
import time
import math
import tkinter as tk
from tkinter import scrolledtext

# Game state
players = {}  # Store player info {client_socket: {"x": ..., "y": ..., "angle": ..., "id": ...}}
bullets = []  # Store all bullets [{"x": bx, "y": by, "angle": bangle, "shooter_id": ...}]
scores = {}   # Store player scores {player_id: score}

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
    log_text.config(state='normal')
    log_text.insert(tk.END, f"{message}\n")
    log_text.see(tk.END)
    log_text.config(state='disabled')

def start_server():
    global server_socket
    if server_socket is not None:
        log_message("Server is already running!")
        return

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(4)
        log_message("Server started. Waiting for players...")
        threading.Thread(target=accept_players, daemon=True).start()
        threading.Thread(target=send_updates, daemon=True).start()
    except Exception as e:
        log_message(f"Error starting server: {e}")

def stop_server():
    global server_socket, players
    if server_socket is None:
        log_message("Server is not running!")
        return

    try:
        for client_socket in list(players.keys()):
            disconnect_player(client_socket)
        server_socket.close()
        server_socket = None
        log_message("Server stopped.")
    except Exception as e:
        log_message(f"Error stopping server: {e}")

def disconnect_player(client_socket):
    global players
    if client_socket in players:
        player_id = players[client_socket]["id"]
        del players[client_socket]
        if player_id in scores:
            del scores[player_id]
        try:
            client_socket.close()
        except:
            pass
        log_message(f"Player {player_id} disconnected.")

def update_bullets():
    global bullets
    for bullet in bullets[:]:
        rad = math.radians(bullet["angle"])
        bullet["x"] += 10 * math.cos(rad)
        bullet["y"] += 10 * math.sin(rad)

        if not (0 <= bullet["x"] <= 800 and 0 <= bullet["y"] <= 600):
            bullets.remove(bullet)
            continue

        for client_socket, tank in list(players.items()):
            if check_collision(bullet, tank):
                shooter_id = bullet["shooter_id"]
                if shooter_id in scores:
                    scores[shooter_id] += 1
                try:
                    client_socket.send("LOSE".encode())
                except:
                    pass

                for other_socket in [s for s in players.keys() if s != client_socket]:
                    try:
                        other_socket.send("WIN".encode())
                    except:
                        pass

                index = list(players.keys()).index(client_socket)
                spawn_positions = [(200, 300), (600, 300), (200, 500), (600, 500)]
                x, y = spawn_positions[index % len(spawn_positions)]
                tank_id = players[client_socket]["id"]
                players[client_socket] = {"x": x, "y": y, "angle": 0, "id": tank_id}
                bullets.remove(bullet)
                break

def check_collision(bullet, tank):
    bullet_radius = 5
    tank_width, tank_height = 40, 40
    distance = math.sqrt((bullet["x"] - tank["x"]) ** 2 + (bullet["y"] - tank["y"]) ** 2)
    return distance < (tank_width / 2 + bullet_radius)

def handle_client(client_socket, player_id):
    global players, bullets

    spawn_positions = [(200, 300), (600, 300), (200, 500), (600, 500)]
    if player_id > len(spawn_positions):
        client_socket.close()
        return

    x, y = spawn_positions[player_id - 1]
    players[client_socket] = {"x": x, "y": y, "angle": 0, "id": player_id}
    scores[player_id] = 0

    try:
        while True:
            data = client_socket.recv(4096).decode()
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
                try:
                    players[client_socket]["angle"] = float(data.split(":")[1])
                except ValueError:
                    pass

            elif data == "SHOOT":
                px = players[client_socket]["x"]
                py = players[client_socket]["y"]
                angle = players[client_socket]["angle"]
                offset = 25
                bullet_x = px + offset * math.cos(math.radians(angle))
                bullet_y = py + offset * math.sin(math.radians(angle))
                bullets.append({"x": bullet_x, "y": bullet_y, "angle": angle, "shooter_id": players[client_socket]["id"]})

    except Exception as e:
        log_message(f"Error handling client {player_id}: {e}")

    finally:
        disconnect_player(client_socket)

def send_updates():
    while True:
        time.sleep(1 / 120)
        update_bullets()

        game_state = ""
        for tank in players.values():
            game_state += f"PLAYER:{tank['x']},{tank['y']},{tank['angle']}\n"

        for bullet in bullets:
            game_state += f"BULLET:{bullet['x']},{bullet['y']},{bullet['angle']}\n"

        score_data = ",".join(f"{pid}={score}" for pid, score in scores.items())
        game_state += f"SCORE:{score_data}\n"

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

            if player_id > 4:
                log_message(f"Connection attempt from {addr} rejected: Server full.")
                client_socket.send("FULL".encode())
                client_socket.close()
                continue

            log_message(f"Player {player_id} connected from {addr}")
            threading.Thread(target=handle_client, args=(client_socket, player_id)).start()
            player_id += 1
        except Exception as e:
            log_message(f"Error accepting players: {e}")
            break

start_button = tk.Button(root, text="Start Server", command=start_server, width=20)
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Server", command=stop_server, width=20)
stop_button.pack(pady=5)

root.mainloop()
