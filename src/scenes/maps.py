import pygame

def maps(screen, current_scene):
  pygame.display.set_caption("Bounce Attack (REMASTERED) - 맵 선택")

  screen.fill((0, 0, 0))

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None

  return "Maps"
