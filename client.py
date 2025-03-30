import pygame
import socket
import math
from bullet import Bullet

# Client Setup
host = '127.0.0.1'
port = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

# Initialize Pygame
pygame.init()
screen_width, screen_height = 800, 533
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Tank Shooter - Multiplayer')

# Load assets
background_image = pygame.image.load(r"assets/background.jpg")
tank_image = pygame.image.load(r"assets\image_no_bg.png")
tank_image = pygame.transform.scale(tank_image, (40, 40))

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

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
    player_tanks = [Tank(400, 300), Tank(400, 300)]  # 2 player tanks
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
        dx, dy = mouse_x - player_tanks[0].x, mouse_y - player_tanks[0].y
        # Use atan2(dy, dx) for a direct point-at-mouse approach
        raw_angle = math.degrees(math.atan2(dy, dx))
        # If your tank sprite points “up” by default, adjust as needed
        player_tanks[0].angle = raw_angle  # Or just raw_angle, or raw_angle + 90, etc.  
        send_command(f"ROTATE:{player_tanks[0].angle}")
        # Receive state from server
        try:
            data = client_socket.recv(1024).decode()
            if data:
                # Check if the client received a lose/respawn notification
                if "LOSE" in data:
                    # Display lose notification
                    font = pygame.font.SysFont("Arial", 50)
                    text = font.render("You Lose!", True, RED)
                    screen.blit(text, (screen_width // 2 - text.get_width() // 2,
                                    screen_height // 2 - text.get_height() // 2))
                    pygame.display.update()
                    pygame.time.delay(2000)  # Show message for 2 seconds
                    # Instead of stopping, continue so that the new respawn position from the server takes effect
                    continue
                elif "WIN" in data:
                    # Display win notification
                    font = pygame.font.SysFont("Arial", 50)
                    text = font.render("You Win!", True, (0, 255, 0))  # green text
                    screen.blit(text,
                        (screen_width // 2 - text.get_width() // 2,
                        screen_height // 2 - text.get_height() // 2))
                    pygame.display.update()
                    pygame.time.delay(2000) 
                    continue
                bullets.clear()
                lines = data.split("\n")
                player_index = 0
                for line in lines:
                    if not line.strip():
                        continue
                    if line.startswith("BULLET"):
                        _, bullet_data = line.split(":")
                        bx, by, bangle = map(float, bullet_data.split(","))
                        bullets.append(Bullet(bx, by, bangle))
                    elif line.startswith("PLAYER") and player_index < 2:
                        # Player data: PLAYER:x,y,angle
                        _, tank_data = line.split(":")
                        x, y, angle = map(float, tank_data.split(","))
                        player_tanks[player_index].x = x
                        player_tanks[player_index].y = y
                        player_tanks[player_index].angle = angle
                        player_index += 1
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

game_loop()