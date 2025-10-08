import pygame
from scenes.maps import map_config, get_mapname_by_codename
from scenes.characters import character_config, get_charactername_by_codename

pygame.mixer.init()

start_time = None
end_time = None

def map_loading(screen, current_map):
  global start_time, end_time

  pygame.display.set_caption("Bounce Attack (REMASTERED) - 맵 로딩")

  if start_time is None:
    start_time = pygame.time.get_ticks()
    end_time = start_time + 12000

  remaining = (end_time - pygame.time.get_ticks()) / 1000

  screen.fill((0, 0, 0))

  font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 70)
  font_small = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 35)

  text_map = font.render(f"Map: {get_mapname_by_codename(map_config['selected_map'])}", True, (255, 255, 255))
  text_map_rect = text_map.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 290))
  screen.blit(text_map, text_map_rect)

  text_remaining = font.render(f"{remaining:.0f}초 후 게임이 시작됩니다", True, (255, 255, 255))
  text_remaining_rect = text_remaining.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 200))
  screen.blit(text_remaining, text_remaining_rect)

  text1p = font_small.render(f"Player 1: {get_charactername_by_codename(character_config['selected_1p'])}", True, (255, 255, 255))
  text1p_rect = text1p.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))
  screen.blit(text1p, text1p_rect)

  text2p = font_small.render(f"Player 2: {get_charactername_by_codename(character_config['selected_2p'])}", True, (255, 255, 255))
  text2p_rect = text2p.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 90))
  screen.blit(text2p, text2p_rect)

  if remaining < 0.1:
    start_time = None
    end_time = None
    pygame.mixer.music.fadeout(1000)
    return map_config["selected_map"]

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None

  return "map_loading"