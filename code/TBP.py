import pygame
import numpy as np
import sys
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants - Larger window with more space for simulation
WIDTH, HEIGHT = 1200, 900
SIMULATION_HEIGHT = 700  # Most of the screen for simulation
CONTROL_HEIGHT = HEIGHT - SIMULATION_HEIGHT
FPS = 60
G = 6.67430e-11  # gravitational constant
SCALE = 3e9  # Increased scale to see more movement
TIME_STEP = 3600 * 24  # 1 day in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)

# Create the window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Three-Body Problem - Triangular Configuration")
clock = pygame.time.Clock()

# Font for UI
font = pygame.font.SysFont('Arial', 16)
title_font = pygame.font.SysFont('Arial', 20, bold=True)

class Body:
    def __init__(self, mass, position, velocity, color, name, radius=10):
        self.mass = mass
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.color = color
        self.name = name
        self.radius = radius
        self.trail = []
        self.max_trail_length = 400
        
    def update_position(self, bodies, dt):
        # Calculate gravitational forces from all other bodies
        acceleration = np.zeros(2)
        for body in bodies:
            if body is not self:
                r = body.position - self.position
                distance = np.linalg.norm(r)
                if distance > 0:
                    force_magnitude = G * self.mass * body.mass / (distance ** 2 + 1e5)
                    acceleration += force_magnitude * r / (distance * self.mass)
        
        # Update velocity and position
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        
        # Add current position to trail
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
    
    def draw(self, screen):
        # Draw trail
        if len(self.trail) > 1:
            points = []
            for pos in self.trail:
                x = pos[0] / SCALE + WIDTH/2
                y = pos[1] / SCALE + SIMULATION_HEIGHT/2
                if -2000 < x < WIDTH + 2000 and -2000 < y < SIMULATION_HEIGHT + 2000:
                    points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(screen, self.color, False, points, 2)
        
        # Draw body
        try:
            x = int(self.position[0] / SCALE + WIDTH/2)
            y = int(self.position[1] / SCALE + SIMULATION_HEIGHT/2)
            
            if -2000 < x < WIDTH + 2000 and -2000 < y < SIMULATION_HEIGHT + 2000:
                pygame.draw.circle(screen, self.color, (x, y), self.radius)
                
                # Draw name
                name_text = font.render(self.name, True, WHITE)
                screen.blit(name_text, (x - name_text.get_width()//2, y + self.radius + 5))
        except (ValueError, TypeError, OverflowError):
            pass

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
        self.label = label
        
    def draw(self, screen):
        # Draw slider track
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=3)
        
        # Draw slider handle
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        pygame.draw.circle(screen, WHITE, (int(handle_x), self.rect.centery), 8)
        
        # Draw label and value
        label_text = font.render(f"{self.label}: {self.value:.1e}", True, WHITE)
        screen.blit(label_text, (self.rect.x, self.rect.y - 20))
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
                
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            
        elif event.type == MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
            
    def update_value(self, x):
        # Calculate value based on mouse position
        rel_x = max(0, min(self.rect.width, x - self.rect.x))
        self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)

# Create initial bodies in equilateral triangle formation
def create_triangle_configuration(mass1=1e30, mass2=1e30, mass3=1e30, size=2.5e11):
    # Equilateral triangle points
    bodies = [
        Body(mass1, [0, -size], [1.2e4, 0], RED, "Body 1", 12),
        Body(mass2, [size * np.sqrt(3)/2, size/2], [-6e3, -1.04e4], GREEN, "Body 2", 12),
        Body(mass3, [-size * np.sqrt(3)/2, size/2], [-6e3, 1.04e4], BLUE, "Body 3", 12)
    ]
    return bodies

# Create sliders for mass control
sliders = [
    Slider(50, SIMULATION_HEIGHT + 30, 250, 1e28, 5e30, 1e30, "Body 1 Mass"),
    Slider(50, SIMULATION_HEIGHT + 70, 250, 1e28, 5e30, 1e30, "Body 2 Mass"),
    Slider(50, SIMULATION_HEIGHT + 110, 250, 1e28, 5e30, 1e30, "Body 3 Mass")
]

