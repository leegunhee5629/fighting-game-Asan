import pygame
from gameplay import gameplay

def sky_island(screen, current_map):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - sky_island")
    return gameplay(screen, "assets/maps/sky_island.png")
