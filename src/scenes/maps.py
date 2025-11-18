import pygame
import os

pygame.mixer.init()

# 📢 [수정]: 맵 목록에 '하늘섬' 맵을 추가했습니다.
# '수영장' 맵 오른쪽 (X: 466)에 배치했습니다. (160 너비 + 약 50 픽셀 간격)
map_config = {
  "map_list": [
    {"name": "수영장", "codename": "swimming_pool", "rect": pygame.Rect(256, 313.5, 160, 160)},
    {"name": "하늘섬", "codename": "sky_island", "rect": pygame.Rect(466, 313.5, 160, 160)},
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

  # 배경 로드
  try:
      background = pygame.image.load("assets/img/maps.png")
      background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  except pygame.error:
      background = pygame.Surface((screen.get_width(), screen.get_height()))
      background.fill((0, 0, 0)) # 배경 이미지 없으면 검은색으로 대체
      
  screen.blit(background, (0, 0))

  # 📢 [수정]: 맵 리스트를 반복하여 모든 맵을 로드하고 렌더링합니다.
  for map_data in map_config["map_list"]:
      target_rect = map_data["rect"]
      codename = map_data["codename"]
      
      try:
          # assets/maps/{codename}.png 경로에서 맵 이미지 로드
          map_image = pygame.image.load(os.path.join("assets", "maps", f"{codename}.png"))
          map_image = pygame.transform.scale(map_image, (target_rect.width, target_rect.height))
          
          # 이미지를 목표 Rect의 중앙에 맞춥니다.
          image_rect = map_image.get_rect(center=target_rect.center)
          screen.blit(map_image, image_rect)
          
      except pygame.error as e:
          # 이미지 로드 실패 시 대체 표시 (디버그용)
          print(f"Error loading map image {codename}.png: {e}")
          pygame.draw.rect(screen, (255, 0, 0), target_rect, 2)

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None
    if event.type == pygame.MOUSEBUTTONDOWN:
      mouse_pos = pygame.mouse.get_pos()
      # 맵 선택 로직은 그대로 유지 (이미 모든 맵을 순회하고 있었음)
      for map in map_config["map_list"]:
        if map["rect"].collidepoint(mouse_pos):
          map_config["selected_map"] = map["codename"]
          return "map_loading"

  return "Maps"