import pygame

def swimming_pool(screen, current_map):
  pygame.display.set_caption("Bounce Attack (REMASTERED) - 수영장")

  background = pygame.image.load("assets/maps/swimming_pool.png")
  background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  screen.blit(background, (0, 0))

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None

  return "swimming_pool"