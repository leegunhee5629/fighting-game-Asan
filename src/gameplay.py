import pygame
from scenes.characters import character_config, character_skill, character_skill_state # 캐릭터 선택 정보를 불러옵니다.
import copy

def gameplay(screen, map_image_path):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - Gameplay")
    background = pygame.image.load(map_image_path)
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))

    # 캐릭터 이미지 불러오기
    p1_img = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/body.png").convert_alpha()
    p2_img = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/body.png").convert_alpha()
    p1_img = pygame.transform.scale(p1_img, (200, 200))
    p2_img = pygame.transform.scale(p2_img, (200, 200))
    
    #스킬 이미지 불러오기
    p1_skill1_img = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/skill1.png").convert_alpha()
    p2_skill1_img = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/skill1.png").convert_alpha()
    p1_skill1_img = pygame.transform.scale(p1_skill1_img, (50, 50))
    p2_skill1_img = pygame.transform.scale(p2_skill1_img, (50, 50))

    #궁극기 이미지 불러오기
    p1_ultimate_img = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/ultimate.png").convert_alpha()
    p2_ultimate_img = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/ultimate.png").convert_alpha()
    p1_ultimate_img = pygame.transform.scale(p1_ultimate_img, (50, 50))
    p2_ultimate_img = pygame.transform.scale(p2_ultimate_img, (50, 50))
    
    #스킬 가져오기
    selected_1p = character_config["selected_1p"]
    p1_skill1 = character_skill[selected_1p][0]
    p1_skill2 = character_skill[selected_1p][1]
    p1_ultimate = character_skill[selected_1p][2]

    selected_2p = character_config["selected_2p"]
    p2_skill1 = character_skill[selected_2p][0]
    p2_skill2 = character_skill[selected_2p][1]
    p2_ultimate = character_skill[selected_2p][2]

    bones = []

    p1_skill_state = copy.deepcopy(character_skill_state[character_config["selected_1p"]])
    p2_skill_state = copy.deepcopy(character_skill_state[character_config["selected_2p"]])
    # 캐릭터 초기 위치 및 속도 Hp 
    p1 = {"x": 100, "y": 500, "vx": 0, "vy": 0, "on_ground": True, "hp":100, "ultimate_gauge": 0}
    p2 = {"x": 1260, "y": 500, "vx": 0, "vy": 0, "on_ground": True, "hp":100, "ultimate_gauge": 0}
    speed = 6
    jump_power = -18
    gravity = 1

    running = True
    clock = pygame.time.Clock()


    # 체력바 
    def draw_hp_bar(screen, x, y, hp, color):
            hp=max(0, min(100, hp))
            pygame.draw.rect(screen, (255, 0 ,0), (x, y, 100, 10))
            pygame.draw.rect(screen, color, (x, y, hp, 10))
    # 궁 게이지
    def draw_ultimate_gauge(screen, x, y, gauge, color):
            gauge=max(0, min(100, gauge))
            pygame.draw.rect(screen, (128, 128 ,128), (x, y, 100, 10))
            pygame.draw.rect(screen, color, (x, y, gauge, 10))
    # 데미지 처리
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




    while running:
        screen.blit(background, (0, 0))

        keys = pygame.key.get_pressed()

        # 1P 이동
        if keys[pygame.K_a]:
            p1["vx"] = -speed
        elif keys[pygame.K_d]:
            p1["vx"] = speed
        else:
            p1["vx"] = 0

        if keys[pygame.K_w] and p1["on_ground"]:
            p1["vy"] = jump_power
            p1["on_ground"] = False

        # 2P 이동
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
                
            # 벽에 닿으면 튕기기
            if p["x"] <= 0:
                p["x"] = 0
                p["vx"] = abs(p["vx"])
            elif p["x"] >= screen.get_width() - 200:  # 200은 캐릭터 이미지 크기
                p["x"] = screen.get_width() - 200
                p["vx"] = -abs(p["vx"])

        # 캐릭터 이미지 그리기
        screen.blit(p1_img, (int(p1["x"]), int(p1["y"])))
        screen.blit(p2_img, (int(p2["x"]), int(p2["y"])))

        # 체력바 그리기
        draw_hp_bar(screen, 100, 50, p1["hp"], (0, 255, 0))
        draw_hp_bar(screen, 1350, 50, p2["hp"], (0, 255, 0))
        draw_ultimate_gauge(screen, 100, 100, p1["ultimate_gauge"], (238, 130, 238))
        draw_ultimate_gauge(screen, 1350, 100, p2["ultimate_gauge"], (238, 130, 238))

    
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

            # 임시 게임오버
                if p1["hp"] <= 0 or p2["hp"] <= 0:
                    running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None







        pygame.display.update()
        clock.tick(60)

    return "Title"