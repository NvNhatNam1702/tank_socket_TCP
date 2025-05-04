import pygame
import socket
import math
import sys
import tkinter as tk
from tkinter import messagebox
from bullet import Bullet

# ----------------------------
# Game Logic (Pygame based)
# ----------------------------

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

    # Tank class defined inside game_loop (so it can use loaded images and screen)
    class Tank:
        def __init__(self, x, y, angle=0):
            self.x = x
            self.y = y
            self.angle = angle

        def draw(self):
            rotated_image = pygame.transform.rotate(tank_image, -self.angle)
            new_rect = rotated_image.get_rect(center=(self.x, self.y))
            screen.blit(rotated_image, new_rect.topleft)

    # Send commands to server
    def send_command(command):
        try:
            client_socket.send(command.encode())
        except:
            pass

    clock = pygame.time.Clock()
    player_tanks = []
    bullets = []

    running = True
    while running:
        screen.fill(WHITE)
        screen.blit(background_image, (0, 0))

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                send_command("SHOOT")

        # Handle movement input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            send_command("MOVE:LEFT")
        elif keys[pygame.K_RIGHT]:
            send_command("MOVE:RIGHT")
        elif keys[pygame.K_UP]:
            send_command("MOVE:UP")
        elif keys[pygame.K_DOWN]:
            send_command("MOVE:DOWN")

        # Update tank turret rotation based on mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if player_tanks:
            dx = mouse_x - player_tanks[0].x
            dy = mouse_y - player_tanks[0].y
            angle = math.degrees(math.atan2(dy, dx))
            player_tanks[0].angle = angle
            send_command(f"ROTATE:{angle}")

        # Receive data from server
        try:
            data = client_socket.recv(4096).decode()
            if data:
                player_tanks.clear()
                bullets.clear()
                lines = data.split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    if line.startswith("PLAYER"):
                        # Expected format: "PLAYER:x,y,angle"
                        _, tank_data = line.split(":")
                        x, y, angle = map(float, tank_data.split(","))
                        player_tanks.append(Tank(x, y, angle))
                    elif line.startswith("BULLET"):
                        # Expected format: "BULLET:bx,by,bangle"
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
        except:
            pass

        # Draw tanks
        for tank in player_tanks:
            tank.draw()

        # Draw bullets
        for bullet in bullets:
            pygame.draw.circle(screen, RED, (int(bullet.x), int(bullet.y)), 5)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    client_socket.close()
    sys.exit()

# ----------------------------
# Tkinter UI for IP Adjustment
# ----------------------------

def connect_and_start(ip):
    port = 5555  # Fixed port for your game
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        data = client_socket.recv(1024).decode()
        if "FULL" in data:
            messagebox.showinfo("Server Full", "Server is full. Please try again later.")
            client_socket.close()
            return
    except Exception as e:
        messagebox.showerror("Connection Error", f"Unable to connect: {e}")
        return
    # Close the launcher UI and start the game loop
    launcher.destroy()
    game_loop(client_socket)

launcher = tk.Tk()
launcher.title("Tank Shooter Client")

tk.Label(launcher, text="Server IP Address:").pack(pady=10)
ip_entry = tk.Entry(launcher, width=30)
ip_entry.insert(0, "192.168.1.4")  # Default IP; change as needed
ip_entry.pack(pady=5)

connect_button = tk.Button(launcher, text="Connect and Play", 
                           command=lambda: connect_and_start(ip_entry.get()))
connect_button.pack(pady=20)

launcher.mainloop()