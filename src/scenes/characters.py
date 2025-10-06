import pygame

pygame.mixer.init()

character_config = {
  "character_list": [
    {"name": "이생선", "codename": "leesaengseon", "rect": pygame.Rect(70, 380, 85, 85)},
    {"name": "해골", "codename": "haegol", "rect": pygame.Rect(175, 380, 85, 85)},
  ],
  "selected_1p": None,
  "selected_2p": None,
}

text_1p = None
text_2p = None

start_time = None

process = 0

def get_charactername_by_codename(codename):
  for char in character_config["character_list"]:
    if char["codename"] == codename:
      return char["name"]
  return None

def characters(screen, current_scene):
  global character_config, text_1p, text_2p, start_time, process, get_charactername_by_codename

  if start_time is None:
    start_time = pygame.time.get_ticks()

  pygame.display.set_caption("Bounce Attack (REMASTERED) - 캐릭터 선택")

  background = pygame.image.load("assets/img/characters.png")
  background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  screen.blit(background, (0, 0))

  if current_scene == "Characters" and not pygame.mixer.music.get_busy():
    pygame.mixer.music.load("assets/bgm/F1_starting_grid.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(0, fade_ms=2000)

  font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 40)

  elapsed = pygame.time.get_ticks() - start_time
  if process == 0 and elapsed > 3000:
    process = 1

  # 단계별 문구 표시
  if process == 0:
    text_1p = font.render("Player 1", True, (255, 255, 255))
    text_2p = font.render("Player 2", True, (255, 255, 255))

  else:
    blink = (pygame.time.get_ticks() // 750) % 2

    if process == 1:
      text_1p = font.render("선택 준비", True, (255, 255, 0))
      text_2p = font.render("Player 2", True, (255, 255, 255))

      if blink:
        text_1p = font.render("", True, (0, 255, 0))

    elif process == 2:
      text_1p = font.render(get_charactername_by_codename(character_config["selected_1p"]), True, (0, 255, 0))

      text_2p = font.render("선택 준비", True, (255, 255, 0))

      if blink:
        text_2p = font.render("", True, (0, 255, 0))

    elif process == 3:
      text_1p = font.render(get_charactername_by_codename(character_config["selected_1p"]), True, (0, 255, 0))
      text_2p = font.render(get_charactername_by_codename(character_config["selected_2p"]), True, (0, 255, 0))

      if start_time is None:
        start_time = pygame.time.get_ticks()

      if elapsed > 3000:
        text_1p = font.render("", True, (255, 255, 255))
        text_2p = font.render("", True, (255, 255, 255))

      if elapsed > 3500:
        text_1p = font.render("Player 1", True, (255, 255, 255))
        text_2p = font.render("Player 2", True, (255, 255, 255))

      if elapsed > 6000:
        return "Maps"

  text_1p_rect = text_1p.get_rect(center=(300, 70))
  text_2p_rect = text_2p.get_rect(center=(screen.get_width() - 300, 70))
  
  screen.blit(text_1p, text_1p_rect)
  screen.blit(text_2p, text_2p_rect)

  if character_config["selected_1p"]:
    img_1p = pygame.image.load(f"assets/characters/{character_config["selected_1p"]}/body.png")
    img_1p = pygame.transform.scale(img_1p, (200, 200))
    screen.blit(img_1p, img_1p.get_rect(center=(text_1p_rect.centerx, text_1p_rect.centery + 130)))

  if character_config["selected_2p"]:
    img_2p = pygame.image.load(f"assets/characters/{character_config["selected_2p"]}/body.png")
    img_2p = pygame.transform.scale(img_2p, (200, 200))
    screen.blit(img_2p, img_2p.get_rect(center=(text_2p_rect.centerx, text_2p_rect.centery + 130)))

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None

    if event.type == pygame.MOUSEBUTTONDOWN and elapsed > 1000:
      for char in character_config["character_list"]:
        if char["rect"].collidepoint(event.pos):
          if process == 1:
            character_config["selected_1p"] = char["codename"]
            start_time = pygame.time.get_ticks()
            process = 2

          elif process == 2:
            character_config["selected_2p"] = char["codename"]
            start_time = None
            process = 3

  return "Characters"
