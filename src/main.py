import pygame
import sys
from scenes.title import title
from scenes.characters import characters
from scenes.maps import maps
from maps.loading import map_loading
from maps.swimming_pool import swimming_pool

pygame.init() 

screen = pygame.display.set_mode((1080, 720))

FPS = 60
clock = pygame.time.Clock() 

current_screen = "Title"
past_screen = "Title"

screens = {
  "Title": title,
  "Characters": characters,
  "Maps": maps,
  "map_loading": map_loading,
  "swimming_pool": swimming_pool,
}

while current_screen:
  if current_screen[0].isupper() != past_screen[0].isupper():
    if current_screen[0].isupper():
      pygame.mouse.set_visible(True)
      screen = pygame.display.set_mode((1080, 720))
    else:
      pygame.mouse.set_visible(False)
      screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    past_screen = current_screen
  
  current_screen = screens[current_screen](screen, current_screen)
    
  clock.tick(FPS)
  if pygame.display.get_init():
    pygame.display.update()

pygame.quit()
sys.exit()