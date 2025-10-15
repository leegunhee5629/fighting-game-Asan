import pygame
from scenes.characters import character_config  # 캐릭터 선택 정보를 불러옵니다.

def gameplay(screen, map_image_path):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - Gameplay")
    background = pygame.image.load(map_image_path)
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))

    # 캐릭터 이미지 불러오기
    p1_img = pygame.image.load(f"assets/characters/{character_config['selected_1p']}/body.png").convert_alpha()
    p2_img = pygame.image.load(f"assets/characters/{character_config['selected_2p']}/body.png").convert_alpha()
    p1_img = pygame.transform.scale(p1_img, (200, 200))
    p2_img = pygame.transform.scale(p2_img, (200, 200))

    # 캐릭터 초기 위치 및 속도
    p1 = {"x": 100, "y": 500, "vx": 0, "vy": 0, "on_ground": True}
    p2 = {"x": 1260, "y": 500, "vx": 0, "vy": 0, "on_ground": True}
    speed = 6
    jump_power = -18
    gravity = 1

    running = True
    clock = pygame.time.Clock()

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
            pass
        if keys[pygame.K_r]:
            pass
        if keys[pygame.K_s]:
            pass

        # 2P 기술
        if keys[pygame.K_RETURN]:
            pass
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            pass
        if keys[pygame.K_DOWN]:
            pass

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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        pygame.display.update()
        clock.tick(60)

    return "Title"