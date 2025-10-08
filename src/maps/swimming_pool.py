import pygame
from scenes.characters import character_config

def swimming_pool(screen, current_map):
  pygame.display.set_caption("Bounce Attack (REMASTERED) - 수영장")

  background = pygame.image.load("assets/maps/swimming_pool.png")
  background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  screen.blit(background, (0, 0))

  p1 = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/body.png")
  p1 = pygame.transform.scale(p1, (200, 200))
  screen.blit(p1, (100, 900))

  p2 = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/body.png")
  p2 = pygame.transform.scale(p2, (200, 200))
  screen.blit(p2, (screen.get_width() - 300, 900))

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None

  return "swimming_pool"