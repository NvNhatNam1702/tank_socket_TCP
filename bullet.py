import math

class Bullet:
    def __init__(self, x, y, angle, speed=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.dx = math.cos(math.radians(angle)) * self.speed
        self.dy = -math.sin(math.radians(angle)) * self.speed

    def move(self):
        """ Update bullet position """
        self.x += self.dx
        self.y += self.dy

    def is_out_of_bounds(self, screen_width=800, screen_height=600):
        """ Check if the bullet is outside the game area """
        return self.x < 0 or self.x > screen_width or self.y < 0 or self.y > screen_height
