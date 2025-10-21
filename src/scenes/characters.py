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

def deal_damage(attacker, defender, damage):
        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0

        attacker["ultimate_gauge"] += 10
        if attacker["ultimate_gauge"] > 100:
            attacker["ultimate_gauge"] = 100

        defender["ultimate_gauge"] += 5
        if defender["ultimate_gauge"] > 100:
            defender["ultimate_gauge"] = 100

# 스킬 함수들 정의
def leesaengseon_skill1(p1, p2, skill_state):
  pass
def leesaengseon_skill2(p1, p2, skill_state):
  pass
def leesaengseon_ultimate(p1, p2, skill_state):
  pass

def haegol_skill1(p1, p2, skill_state, bones, owner):
  current_time = pygame.time.get_ticks()
  if current_time - skill_state["last_used"] < skill_state["cooldown"]:
    return #쿨타임 사용불가
  skill_state["last_used"] = current_time
  bone_img = pygame.image.load("assets/characters/haegol/skill1.png").convert_alpha()
  bone_img = pygame.transform.scale(bone_img, (80, 80))
  
  bone = { 
    "x": p1["x"] + (100 if owner == "p1" else -100),
    "y": p1["y"]  + 80,
    "vx": 15 if p2["x"] > p1["x"] else -15,
    "active": True,
    "damage": 10,
    "img": bone_img,
    "owner": owner
  }
  bones.append(bone)
  

def haegol_skill2(p1, p2, skill_state):
  current_time = pygame.time.get_ticks()
  if skill_state.get("in_action", False):
    return
  if current_time - skill_state["last_used"] < skill_state["cooldown"]:
    return #쿨타임 사용불가
  skill_state["last_used"] = current_time

  skill_state["in_action"] = True
  skill_state["last_used"] = current_time
  skill_state["damage_done"] = False

  bone_img = pygame.image.load("assets/characters/haegol/ultimate.png").convert_alpha()
  bone_img = pygame.transform.scale(bone_img, (160, 100))

  facing_right = p2["x"] > p1["x"]
  direction = 1 if facing_right else -1

  duration = 300
  max_reach = 160
  start_x = p1["x"] + (40 if facing_right else 40)
  start_y = p1["y"] + 60
  start_time = pygame.time.get_ticks()
  

  def draw_attack_effect(screen):
    elapsed = pygame.time.get_ticks() - start_time
    progress = min(1.0, elapsed / duration)
    distance = max_reach * progress
    attack_x = start_x + distance * direction
    attack_y = start_y

    screen.blit(bone_img, (attack_x, attack_y))

    if not skill_state["damage_done"]:
        hitbox = pygame.Rect(attack_x, attack_y, 120, 80)
        target_rect = pygame.Rect(p2["x"], p2["y"], 200, 200)
        if hitbox.colliderect(target_rect):
          deal_damage(p1, p2, 15)
          skill_state["damage_done"] = True

    if elapsed >= duration:
        skill_state["in_action"] = False
        return False
    return True


  skill_state["draw_func"] = draw_attack_effect


def haegol_ultimate(p1, skill_state):
  current_time = pygame.time.get_ticks()
  if skill_state.get("in_action", False):
    return
  if current_time - skill_state["last_used"] < skill_state["cooldown"]:
    return
  if p1["ultimate_gauge"] < 100:
    return #게이지 부족으로 인한 궁 사용불가

  skill_state["in_action"] = True
  skill_state["last_used"] = current_time
  skill_state["start_time"] = pygame.time.get_ticks()
  skill_state["duration"] = 3000
  skill_state["invincible"] = True
  p1["ultimate_gauge"] = 0

  def draw_ultimate(screen):
      elapsed = pygame.time.get_ticks() - skill_state["start_time"]

      pygame.draw.circle(screen, (255, 215, 0), (int(p1["x"] + 100), int(p1["y"] + 100)), 70, 5)
      

  
      if elapsed >= skill_state["duration"]:
           skill_state["in_action"] = False
           skill_state["invincible"] = False
           return False
      return True
  skill_state["draw_func"] = draw_ultimate
# 캐릭터 스킬 함수
character_skill = {
  "leesaengseon":  [leesaengseon_skill1, leesaengseon_skill2, leesaengseon_ultimate],
  "haegol":  [haegol_skill1, haegol_skill2, haegol_ultimate],
}
# 캐릭터 스킬 상태 리스트
character_skill_state = {
  "leesaengseon" : {
    "skill1": {"cooldown":2000 , "last_used":0, "active":False},
    "skill2": {"cooldown":1000 , "last_used":0, "active":False},
    "ultimate": {"cooldown":10000 , "last_used":0, "active":False},
  },
  "haegol" : {
    "skill1": {"cooldown":2000 , "last_used":0, "active":False},
    "skill2": {"cooldown":4000 , "last_used":0, "active":False},
    "ultimate": {"cooldown":10000 , "last_used":0, "active":False},
  },

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
    img_1p = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/body.png")
    img_1p = pygame.transform.scale(img_1p, (200, 200))
    screen.blit(img_1p, img_1p.get_rect(center=(text_1p_rect.centerx, text_1p_rect.centery + 130)))

  if character_config["selected_2p"]:
    img_2p = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/body.png")
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
