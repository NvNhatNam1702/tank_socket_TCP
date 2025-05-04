import sys
import socket
import math
import pygame
import threading
import tkinter as tk
from tkinter import messagebox
from bullet import Bullet

# -------------------------------
# Pygame Game Code and Classes
# -------------------------------

# Tank class for rendering tanks on screen.
class Tank:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle

    def draw(self, screen, tank_image):
        rotated_image = pygame.transform.rotate(tank_image, -self.angle)
        new_rect = rotated_image.get_rect(center=(self.x, self.y))
        screen.blit(rotated_image, new_rect.topleft)

# Send commands to server.
def send_command(client_socket, command):
    try:
        client_socket.send(command.encode())
    except Exception as e:
        print("Send error:", e)

# Main game loop.
def game_loop(client_socket):
    pygame.init()
    screen_width, screen_height = 800, 533
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Tank Shooter - Multiplayer')

    # Load assets
    background_image = pygame.image.load(r"assets/background.jpg")
    tank_image = pygame.image.load(r"assets/image_no_bg.png")
    tank_image = pygame.transform.scale(tank_image, (40, 40))

    WHITE = (255, 255, 255)
    RED = (255, 0, 0)

    clock = pygame.time.Clock()
    player_tanks = []  # This list will be dynamically rebuilt
    bullets = []       # Local bullet list

    running = True
    while running:
        screen.fill(WHITE)
        screen.blit(background_image, (0, 0))

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                send_command(client_socket, "SHOOT")

        # Movement input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            send_command(client_socket, "MOVE:LEFT")
        elif keys[pygame.K_RIGHT]:
            send_command(client_socket, "MOVE:RIGHT")
        elif keys[pygame.K_UP]:
            send_command(client_socket, "MOVE:UP")
        elif keys[pygame.K_DOWN]:
            send_command(client_socket, "MOVE:DOWN")

        # Update turret rotation based on mouse for local tank (first tank)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if player_tanks:
            dx = mouse_x - player_tanks[0].x
            dy = mouse_y - player_tanks[0].y
            angle = math.degrees(math.atan2(dy, dx))
            player_tanks[0].angle = angle
            send_command(client_socket, f"ROTATE:{angle}")

        # Receive game state from server
        try:
            data = client_socket.recv(4096).decode()
            if data:
                # Clear previous game state
                player_tanks.clear()
                bullets.clear()
                lines = data.split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    if line.startswith("PLAYER"):
                        # Expected format: PLAYER:x,y,angle
                        _, tank_data = line.split(":")
                        x, y, angle = map(float, tank_data.split(","))
                        player_tanks.append(Tank(x, y, angle))
                    elif line.startswith("BULLET"):
                        # Expected format: BULLET:bx,by,bangle
                        _, bullet_data = line.split(":")
                        bx, by, bangle = map(float, bullet_data.split(","))
                        bullets.append(Bullet(bx, by, bangle))
                    elif "LOSE" in line:
                        font = pygame.font.SysFont("Arial", 50)
                        text = font.render("You Lose!", True, RED)
                        screen.blit(text, ((screen_width - text.get_width()) // 2,
                                           (screen_height - text.get_height()) // 2))
                        pygame.display.update()
                        pygame.time.delay(2000)
                        continue
                    elif "WIN" in line:
                        font = pygame.font.SysFont("Arial", 50)
                        text = font.render("You Win!", True, (0, 255, 0))
                        screen.blit(text, ((screen_width - text.get_width()) // 2,
                                           (screen_height - text.get_height()) // 2))
                        pygame.display.update()
                        pygame.time.delay(2000)
                        continue
        except Exception as e:
            print("Receive error:", e)
            running = False

        # Draw tanks
        for tank in player_tanks:
            tank.draw(screen, tank_image)
        # Draw bullets
        for bullet in bullets:
            pygame.draw.circle(screen, RED, (int(bullet.x), int(bullet.y)), 5)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    client_socket.close()
    sys.exit()

# -------------------------------
# Tkinter Launcher UI
# -------------------------------

def start_game():
    # Get server details from UI entries.
    ip = ip_entry.get().strip()
    port_str = port_entry.get().strip()

    if not ip or not port_str:
        messagebox.showerror("Input Error", "Please provide both IP and Port.")
        return

    try:
        port_num = int(port_str)
    except ValueError:
        messagebox.showerror("Input Error", "Port must be an integer.")
        return

    # Attempt to connect to the server.
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port_num))
        # Check if server returns a "FULL" message.
        data = client_socket.recv(1024).decode()
        if "FULL" in data:
            messagebox.showinfo("Server Full", "Server is full. Please try again later.")
            client_socket.close()
            return
    except Exception as e:
        messagebox.showerror("Connection Error", f"Unable to connect: {e}")
        return

    # Close the launcher window and start the game loop in a separate thread.
    root.destroy()
    game_loop(client_socket)

# Tkinter UI for client launcher.
root = tk.Tk()
root.title("Tank Shooter Client")

# IP and Port Frame
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="Server IP:").grid(row=0, column=0, sticky="e")
ip_entry = tk.Entry(frame, width=20)
ip_entry.insert(0, "192.168.1.13")  # default IP
ip_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame, text="Port:").grid(row=1, column=0, sticky="e")
port_entry = tk.Entry(frame, width=20)
port_entry.insert(0, "5555")  # default Port
port_entry.grid(row=1, column=1, padx=5, pady=5)

# Connect Button
connect_button = tk.Button(root, text="Connect and Start Game", command=start_game, width=30)
connect_button.pack(pady=10)

root.mainloop()