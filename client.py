import pygame
import socket
import math
import time

# Client Setup
host = '127.0.0.1'
port = 5555

# Initialize Pygame
pygame.init()

# Screen setup
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Client: Simple Battle Tank')

# Load background image
background_image = pygame.image.load(r"assets\background.jpg")  # Make sure you have this image in the same directory

# Load tank image
tank_image = pygame.image.load(r"assets/tank.jpg")  # Replace with your tank image path
tank_image = pygame.transform.scale(tank_image, (40, 40))  # Resize tank image if needed

# Colors
WHITE = (255, 255, 255)

# Tank class
class Tank:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 5
        self.vel_x = 0  # Velocity in X direction
        self.vel_y = 0  # Velocity in Y direction
        self.image = tank_image
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def move(self, direction, delta_time):
        # Update velocity based on direction
        if direction == "LEFT":
            self.vel_x = -self.speed
        elif direction == "RIGHT":
            self.vel_x = self.speed
        elif direction == "UP":
            self.vel_y = -self.speed
        elif direction == "DOWN":
            self.vel_y = self.speed
        else:
            self.vel_x = 0
            self.vel_y = 0
        
        # Smoothly move the tank (adding delta time to make it frame-rate independent)
        self.x += self.vel_x * delta_time
        self.y += self.vel_y * delta_time

        # Ensure tank stays within window boundaries (clamp the position)
        self.x = max(0, min(self.x, screen_width - self.rect.width))
        self.y = max(0, min(self.y, screen_height - self.rect.height))

    def stop(self):
        # Stop the movement when no key is pressed
        self.vel_x = 0
        self.vel_y = 0

    def rotate(self, angle):
        self.angle = angle  # Rotate the tank's angle

    def draw(self):
        rotated_image = pygame.transform.rotate(self.image, -self.angle)  # Pygame rotates counter-clockwise
        new_rect = rotated_image.get_rect(center=(self.x, self.y))
        screen.blit(rotated_image, new_rect.topleft)

# Connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

# Send movement input to server
def send_movement(direction):
    try:
        client_socket.send(f"MOVE:{direction}".encode())
    except:
        pass

# Send rotation input to server
def send_rotation(angle):
    try:
        client_socket.send(f"ROTATE:{angle}".encode())
    except:
        pass

# Main game loop
def game_loop():
    clock = pygame.time.Clock()
    tank = Tank(400, 300)
    last_time = time.time()  # Record the last time for delta time calculations
    running = True

    while running:
        screen.fill(WHITE)  # Fill screen with white as fallback
        screen.blit(background_image, (0, 0))  # Draw the background image
        
        delta_time = time.time() - last_time  # Calculate delta time for smoothness
        last_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Get key presses for movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            send_movement("LEFT")
        elif keys[pygame.K_RIGHT]:
            send_movement("RIGHT")
        elif keys[pygame.K_UP]:
            send_movement("UP")
        elif keys[pygame.K_DOWN]:
            send_movement("DOWN")
        else:
            send_movement("STOP")

        # Rotate turret with mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - tank.x
        dy = mouse_y - tank.y
        angle = math.degrees(math.atan2(-dy, dx))
        send_rotation(angle)

        # Receive updated game state from the server
        try:
            data = client_socket.recv(1024).decode()
            if data:
                tanks_data = data.split("\n")
                for tank_data in tanks_data:
                    tank_info = tank_data.split(":")
                    if len(tank_info) == 2:
                        _, position = tank_info
                        x, y, angle = map(float, position.split(","))
                        tank.x, tank.y, tank.angle = x, y, angle

        except:
            pass

        # Update tank's movement based on user input
        tank.move(keys, delta_time)

        # Draw the tank
        tank.draw()
        pygame.display.update()
        clock.tick(256)  # Cap frame rate to 60 FPS

    pygame.quit()
    client_socket.close()

# Start the game loop
game_loop()
