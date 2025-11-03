import pygame

import os

# scenes.characters에서 필요한 것을 임포트합니다.

from scenes.characters import character_config, character_skill_state, get_charactername_by_codename

from scenes.skills import get_skills_for_character, UltimateBeltEffect, MeleeHitbox, Projectile, LeesaengseonBombSkill



# Character 클래스가 정의되어 있다고 가정

from animation import Character



pygame.mixer.init()

pygame.font.init()



def gameplay(screen, map_image_path):

    # 화면 크기를 동적으로 가져옵니다 (풀스크린 대응)

    SCREEN_WIDTH = screen.get_width()

    SCREEN_HEIGHT = screen.get_height()

   

    # 바닥 높이 조정

    GROUND_Y = SCREEN_HEIGHT * 0.90

   

    # 캐릭터 크기 (200x200 픽셀 기준)

    CHAR_SIZE = 200

   

    # 무적 시간 설정 (0.5초)

    INVINCIBILITY_DURATION = 500 # ms

   

    # 초기 설정

    try:

        # 배경 이미지도 화면 크기에 맞춰 스케일링됩니다.

        background = pygame.image.load(map_image_path).convert()

        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

    except Exception:

        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        background.fill((0, 0, 100)) # Blue fallback



    # 📌 NameError 해결: 캐릭터 설정 로드 (41-43 라인)

    p1_codename = character_config.get("selected_1p", "default_p1") # 기본값 설정

    p2_codename = character_config.get("selected_2p", "default_p2") # 기본값 설정

   

    # 캐릭터 초기 상태

    # 초기 Y 위치 조정: GROUND_Y에서 캐릭터 높이(200)만큼 빼줍니다.

    initial_y = GROUND_Y - CHAR_SIZE

   

    p1 = {"x": 200, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0}

    p2 = {"x": SCREEN_WIDTH - 400, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0}

   

    # 스킬 상태 (쿨다운 초기화를 위해 복사본 사용)

    p1_skill_state = character_skill_state.get(p1_codename, {}).copy() # 안전하게 .get() 사용

    p2_skill_state = character_skill_state.get(p2_codename, {}).copy() # 안전하게 .get() 사용



    # 스킬 클래스 인스턴스

    p1_skills = get_skills_for_character(p1_codename)

    p2_skills = get_skills_for_character(p2_codename)

    p1_skill1, p1_skill2, p1_ultimate = p1_skills

    p2_skill1, p2_skill2, p2_ultimate = p2_skills



    # 캐릭터 애니메이션 클래스 (Character 클래스가 정의되어 있다고 가정)

    p1_char = Character(p1_codename, 1, p1, p1_skill_state)

    p2_char = Character(p2_codename, 2, p2, p2_skill_state)



    # 발사체 및 효과 리스트

    projectiles = []



    # 월드 변수

    world = {

        "screen_width": SCREEN_WIDTH,

        "screen_height": SCREEN_HEIGHT,

        "GROUND_Y": GROUND_Y,

        "projectiles": projectiles

    }



    # 물리 상수

    speed = 6

    jump_power = -18

    gravity = 1

   

    # 폰트 로드 (에러 방지용 try-except 추가)

    try:

        font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 30)

    except Exception:

        font = pygame.font.Font(None, 30)

   

    clock = pygame.time.Clock()

    running = True

   

    # --- 헬퍼 함수 (이전과 동일) ---

    def draw_hp_bar(screen, x, y, hp, max_hp=100):

        width = 200

        height = 20

        fill = (hp / max_hp) * width

        outline_rect = pygame.Rect(x, y, width, height)

        fill_rect = pygame.Rect(x, y, fill, height)

        pygame.draw.rect(screen, (255, 0, 0), fill_rect)

        pygame.draw.rect(screen, (255, 255, 255), outline_rect, 2)



    def draw_ultimate_gauge(screen, x, y, gauge, max_gauge=100):

        width = 200

        height = 10

        fill = (gauge / max_gauge) * width

        outline_rect = pygame.Rect(x, y, width, height)

        fill_rect = pygame.Rect(x, y, fill, height)

        pygame.draw.rect(screen, (0, 0, 255), fill_rect)

        pygame.draw.rect(screen, (255, 255, 255), outline_rect, 1)



    def draw_stun_status(screen, x, y, char_state, font):

        """기절 상태 타이머를 그립니다."""

        if char_state.get("is_stunned", False):

            end_time = char_state.get("stun_end_time", 0)

            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())

            remaining_time_s = remaining_time_ms / 1000

           

            text = font.render(f"기절: {remaining_time_s:.1f}s", True, (255, 0, 0)) # 빨간색

            screen.blit(text, (x, y + 50))

           

    def deal_damage(target_state, target_char_obj, damage):

        target_state["hp"] = max(0, target_state["hp"] - damage)

        target_state["ultimate_gauge"] = min(100, target_state["ultimate_gauge"] + damage)

        target_char_obj.start_hit_animation()

       

        # 타격 시 무적 시간 시작

        target_state["invincible_end_time"] = pygame.time.get_ticks() + INVINCIBILITY_DURATION



    def apply_stun(defender_state, duration_ms):

        """캐릭터에게 기절 상태를 적용하고 타이머를 설정합니다."""

        if not defender_state.get("is_stunned", False):

            defender_state["is_stunned"] = True

            defender_state["stun_end_time"] = pygame.time.get_ticks() + duration_ms



    # --- 메인 루프 ---

    while running:

        dt = clock.tick(60)

        current_time = pygame.time.get_ticks()

       

        screen.blit(background, (0, 0))

        keys = pygame.key.get_pressed()



        # 이벤트 처리

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return None



        # --- 기절 및 무적 상태 업데이트 ---

        for char_state in [p1, p2]:

            # 기절 해제 체크

            if char_state.get("is_stunned", False):

                if current_time > char_state["stun_end_time"]:

                    char_state["is_stunned"] = False

                    char_state["stun_end_time"] = 0

                else:

                    char_state["vx"] = 0 # 기절 상태에서는 이동 불가



            # 무적 상태 해제 체크

            is_invincible = current_time < char_state.get("invincible_end_time", 0)

            char_state["is_invincible"] = is_invincible



        # P1 이동 처리 (기절 상태가 아닐 때만)

        if not p1.get("is_stunned", False):

            if keys[pygame.K_a]: p1["vx"] = -speed

            elif keys[pygame.K_d]: p1["vx"] = speed

            else: p1["vx"] = 0

            if keys[pygame.K_w] and p1["on_ground"]:

                p1["vy"] = jump_power

                p1["on_ground"] = False



        # P2 이동 처리 (기절 상태가 아닐 때만)

        if not p2.get("is_stunned", False):

            if keys[pygame.K_LEFT]: p2["vx"] = -speed

            elif keys[pygame.K_RIGHT]: p2["vx"] = speed

            else: p2["vx"] = 0

            if keys[pygame.K_UP] and p2["on_ground"]:

                p2["vy"] = jump_power

                p2["on_ground"] = False



        # --- 스킬 입력 처리 (이전과 동일) ---

        if not p1.get("is_stunned", False):

            if keys[pygame.K_e]:

                new_projs = p1_skill1.activate(p1, p2, p1_skill_state.get("skill1", {}), world, p1_char, owner="p1")

                projectiles.extend(new_projs)

            if keys[pygame.K_r]:

                new_projs = p1_skill2.activate(p1, p2, p1_skill_state.get("skill2", {}), world, p1_char, owner="p1")

                projectiles.extend(new_projs)

            if keys[pygame.K_s]:

                new_projs = p1_ultimate.activate(p1, p2, p1_skill_state.get("ultimate", {}), world, p1_char, owner="p1")

                projectiles.extend(new_projs)

           

        if not p2.get("is_stunned", False):

            if keys[pygame.K_RETURN]:

                new_projs = p2_skill1.activate(p2, p1, p2_skill_state.get("skill1", {}), world, p2_char, owner="p2")

                projectiles.extend(new_projs)

            if keys[pygame.K_RSHIFT]:

                new_projs = p2_skill2.activate(p2, p1, p2_skill_state.get("skill2", {}), world, p2_char, owner="p2")

                projectiles.extend(new_projs)

            if keys[pygame.K_DOWN]:

                new_projs = p2_ultimate.activate(p2, p1, p2_skill_state.get("ultimate", {}), world, p2_char, owner="p2")

                projectiles.extend(new_projs)

        # --- (스킬 입력 처리 종료) ---





        # 물리 업데이트

        for char_state in [p1, p2]:

            char_state["vy"] += gravity

            char_state["x"] += char_state["vx"]

            char_state["y"] += char_state["vy"]

           

            # 바닥 충돌 처리 로직

            if char_state["y"] >= initial_y:

                char_state["y"] = initial_y

                char_state["vy"] = 0

                char_state["on_ground"] = True

            else:

                char_state["on_ground"] = False



            char_state["x"] = max(0, min(SCREEN_WIDTH - CHAR_SIZE, char_state["x"]))

           

        # 캐릭터 애니메이션 업데이트

        # Character 클래스가 무적 상태를 인식하고 깜빡이는 등의 시각 효과를 적용해야 합니다.

        p1_char.update(dt, p1.get("is_invincible", False))

        p2_char.update(dt, p2.get("is_invincible", False))



        # 발사체 업데이트 (이전과 동일)

        new_projectiles = []

        explosion_effects = []

        for proj in projectiles:

            proj.update(world)

           

            is_bomb_projectile = proj.gravity != 0 and proj.damage > 0

            if is_bomb_projectile and proj.y + proj.size >= GROUND_Y and proj.active:

                explosion_center_x = proj.x + proj.size / 2

                explosion_center_y = GROUND_Y

                proj.active = False

               

                effect_creator = p1_skill2 if proj.owner == "p1" else p2_skill2

               

                if isinstance(effect_creator, LeesaengseonBombSkill):

                    new_effects = effect_creator.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)

                    explosion_effects.extend(new_effects)



            if proj.active:

                new_projectiles.append(proj)

       

        projectiles[:] = new_projectiles

        projectiles.extend(explosion_effects)

        world["projectiles"] = projectiles



        # 충돌 처리

        p1_rect = pygame.Rect(p1["x"], p1["y"], CHAR_SIZE, CHAR_SIZE)

        p2_rect = pygame.Rect(p2["x"], p2["y"], CHAR_SIZE, CHAR_SIZE)

       

        for proj in projectiles:

            proj_rect = pygame.Rect(proj.x, proj.y, proj.size, proj.size)

            is_damage_dealer = proj.damage > 0

           

            target_char = None

            target_state = None

           

            if proj.owner == "p1" and proj_rect.colliderect(p2_rect):

                target_char = p2_char

                target_state = p2

            elif proj.owner == "p2" and proj_rect.colliderect(p1_rect):

                target_char = p1_char

                target_state = p1



            if target_char and is_damage_dealer:

               

                # 무적 상태 체크: 무적이 아닐 때만 데미지 적용

                if current_time >= target_state.get("invincible_end_time", 0):

                   

                    # 1. 데미지 적용 및 무적 시간 시작

                    deal_damage(target_state, target_char, proj.damage)

                   

                    # 2. 기절 적용

                    if proj.stuns_target:

                        apply_stun(target_state, duration_ms=1000)

                   

                    # 3. 투사체 제거 (지속되는 투사체 제외)

                    is_persistent_proj = isinstance(proj, (MeleeHitbox, UltimateBeltEffect))

                   

                    if proj.gravity == 0 and not is_persistent_proj:

                        proj.active = False

                       

                    # 4. 비린내 폭탄의 공중 충돌 처리 (폭발 이펙트 생성 및 제거)

                    elif proj.gravity != 0 and not is_persistent_proj and proj.active:

                        explosion_center_x = proj.x + proj.size / 2

                        explosion_center_y = proj.y + proj.size / 2

                        proj.active = False



                        effect_creator = p1_skill2 if proj.owner == "p1" else p2_skill2

                       

                        if isinstance(effect_creator, LeesaengseonBombSkill):

                            new_effects = effect_creator.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)

                            projectiles.extend(new_effects)





        # --- 렌더링 ---

       

        # 발사체 및 이펙트 렌더링

        for proj in projectiles:

            proj.draw(screen)



        # 캐릭터 렌더링

        # Character 클래스가 무적 상태를 받아 시각 효과를 적용해야 합니다.

        p1_char.draw(screen, p1["x"], p1["y"], p2["x"], p1.get("is_invincible", False))

        p2_char.draw(screen, p2["x"], p2["y"], p1["x"], p2.get("is_invincible", False))



        # UI 렌더링

       

        # P1 UI (왼쪽 상단)

        draw_hp_bar(screen, 50, 50, p1["hp"])

        draw_ultimate_gauge(screen, 50, 75, p1["ultimate_gauge"])

        draw_stun_status(screen, p1["x"], p1["y"], p1, font)

       

        # P2 UI (오른쪽 상단)

        p2_ui_x = SCREEN_WIDTH - 250 # 200 너비 바 + 50 오른쪽 여백

        draw_hp_bar(screen, p2_ui_x, 50, p2["hp"])

        draw_ultimate_gauge(screen, p2_ui_x, 75, p2["ultimate_gauge"])

        draw_stun_status(screen, p2["x"], p2["y"], p2, font)





        pygame.display.flip()

       

    return "menu"