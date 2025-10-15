import pygame
from gameplay import gameplay

def swimming_pool(screen, current_map):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - swimming_pool")
    return gameplay(screen, "assets/maps/swimming_pool.png")