# Create buttons
class Button:
    def __init__(self, x, y, width, height, text, color=GRAY):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=3)
        pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=3)
        
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def is_clicked(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

reset_button = Button(350, SIMULATION_HEIGHT + 30, 120, 30, "Reset")
pause_button = Button(350, SIMULATION_HEIGHT + 70, 120, 30, "Pause")
clear_trails_button = Button(350, SIMULATION_HEIGHT + 110, 120, 30, "Clear Trails")

# Initialize simulation
bodies = create_triangle_configuration()
paused = False
simulation_speed = 1.0

def reset_simulation():
    global bodies
    masses = [slider.value for slider in sliders]
    bodies = create_triangle_configuration(masses[0], masses[1], masses[2])

def clear_trails():
    for body in bodies:
        body.trail = []

# Main game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
            
        # Handle sliders
        for slider in sliders:
            slider.handle_event(event)
            
        # Handle buttons
        if reset_button.is_clicked(event):
            reset_simulation()
            
        if pause_button.is_clicked(event):
            paused = not paused
            
        if clear_trails_button.is_clicked(event):
            clear_trails()
            
        # Speed control with mouse wheel
        if event.type == MOUSEWHEEL:
            simulation_speed *= 1.2 if event.y > 0 else 0.8
            simulation_speed = max(0.1, min(10.0, simulation_speed))
    
    # Update physics if not paused
    if not paused:
        for _ in range(int(simulation_speed)):
            for body in bodies:
                body.update_position(bodies, TIME_STEP)
    
    # Draw everything
    screen.fill(BLACK)
    
    # Draw center reference point
    pygame.draw.circle(screen, GRAY, (WIDTH//2, SIMULATION_HEIGHT//2), 3)
    
    # Draw boundary line between simulation and controls
    pygame.draw.line(screen, WHITE, (0, SIMULATION_HEIGHT), (WIDTH, SIMULATION_HEIGHT), 2)
    
    # Draw bodies
    for body in bodies:
        body.draw(screen)
    
    # Draw UI panel
    pygame.draw.rect(screen, DARK_GRAY, (0, SIMULATION_HEIGHT, WIDTH, CONTROL_HEIGHT))
    
    # Draw title
    title_text = title_font.render("Three-Body Problem - Equilateral Triangle Configuration", True, WHITE)
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 20))
    
    # Draw sliders
    for slider in sliders:
        slider.draw(screen)
    
    # Draw buttons
    reset_button.draw(screen)
    pause_button.draw(screen)
    clear_trails_button.draw(screen)
    
    # Draw status and info
    status_text = "PAUSED" if paused else "RUNNING"
    status_color = RED if paused else GREEN
    status_surf = font.render(f"Status: {status_text}", True, status_color)
    screen.blit(status_surf, (500, SIMULATION_HEIGHT + 30))
    
    speed_text = font.render(f"Simulation Speed: {simulation_speed:.1f}x", True, WHITE)
    screen.blit(speed_text, (500, SIMULATION_HEIGHT + 60))
    
    # Draw mass ratio info
    mass1 = sliders[0].value
    mass2 = sliders[1].value
    mass3 = sliders[2].value
    total_mass = mass1 + mass2 + mass3
    
    if total_mass > 0:
        ratio_text = font.render(f"Mass Ratio: {mass1/total_mass:.2f} : {mass2/total_mass:.2f} : {mass3/total_mass:.2f}", True, WHITE)
        screen.blit(ratio_text, (500, SIMULATION_HEIGHT + 90))
    
    # Draw distance info between bodies
    if len(bodies) == 3:
        dist1 = np.linalg.norm(bodies[0].position - bodies[1].position)
        dist2 = np.linalg.norm(bodies[1].position - bodies[2].position)
        dist3 = np.linalg.norm(bodies[2].position - bodies[0].position)
        
        dist_text = font.render(f"Distances: {dist1/1e11:.2f} / {dist2/1e11:.2f} / {dist3/1e11:.2f} x10¹¹ m", True, WHITE)
        screen.blit(dist_text, (500, SIMULATION_HEIGHT + 120))
    
    info_text = font.render("Use mouse wheel to adjust simulation speed | Drag sliders to change mass", True, GRAY)
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, SIMULATION_HEIGHT + 150))
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()