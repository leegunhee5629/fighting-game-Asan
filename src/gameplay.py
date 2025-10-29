import pygame
from scenes.characters import character_config, character_skill, character_skill_state # 캐릭터 선택 정보를 불러옵니다.
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
            gauge=max(0, min(100, gauge))
            pygame.draw.rect(screen, (128, 128 ,128), (x, y, 100, 10))
            pygame.draw.rect(screen, color, (x, y, gauge, 10))
    # 데미지 처리
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

        # 1P 기술
        if keys[pygame.K_e]:
            selected_1p = character_config["selected_1p"]
            skill_state = character_skill_state[selected_1p]["skill1"]
            if selected_1p == "haegol":
                 p1_skill1(p1, p2, p1_skill_state["skill1"], bones, owner="p1")
            else:
                 p1_skill1(p1, p2, p1_skill_state["skill1"])
        if keys[pygame.K_r]:
            pass
        #궁극기
        if keys[pygame.K_s] and p1["ultimate_gauge"] >= 100:
            pass #궁쓰고 나서 얼티게이지 0으로 초기화 하는 코드넣기

        # 2P 기술
        if keys[pygame.K_RETURN]:
            selected_2p = character_config["selected_2p"]
            skill_state = character_skill_state[selected_2p]["skill1"]
            if selected_2p == "haegol":
                p2_skill1(p2, p1, p2_skill_state["skill1"], bones, owner="p2")
            else:
                p2_skill1(p2, p1, p2_skill_state["skill1"])

        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            pass
        #궁극기
        if keys[pygame.K_DOWN] and p2["ultimate_gauge"] >= 100:
            pass #궁쓰고 나서 얼티게이지 0으로 초기화 하는 코드넣기
               
        # 캐릭터 위치 업데이트 (중력 적용)
        for p in [p1, p2]:
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

    
        # 뼈 스킬 발사체
        if bones:
            for bone in bones[:]:
                if not bone["active"]:
                    bones.remove(bone)
                    continue
                bone["x"] += bone["vx"]

                hit_margin = 30

                if bone["owner"] == "p1": 
                   if (bone["x"] > p2["x"] and bone["x"] < p2["x"] + 200 and
                      bone["y"] > p2["y"] and bone["y"] < p2["y"] + 200):
                      deal_damage(p1, p2, bone["damage"])
                      bone["active"] = False

                elif bone["owner"] == "p2":
                    if (bone["x"] > p1["x"] and bone["x"] < p1["x"] + 200 and
                        bone["y"] > p1["y"] and bone["y"] < p1["y"] + 200):
                        deal_damage(p2, p1, bone["damage"])
                        bone["active"] = False   

                screen.blit(bone["img"], (bone["x"], bone["y"]))

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