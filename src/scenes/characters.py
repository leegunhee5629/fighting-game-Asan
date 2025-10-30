# ...existing code...
import os
import pygame

pygame.mixer.init()

character_config = {
  "character_list": [
    {"name": "이생선", "codename": "leesaengseon", "rect": pygame.Rect(40, 380, 85, 85)},
    {"name": "해골",   "codename": "haegol",       "rect": pygame.Rect(150, 380, 85, 85)},
    {"name": "조커",   "codename": "joker",       "rect": pygame.Rect(260, 380, 85, 85)},
    {"name": "아이스맨","codename": "iceman",     "rect": pygame.Rect(370, 380, 85, 85)},
    {"name": "마녀",   "codename": "witch",       "rect": pygame.Rect(480, 380, 85, 85)},
    {"name": "두더지", "codename": "mole",        "rect": pygame.Rect(590, 380, 85, 85)},
    {"name": "보노보노","codename": "bonobono",   "rect": pygame.Rect(700, 380, 85, 85)},
    {"name": "파이터", "codename": "fighter",     "rect": pygame.Rect(810, 380, 85, 85)},
  ],
  "selected_1p": None,
  "selected_2p": None,
}

# 스킬 함수들 (간단히 자리만 확보)
def leesaengseon_skill1(p1, p2, skill_state):
  pass
def leesaengseon_skill2(p1, p2, skill_state):
  pass
def leesaengseon_ultimate(p1, p2, skill_state):
  pass

def haegol_skill1(p1, p2, skill_state, bones, owner):
  current_time = pygame.time.get_ticks()
  if current_time - skill_state.get("last_used", 0) < skill_state.get("cooldown", 0):
    return
  skill_state["last_used"] = current_time
  try:
    bone_img = pygame.image.load("assets/characters/haegol/skill1.png").convert_alpha()
    bone_img = pygame.transform.scale(bone_img, (80, 80))
  except Exception:
    bone_img = None

  bone = {
    "x": p1.get("x", 0) + (100 if owner == "p1" else -100),
    "y": p1.get("y", 0) + 80,
    "vx": 15 if p2.get("x", 0) > p1.get("x", 0) else -15,
    "active": True,
    "damage": 10,
    "img": bone_img,
    "owner": owner
  }
  bones.append(bone)

def haegol_skill2(p1, p2, skill_state):
  pass
def haegol_ultimate(p1, p2, skill_state):
  pass

# 캐릭터 스킬 함수 매핑
character_skill = {
  "leesaengseon": [leesaengseon_skill1, leesaengseon_skill2, leesaengseon_ultimate],
  "haegol":       [haegol_skill1, haegol_skill2, haegol_ultimate],
  # 나머지 캐릭터는 필요한 경우 추가
}

# 캐릭터 스킬 상태: 안전한 방식으로 생성 (NameError 방지)
_default_skill_template = {
  "skill1":  {"cooldown": 500,  "last_used": 0, "active": False},
  "skill2":  {"cooldown": 1000,  "last_used": 0, "active": False},
  "ultimate":{"cooldown":10000, "last_used": 0, "active": False},
}
character_skill_state = {}
for c in [c["codename"] for c in character_config["character_list"]]:
  character_skill_state[c] = {k: v.copy() for k, v in _default_skill_template.items()}
# 개별 튜닝
if "haegol" in character_skill_state:
  character_skill_state["haegol"]["skill2"]["cooldown"] = 5000

text_1p = None
text_2p = None
start_time = None
process = 0

def get_charactername_by_codename(codename):
  if not codename:
    return None
  for char in character_config["character_list"]:
    if char["codename"] == codename:
      return char["name"]
  return None

def _safe_load_image(path, size=None):
  if not path or not os.path.exists(path):
    return None
  try:
    img = pygame.image.load(path).convert_alpha()
    if size:
      img = pygame.transform.scale(img, size)
    return img
  except Exception:
    return None

def characters(screen, current_scene):
  global character_config, text_1p, text_2p, start_time, process

  if start_time is None:
    start_time = pygame.time.get_ticks()

  pygame.display.set_caption("Bounce Attack (REMASTERED) - 캐릭터 선택")

  background = _safe_load_image("assets/img/characters.png", (screen.get_width(), screen.get_height()))
  if background:
    screen.blit(background, (0, 0))
  else:
    screen.fill((30, 120, 60))

  if current_scene == "Characters" and not pygame.mixer.music.get_busy():
    music_path = "assets/bgm/F1_starting_grid.mp3"
    if os.path.exists(music_path):
      try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.play(0, fade_ms=2000)
      except Exception:
        pass

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
      text_1p = font.render(get_charactername_by_codename(character_config["selected_1p"]) or "", True, (0, 255, 0))
      text_2p = font.render("선택 준비", True, (255, 255, 0))
      if blink:
        text_2p = font.render("", True, (0, 255, 0))
    elif process == 3:
      text_1p = font.render(get_charactername_by_codename(character_config["selected_1p"]) or "", True, (0, 255, 0))
      text_2p = font.render(get_charactername_by_codename(character_config["selected_2p"]) or "", True, (0, 255, 0))
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

  # 마우스 위치로 hover 코드네임 계산
  mouse_pos = pygame.mouse.get_pos()
  hover_codename = None
  for char in character_config["character_list"]:
    if char["rect"].collidepoint(mouse_pos):
      hover_codename = char["codename"]
      break

  # 미리보기 그리기 (hover 우선, 아니면 선택된 것 보여줌)
  def _draw_preview_for_player(player_idx, centerx, centery):
    sel = character_config["selected_1p"] if player_idx == 1 else character_config["selected_2p"]
    if (process == 1 and player_idx == 1) or (process == 2 and player_idx == 2):
      show_codename = hover_codename or sel
    else:
      show_codename = sel or None

    if not show_codename:
      return

    path = f"assets/characters/{show_codename}/body.png"
    img = _safe_load_image(path, (200, 200))
    if img:
      screen.blit(img, img.get_rect(center=(centerx, centery)))
    else:
      pygame.draw.rect(screen, (220,220,220), (centerx-100, centery-100, 200, 200))
      small = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 24)
      name = get_charactername_by_codename(show_codename) or show_codename
      label = small.render(name, True, (0,0,0))
      screen.blit(label, label.get_rect(center=(centerx, centery)))

  _draw_preview_for_player(1, text_1p_rect.centerx, text_1p_rect.centery + 130)
  _draw_preview_for_player(2, text_2p_rect.centerx, text_2p_rect.centery + 130)

  # (타일/아이콘 렌더링 없음 — rect는 hover/클릭 판정에 계속 사용)
  # 이벤트 처리: 좌클릭으로 hover된 캐릭터를 확정
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      return None
    if event.type == pygame.MOUSEBUTTONDOWN and elapsed > 1000:
      if event.button == 1 and hover_codename:
        if process == 1:
          character_config["selected_1p"] = hover_codename
          start_time = pygame.time.get_ticks()
          process = 2
        elif process == 2:
          character_config["selected_2p"] = hover_codename
          start_time = None
          process = 3

  return "Characters"
# ...existing code...