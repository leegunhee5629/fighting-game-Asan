import pygame

pygame.mixer.init()

map_config = {
  "map_list": [
    {"name": "수영장", "codename": "swimming_pool", "rect": pygame.Rect(256, 313.5, 160, 160)},
  ],
  "selected_map": None
}

def get_mapname_by_codename(codename):
  for map in map_config["map_list"]:
    if map["codename"] == codename:
      return map["name"]
  return None

def maps(screen, current_scene):
  global map_config

  pygame.display.set_caption("Bounce Attack (REMASTERED) - 맵 선택")

  background = pygame.image.load("assets/img/maps.png")
  background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  screen.blit(background, (0, 0))

  swimming_pool_rect = map_config["map_list"][0]["rect"]
  swimming_pool = pygame.image.load("assets/maps/swimming_pool.png")
  swimming_pool = pygame.transform.scale(swimming_pool, (swimming_pool_rect.width, swimming_pool_rect.height))
  swimming_pool_rect = swimming_pool.get_rect(center=swimming_pool_rect.center)
  screen.blit(swimming_pool, swimming_pool_rect)

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None
    if event.type == pygame.MOUSEBUTTONDOWN:
      mouse_pos = pygame.mouse.get_pos()
      for map in map_config["map_list"]:
        if map["rect"].collidepoint(mouse_pos):
          map_config["selected_map"] = map["codename"]
          return "map_loading"

  return "Maps"
