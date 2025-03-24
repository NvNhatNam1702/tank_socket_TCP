# filepath: d:\personal_work\build_project_from_scratch\client.py
import pygame
import socket
import math
import time
from bullet import Bullet  # Import Bullet class

# Client Setup
host = '127.0.0.1'
port = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

# Initialize Pygame
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Client: Simple Battle Tank')

# Load assets
background_image = pygame.image.load(r"assets/background.jpg")
tank_image = pygame.image.load(r"assets/tank.jpg")
tank_image = pygame.transform.scale(tank_image, (40, 40))

# Colors
WHITE = (255, 255, 255)

# Tank class
class Tank:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle

    def draw(self):
        rotated_image = pygame.transform.rotate(tank_image, -self.angle)
        new_rect = rotated_image.get_rect(center=(self.x, self.y))
        screen.blit(rotated_image, new_rect.topleft)

# Send commands
def send_command(command):
    try:
        client_socket.send(command.encode())
    except:
        pass

# Game loop
def game_loop():
    clock = pygame.time.Clock()
    tank = Tank(400, 300)
    bullets = []  # Local bullets

    running = True
    while running:
        screen.fill(WHITE)
        screen.blit(background_image, (0, 0))

        # Event handling
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

        # Rotate turret based on mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx, dy = mouse_x - tank.x, mouse_y - tank.y
        tank.angle = math.degrees(math.atan2(-dy, dx))
        send_command(f"ROTATE:{tank.angle}")

        # Receive state from server
        try:
            data = client_socket.recv(1024).decode()
            if data:
                bullets.clear()
                lines = data.split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    if line.startswith("BULLET"):
                        # Bullet data: BULLET:x,y,angle
                        _, bullet_data = line.split(":")
                        bx, by, bangle = map(float, bullet_data.split(","))
                        bullets.append(Bullet(bx, by, bangle))
                    else:
                        # Tank data: e.g. Player1:400,300,90
                        # Update local tank with values in line
                        player_id, tank_data = line.split(":")
                        x, y, angle = map(float, tank_data.split(","))
                        # For a single-player client, just update local tank
                        tank.x, tank.y, tank.angle = x, y, angle
        except:
            pass

        # Draw tank
        tank.draw()

        # Draw bullets
        for bullet in bullets:
            pygame.draw.circle(screen, (255, 0, 0), (int(bullet.x), int(bullet.y)), 5)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    client_socket.close()

game_loop()
