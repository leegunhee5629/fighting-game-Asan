import pygame
import sys
from scenes.title import title

pygame.init() 

S_WIDTH = 1080
S_HEIGHT = 720
screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))


FPS = 60
clock = pygame.time.Clock() 


current_scene = "Title"
scenes = {
  "Title": title,
  # "Characters": characters,
  # "Maps": maps,
  # "In_game": in_game
}

while current_scene:
  current_scene = scenes[current_scene](screen)
  pygame.display.update()
  clock.tick(FPS)

pygame.quit()
sys.exit()