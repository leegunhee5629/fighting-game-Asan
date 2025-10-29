import pygame
import copy
from scenes.characters import character_config, character_skill_state
from scenes.skills import get_skills_for_character

pygame.init()

def gameplay(screen, map_image_path):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - Gameplay")
    background = pygame.image.load(map_image_path)
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))

    # 캐릭터 이미지 불러오기 (안전하게 로드)
    def safe_load(path, size=None):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except Exception:
            return None

    sel1 = character_config.get("selected_1p")
    sel2 = character_config.get("selected_2p")

    p1_img = safe_load(f"assets/characters/{sel1}/body.png", (200, 200))
    p2_img = safe_load(f"assets/characters/{sel2}/body.png", (200, 200))

    p1_skill1_img = safe_load(f"assets/characters/{sel1}/skill1.png", (50, 50))
    p2_skill1_img = safe_load(f"assets/characters/{sel2}/skill1.png", (50, 50))
    p1_ultimate_img = safe_load(f"assets/characters/{sel1}/ultimate.png", (50, 50))
    p2_ultimate_img = safe_load(f"assets/characters/{sel2}/ultimate.png", (50, 50))

    # 스킬 객체 가져오기 (Skill 객체 리스트: [skill1, skill2, ultimate])
    p1_skills = get_skills_for_character(sel1) if sel1 else [None, None, None]
    p2_skills = get_skills_for_character(sel2) if sel2 else [None, None, None]

    p1_skill1 = p1_skills[0]
    p1_skill2 = p1_skills[1]
    p1_ultimate = p1_skills[2]

    p2_skill1 = p2_skills[0]
    p2_skill2 = p2_skills[1]
    p2_ultimate = p2_skills[2]

    # 발사체 / 월드
    projectiles = []
    world = {"projectiles": projectiles, "screen_width": screen.get_width()}

    p1_skill_state = copy.deepcopy(character_skill_state.get(sel1, {}))
    p2_skill_state = copy.deepcopy(character_skill_state.get(sel2, {}))

    # 캐릭터 상태
    p1 = {"x": 100, "y": 500, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0}
    p2 = {"x": 1260, "y": 500, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0}

    speed = 6
    jump_power = -18
    gravity = 1

    clock = pygame.time.Clock()
    running = True

    def draw_hp_bar(screen, x, y, hp, color):
        hp = max(0, min(100, hp))
        pygame.draw.rect(screen, (255, 0, 0), (x, y, 100, 10))
        pygame.draw.rect(screen, color, (x, y, hp, 10))

    def draw_ultimate_gauge(screen, x, y, gauge, color):
        gauge = max(0, min(100, gauge))
        pygame.draw.rect(screen, (128, 128, 128), (x, y, 100, 10))
        pygame.draw.rect(screen, color, (x, y, gauge, 10))

    def deal_damage(attacker, defender, damage):
        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        attacker["ultimate_gauge"] = min(100, attacker["ultimate_gauge"] + 10)
        defender["ultimate_gauge"] = min(100, defender["ultimate_gauge"] + 5)

    while running:
        screen.blit(background, (0, 0))
        keys = pygame.key.get_pressed()

        # 이동 입력
        if keys[pygame.K_a]:
            p1["vx"] = -speed
        elif keys[pygame.K_d]:
            p1["vx"] = speed
        else:
            p1["vx"] = 0
        if keys[pygame.K_w] and p1["on_ground"]:
            p1["vy"] = jump_power
            p1["on_ground"] = False

        if keys[pygame.K_LEFT]:
            p2["vx"] = -speed
        elif keys[pygame.K_RIGHT]:
            p2["vx"] = speed
        else:
            p2["vx"] = 0
        if keys[pygame.K_UP] and p2["on_ground"]:
            p2["vy"] = jump_power
            p2["on_ground"] = False

        # 스킬 입력 처리 (Skill 객체의 activate 사용)
        if keys[pygame.K_e] and p1_skill1:
            p1_skill1.activate(p1, p2, p1_skill_state.get("skill1", {}), world, owner="p1")
        if keys[pygame.K_r] and p1_skill2:
            p1_skill2.activate(p1, p2, p1_skill_state.get("skill2", {}), world, owner="p1")
        if keys[pygame.K_s] and p1_ultimate and p1["ultimate_gauge"] >= 100:
            p1_ultimate.activate(p1, p2, p1_skill_state.get("ultimate", {}), world, owner="p1")
            p1["ultimate_gauge"] = 0

        if keys[pygame.K_RETURN] and p2_skill1:
            p2_skill1.activate(p2, p1, p2_skill_state.get("skill1", {}), world, owner="p2")
        if (keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]) and p2_skill2:
            p2_skill2.activate(p2, p1, p2_skill_state.get("skill2", {}), world, owner="p2")
        if keys[pygame.K_DOWN] and p2_ultimate and p2["ultimate_gauge"] >= 100:
            p2_ultimate.activate(p2, p1, p2_skill_state.get("ultimate", {}), world, owner="p2")
            p2["ultimate_gauge"] = 0

        # 물리 업데이트
        for p in (p1, p2):
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if not p["on_ground"]:
                p["vy"] += gravity
            if p["y"] >= 500:
                p["y"] = 500
                p["vy"] = 0
                p["on_ground"] = True
            if p["x"] <= 0:
                p["x"] = 0
                p["vx"] = abs(p["vx"])
            elif p["x"] >= screen.get_width() - 200:
                p["x"] = screen.get_width() - 200
                p["vx"] = -abs(p["vx"])

        # 렌더
        if p1_img:
            screen.blit(p1_img, (int(p1["x"]), int(p1["y"])))
        if p2_img:
            screen.blit(p2_img, (int(p2["x"]), int(p2["y"])))

        draw_hp_bar(screen, 100, 50, p1["hp"], (0, 255, 0))
        draw_hp_bar(screen, screen.get_width() - 200, 50, p2["hp"], (0, 255, 0))
        draw_ultimate_gauge(screen, 100, 100, p1["ultimate_gauge"], (238, 130, 238))
        draw_ultimate_gauge(screen, screen.get_width() - 200, 100, p2["ultimate_gauge"], (238, 130, 238))

        # 발사체 업데이트 및 충돌
        for proj in projectiles[:]:
            if hasattr(proj, "update"):
                proj.update(world)
            else:
                proj["x"] += proj.get("vx", 0)
            # 충돌 판정 (단순 박스)
            owner = getattr(proj, "owner", proj.get("owner", None))
            x = getattr(proj, "x", proj.get("x", 0))
            y = getattr(proj, "y", proj.get("y", 0))
            dmg = getattr(proj, "damage", proj.get("damage", 0))
            active = getattr(proj, "active", proj.get("active", True))

            if not active:
                projectiles.remove(proj)
                continue

            if owner == "p1":
                if (x > p2["x"] and x < p2["x"] + 200 and y > p2["y"] and y < p2["y"] + 200):
                    deal_damage(p1, p2, dmg)
                    if hasattr(proj, "active"):
                        proj.active = False
                    else:
                        proj["active"] = False
            elif owner == "p2":
                if (x > p1["x"] and x < p1["x"] + 200 and y > p1["y"] and y < p1["y"] + 200):
                    deal_damage(p2, p1, dmg)
                    if hasattr(proj, "active"):
                        proj.active = False
                    else:
                        proj["active"] = False

            if hasattr(proj, "draw"):
                proj.draw(screen)
            else:
                img = proj.get("img")
                if img:
                    screen.blit(img, (proj["x"], proj["y"]))

            # 제거 조건
            alive = getattr(proj, "active", proj.get("active", True))
            if not alive:
                try:
                    projectiles.remove(proj)
                except ValueError:
                    pass

        # 게임오버 체크
        if p1["hp"] <= 0 or p2["hp"] <= 0:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        pygame.display.update()
        clock.tick(60)

    return "Title"