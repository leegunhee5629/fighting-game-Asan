import pygame
from typing import Dict, Any 

import os

# scenes.characters에서 필요한 것을 임포트합니다.
from scenes.characters import character_config, character_skill_state, get_charactername_by_codename

# 사용자 요청에 따라 파일명 그대로 유지 (skills.skills_skills_loader)
from skills.skills_skills_loader import get_skills_for_character 

# skills_base에서 필요한 공용 클래스 임포트
from skills.skills_base import UltimateBeltEffect, MeleeHitbox, Projectile
# LeesaengseonBombSkill은 해당 파일에 정의되어 있으므로 여기서 가져옵니다.
from skills.leesaengseon_skills import LeesaengseonBombSkill 

# Character 클래스가 정의되어 있다고 가정
from animation import Character

pygame.mixer.init()
pygame.font.init()

# =========================================================
# 🎯 궁극기 게이지 획득 상수 정의
FIXED_ULT_GAIN_ON_HIT = 3 
FIXED_ULT_GAIN_ON_ATTACK = 5 
GAUGE_PASSIVE_GAIN_PER_MS = 1 / 1000 

# 📢 조커 상태 관련 상수
CONFUSION_DURATION_MS = 3000 # 혼란 상태 지속 시간 (skills/joker_skills.py와 일치)
MOVE_BOOST_PERCENTAGE = 0.5 # 궁극기 사용 시 이동 속도 증가율 (50%)

# 📢 디버그 상수: 충돌 박스 시각화 활성화/비활성화
DEBUG_DRAW_HITBOX = True

# 📢 캐릭터 충돌 박스 조정 상수 (기존 설정 유지)
CHAR_SIZE = 200 # 애니메이션 및 기본 캐릭터 크기 (200x200)
HITBOX_WIDTH = 160 # 실제 충돌 박스 너비
HITBOX_HEIGHT = 160 # 실제 충돌 박스 높이

# HITBOX_Y_OFFSET_FROM_IMAGE_TOP: 이미지 상단에서 충돌 박스 상단까지의 거리 (40)
HITBOX_Y_OFFSET_FROM_IMAGE_TOP = CHAR_SIZE - HITBOX_HEIGHT # 200 - 160 = 40
# X_OFFSET: 캐릭터 상태 X 값에서 충돌 박스의 시작점 (가운데 정렬)
ADJ_X_OFFSET = (CHAR_SIZE - HITBOX_WIDTH) / 2 # (200 - 160) / 2 = 20

# 📢 이미지 Y 조정 상수: 캐릭터 이미지를 수직으로 조정할 값 (픽셀 단위).
# 이 값을 늘리면 이미지가 땅 쪽으로 더 내려가 땅에 더 잘 붙습니다.
IMAGE_Y_ADJUSTMENT = 60 
# =========================================================

def gameplay(screen, map_image_path):
    # 화면 크기를 동적으로 가져옵니다 (풀스크린 대응)
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 바닥 높이 조정
    GROUND_Y = SCREEN_HEIGHT * 0.90
    
    # 무적 시간 설정 (0.5초)
    INVINCIBILITY_DURATION = 500 # ms
    
    # 초기 설정
    try:
        background = pygame.image.load(map_image_path).convert()
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception:
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.fill((0, 0, 100))

    p1_codename = character_config.get("selected_1p", "default_p1")
    p2_codename = character_config.get("selected_2p", "default_p2")
    
    # 캐릭터 초기 상태
    # initial_y는 충돌 박스 상단의 Y 좌표 (GROUND_Y - HITBOX_HEIGHT)
    initial_y = GROUND_Y - HITBOX_HEIGHT
    
    # 📢 조커 상태 변수 추가: is_confused, confusion_end_time, speed_boost_end_time
    p1 = {"x": 200, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, 
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0, 
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0}
    p2 = {"x": SCREEN_WIDTH - 400, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, 
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0,
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0}
    
    p1_skill_state = character_skill_state.get(p1_codename, {}).copy()
    p2_skill_state = character_skill_state.get(p2_codename, {}).copy()

    p1_skills = get_skills_for_character(p1_codename)
    p2_skills = get_skills_for_character(p2_codename)
    p1_skill1, p1_skill2, p1_ultimate = p1_skills
    p2_skill1, p2_skill2, p2_ultimate = p2_skills

    p1_char = Character(p1_codename, 1, p1, p1_skill_state)
    p2_char = Character(p2_codename, 2, p2, p2_skill_state)

    projectiles = []
    world = {
        "screen_width": SCREEN_WIDTH,
        "screen_height": SCREEN_HEIGHT,
        "GROUND_Y": GROUND_Y,
        "projectiles": projectiles
    }

    # 물리 상수
    BASE_SPEED = 6 # 📢 기본 속도 상수로 변경
    jump_power = -18
    gravity = 1
    
    # 폰트 로드
    try:
        font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 30)
    except Exception:
        font = pygame.font.Font(None, 30)
    
    clock = pygame.time.Clock()
    running = True
    
    # --- 헬퍼 함수 (일부 생략 및 유지) ---
    def draw_hitbox(screen, x, y, width, height, color=(255, 0, 0)):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, rect, 2)
        
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

    # 📢 혼란 상태 표시 함수 추가
    def draw_confusion_status(screen, x, y, char_state, font):
        if char_state.get("is_confused", False):
            end_time = char_state.get("confusion_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"혼란: {remaining_time_s:.1f}s", True, (128, 0, 128)) # 보라색
            # 캐릭터 이미지 중앙 상단 근처에 표시
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 30)) 

    def draw_stun_status(screen, x, y, char_state, font):
        if char_state.get("is_stunned", False):
            end_time = char_state.get("stun_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"기절: {remaining_time_s:.1f}s", True, (255, 0, 0))
            # 캐릭터 이미지 중앙 상단 근처에 표시 
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 60))
            
    def deal_damage(target_state, target_char_obj, attacker_state, damage, current_time):
        # 무적 시간 확인
        if current_time < target_state.get("invincible_end_time", 0):
            return 
            
        target_state["hp"] = max(0, target_state["hp"] - damage)
        target_char_obj.start_hit_animation()
        target_state["invincible_end_time"] = current_time + INVINCIBILITY_DURATION # 무적 시간 적용

        target_gain = FIXED_ULT_GAIN_ON_HIT 
        target_state["ultimate_gauge"] = min(100, target_state["ultimate_gauge"] + target_gain)
        
        if attacker_state:
            attacker_gain = FIXED_ULT_GAIN_ON_ATTACK
            attacker_state["ultimate_gauge"] = min(100, attacker_state["ultimate_gauge"] + attacker_gain)

    def apply_stun(defender_state, duration_ms, current_time):
        if not defender_state.get("is_stunned", False):
            defender_state["is_stunned"] = True
            defender_state["stun_end_time"] = current_time + duration_ms
            
    # --- 메인 루프 ---
    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()
        
        screen.blit(background, (0, 0))
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        # --- 상태 및 물리 업데이트 ---
        for char_state in [p1, p2]:
            # 1. 상태 해제 로직
            if char_state.get("is_stunned", False):
                if current_time > char_state["stun_end_time"]:
                    char_state["is_stunned"] = False
                    char_state["stun_end_time"] = 0
                else:
                    char_state["vx"] = 0 
            
            # 📢 혼란 상태 해제 로직
            if char_state.get("is_confused", False) and current_time > char_state["confusion_end_time"]:
                char_state["is_confused"] = False
                char_state["confusion_end_time"] = 0
                
            # 📢 이동 속도 버프 해제 로직
            if char_state.get("speed_boost_end_time", 0) > 0 and current_time > char_state["speed_boost_end_time"]:
                char_state["speed_boost_end_time"] = 0

            is_invincible = current_time < char_state.get("invincible_end_time", 0)
            char_state["is_invincible"] = is_invincible
        
        # 2. 게이지 및 이동 로직 (조커 기능 반영)
        for char_state in [p1, p2]:
            passive_gain = GAUGE_PASSIVE_GAIN_PER_MS * dt
            char_state["ultimate_gauge"] = min(100, char_state["ultimate_gauge"] + passive_gain)

        # P1 이동 처리 (혼란 및 속도 버프 적용)
        p1_speed = BASE_SPEED
        if current_time < p1.get("speed_boost_end_time", 0):
            p1_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

        if not p1.get("is_stunned", False):
            is_confused = p1.get("is_confused", False)
            
            if is_confused:
                # 📢 혼란 상태: A/D (좌/우) 반전
                if keys[pygame.K_a]: p1["vx"] = p1_speed # 오른쪽으로 이동
                elif keys[pygame.K_d]: p1["vx"] = -p1_speed # 왼쪽으로 이동
                else: p1["vx"] = 0
            else:
                # 일반 상태
                if keys[pygame.K_a]: p1["vx"] = -p1_speed
                elif keys[pygame.K_d]: p1["vx"] = p1_speed
                else: p1["vx"] = 0
            if keys[pygame.K_w] and p1["on_ground"]:
                p1["vy"] = jump_power
                p1["on_ground"] = False

        # P2 이동 처리 (혼란 및 속도 버프 적용)
        p2_speed = BASE_SPEED
        if current_time < p2.get("speed_boost_end_time", 0):
            p2_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

        if not p2.get("is_stunned", False):
            is_confused = p2.get("is_confused", False)
            
            if is_confused:
                # 📢 혼란 상태: 방향키 (좌/우) 반전
                if keys[pygame.K_LEFT]: p2["vx"] = p2_speed # 오른쪽으로 이동
                elif keys[pygame.K_RIGHT]: p2["vx"] = -p2_speed # 왼쪽으로 이동
                else: p2["vx"] = 0
            else:
                # 일반 상태
                if keys[pygame.K_LEFT]: p2["vx"] = -p2_speed
                elif keys[pygame.K_RIGHT]: p2["vx"] = p2_speed
                else: p2["vx"] = 0
            if keys[pygame.K_UP] and p2["on_ground"]:
                p2["vy"] = jump_power
                p2["on_ground"] = False


        # --- 스킬 입력 처리 (동일) ---
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


        # 물리 업데이트
        for char_state in [p1, p2]:
            char_state["vy"] += gravity
            char_state["x"] += char_state["vx"]
            char_state["y"] += char_state["vy"]
            
            # 바닥 충돌 처리 로직 (initial_y는 충돌 박스 상단 위치임)
            if char_state["y"] >= initial_y: # initial_y = GROUND_Y - HITBOX_HEIGHT
                char_state["y"] = initial_y
                char_state["vy"] = 0
                char_state["on_ground"] = True
            else:
                char_state["on_ground"] = False

            # 화면 경계 처리
            char_state["x"] = max(0, min(SCREEN_WIDTH - CHAR_SIZE, char_state["x"]))
            
        # 📢 Character 클래스 업데이트에 is_confused 상태 전달
        p1_char.update(dt, p1.get("is_invincible", False), p1.get("is_confused", False))
        p2_char.update(dt, p2.get("is_invincible", False), p2.get("is_confused", False))

        # 발사체 업데이트
        new_projectiles = []
        explosion_effects = []
        for proj in projectiles:
            proj.update(world)
            
            # Leesaengseon Bomb의 바닥 충돌 처리 로직 (기존 유지)
            is_bomb_projectile = proj.gravity != 0 and proj.damage > 0 and not hasattr(proj, 'is_gas_cloud')
            if is_bomb_projectile and proj.y + proj.size >= GROUND_Y and proj.active:
                explosion_center_x = proj.x + proj.size / 2
                explosion_center_y = GROUND_Y
                proj.active = False
                
                effect_creator = p1_skill2 if proj.owner == "p1" else p2_skill2
                
                if isinstance(effect_creator, LeesaengseonBombSkill):
                    new_effects = effect_creator.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)
                    explosion_effects.extend(new_effects)

            # 📢 문제 수정: 가스 구름이 active=False일 때만 제거합니다.
            # active=False가 아닌 이상, 투사체와 이펙트는 다음 루프에 계속 포함되어야 합니다.
            # JokerGasCloud의 update에서 지속 시간이 끝나면 active=False가 됩니다.
            # 기존의 'if hasattr(proj, 'is_gas_cloud') and proj.active == False: continue' 코드를 삭제함.

            if proj.active:
                new_projectiles.append(proj)
            
        projectiles[:] = new_projectiles
        projectiles.extend(explosion_effects)
        world["projectiles"] = projectiles

        # 실제 충돌 박스 생성
        p1_rect = pygame.Rect(p1["x"] + ADJ_X_OFFSET, p1["y"] + HITBOX_Y_OFFSET_FROM_IMAGE_TOP, HITBOX_WIDTH, HITBOX_HEIGHT)
        p2_rect = pygame.Rect(p2["x"] + ADJ_X_OFFSET, p2["y"] + HITBOX_Y_OFFSET_FROM_IMAGE_TOP, HITBOX_WIDTH, HITBOX_HEIGHT)
        
        # --- 충돌 처리 ---
        for proj in projectiles:
            proj_rect = pygame.Rect(proj.x, proj.y, proj.size, proj.size)
            
            target_char = None
            target_state = None
            attacker_state = None 
            
            if proj.owner == "p1":
                if proj_rect.colliderect(p2_rect):
                    target_char = p2_char
                    target_state = p2
                    attacker_state = p1 
            elif proj.owner == "p2":
                if proj_rect.colliderect(p1_rect):
                    target_char = p1_char
                    target_state = p1
                    attacker_state = p2 

            if target_char:
                # 📢 1. 조커 기술 2: 혼란 상태 적용 (데미지 0)
                if hasattr(proj, 'causes_confusion') and proj.causes_confusion:
                    if current_time >= target_state.get("invincible_end_time", 0):
                        target_state["is_confused"] = True
                        # JokerConfusionBullet에서 설정한 duration 사용
                        target_state["confusion_end_time"] = current_time + proj.confusion_duration_ms 
                        proj.active = False # 혼란 총알은 1회 사용 후 사라짐
                    continue # 데미지 처리를 건너뛰고 다음 투사체로 이동

                # 📢 2. 가스 궁극기 DoT 처리 (is_gas_cloud 플래그 확인)
                if hasattr(proj, 'is_gas_cloud') and proj.damage > 0:
                    if current_time >= target_state.get("invincible_end_time", 0) and \
                       current_time - proj.last_damage_time >= proj.damage_interval:
                        deal_damage(target_state, target_char, attacker_state, proj.damage, current_time)
                        proj.last_damage_time = current_time # 데미지 적용 시간 업데이트
                        # 가스 효과는 지속되므로 proj.active = False 하지 않음
                    continue # 데미지 처리를 건너뛰고 다음 투사체로 이동 (단일 충돌 아님)
                        
                # 3. 일반/기존 데미지 처리
                elif proj.damage > 0 and current_time >= target_state.get("invincible_end_time", 0):
                    
                    deal_damage(target_state, target_char, attacker_state, proj.damage, current_time) 
                    
                    if proj.stuns_target:
                        apply_stun(target_state, duration_ms=1000, current_time=current_time)
                    
                    is_persistent_proj = isinstance(proj, (MeleeHitbox, UltimateBeltEffect))
                    
                    # 일반 투사체(MeleeHitbox, UltimateBeltEffect 제외)는 충돌 시 비활성화
                    if proj.gravity == 0 and not is_persistent_proj:
                        proj.active = False
                    
                    # Leesaengseon Bomb (포물선 투사체)는 공중에서 피격 시 폭발 처리
                    elif proj.gravity != 0 and not is_persistent_proj and proj.active:
                        # JokerSpinningGun도 여기에 해당되지만, GunToss는 폭발 효과가 없으므로 Bomb만 처리
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

        # 📢 최종 수정: 캐릭터 렌더링 시 Y 위치 조정 적용
        # p1["y"]는 충돌 박스 상단 Y 좌표 (GROUND_Y - HITBOX_HEIGHT)
        # 이미지 상단 Y = p1["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT
        p1_image_y = p1["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT 
        p2_image_y = p2["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT

        p1_char.draw(screen, p1["x"], p1_image_y, p2["x"], p1.get("is_invincible", False), p1.get("is_confused", False))
        p2_char.draw(screen, p2["x"], p2_image_y, p1["x"], p2.get("is_invincible", False), p2.get("is_confused", False))

        # 디버그 충돌 박스 렌더링 (실제 충돌 영역과 일치)
        if DEBUG_DRAW_HITBOX:
            # 1. 플레이어 충돌 박스 (빨간색)
            draw_hitbox(screen, p1_rect.x, p1_rect.y, HITBOX_WIDTH, HITBOX_HEIGHT, color=(255, 0, 0))
            draw_hitbox(screen, p2_rect.x, p2_rect.y, HITBOX_WIDTH, HITBOX_HEIGHT, color=(255, 0, 0))
            
            # 2. 바닥 충돌 경계선 (노란색)
            pygame.draw.line(screen, (255, 255, 0), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)
            
            # 3. 투사체 충돌 박스 (녹색)
            for proj in projectiles:
                draw_hitbox(screen, proj.x, proj.y, proj.size, proj.size, color=(0, 255, 0))


        # UI 렌더링
        p2_ui_x = SCREEN_WIDTH - 250
        draw_hp_bar(screen, 50, 50, p1["hp"])
        draw_ultimate_gauge(screen, 50, 75, p1["ultimate_gauge"])
        draw_stun_status(screen, p1["x"], p1["y"], p1, font)
        draw_confusion_status(screen, p1["x"], p1["y"], p1, font) # 📢 혼란 상태 표시 추가
        
        draw_hp_bar(screen, p2_ui_x, 50, p2["hp"])
        draw_ultimate_gauge(screen, p2_ui_x, 75, p2["ultimate_gauge"])
        draw_stun_status(screen, p2["x"], p2["y"], p2, font)
        draw_confusion_status(screen, p2["x"], p2["y"], p2, font) # 📢 혼란 상태 표시 추가


        pygame.display.flip()
        
    return "menu"