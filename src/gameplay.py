import pygame
import sys
import os
from typing import Dict, Any, List, Tuple

# scenes.characters에서 필요한 것을 임포트합니다.
from scenes.characters import character_config, character_skill_state, get_charactername_by_codename

# 사용자 요청에 따라 파일명 그대로 유지 (skills.skills_skills_loader)
from skills.skills_skills_loader import get_skills_for_character 

# skills_base에서 필요한 공용 클래스 임포트
from skills.skills_base import UltimateBeltEffect, MeleeHitbox, Projectile, UltimateSkillBase
# LeesaengseonBombSkill은 해당 파일에 정의되어 있으므로 여기서 가져옵니다.
from skills.leesaengseon_skills import LeesaengseonBombSkill 
# 🧊 IcemanUltimateSkill, IceBlock 임포트 (아이스맨 궁극기 처리를 위해)
from skills.iceman_skills import IcemanUltimateSkill, IceBlock 

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
IMAGE_Y_ADJUSTMENT = 60 
# =========================================================

def gameplay(screen, map_image_path):
    # 🌟 UnboundLocalError 해결: 함수 내에서 전역 상수를 명시적으로 선언하여 접근을 보장합니다.
    global CHAR_SIZE, HITBOX_HEIGHT, HITBOX_WIDTH, HITBOX_Y_OFFSET_FROM_IMAGE_TOP, ADJ_X_OFFSET, IMAGE_Y_ADJUSTMENT 
    
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
    
    # 📢 last_input_key 필드 추가
    p1 = {"x": 200, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, 
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0, 
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0, 
          "is_frozen": False, "frozen_end_time": 0, 
          "is_dashing": False, "dash_end_time": 0, "last_input_key": None} # 💨 대시 상태 및 마지막 입력 키 추가
    p2 = {"x": SCREEN_WIDTH - 400, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, 
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0,
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0,
          "is_frozen": False, "frozen_end_time": 0,
          "is_dashing": False, "dash_end_time": 0, "last_input_key": None} # 💨 대시 상태 및 마지막 입력 키 추가
    
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
    
    # --- 헬퍼 함수 ---
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

    # 📢 혼란 상태 표시 함수 유지
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
    
    # 🧊 빙결 상태 표시 함수 추가
    def draw_frozen_status(screen, x, y, char_state, font):
        if char_state.get("is_frozen", False):
            end_time = char_state.get("frozen_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"빙결: {remaining_time_s:.1f}s", True, (0, 191, 255)) # 하늘색
            # 캐릭터 이미지 중앙 상단 근처에 표시 (혼란보다 위)
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 90)) 
            
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
        # 🧊 빙결 상태가 아닐 때만 스턴 적용
        if not defender_state.get("is_stunned", False) and not defender_state.get("is_frozen", False):
            defender_state["is_stunned"] = True
            defender_state["stun_end_time"] = current_time + duration_ms

    # 🧊 빙결 상태 적용 함수 추가
    def apply_freeze(defender_state, duration_ms, current_time):
        if not defender_state.get("is_frozen", False):
            defender_state["is_frozen"] = True
            defender_state["frozen_end_time"] = current_time + duration_ms
            
    # --- 메인 루프 ---
    while running:
        dt = clock.tick(60) # dt는 밀리초
        current_time = pygame.time.get_ticks()
        
        screen.blit(background, (0, 0))
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # --- 마지막 입력 키 업데이트 (키 다운 이벤트에서만) ---
            if event.type == pygame.KEYDOWN:
                # P1 입력
                if event.key == pygame.K_a:
                    p1["last_input_key"] = 'a'
                elif event.key == pygame.K_d:
                    p1["last_input_key"] = 'd'
                
                # P2 입력
                elif event.key == pygame.K_LEFT:
                    p2["last_input_key"] = 'left'
                elif event.key == pygame.K_RIGHT:
                    p2["last_input_key"] = 'right'
            # ----------------------------------------------------

        # --- 상태 및 물리 업데이트 ---
        for char_state in [p1, p2]:
            # 1. 상태 해제 로직
            
            # 🧊 빙결 상태 해제 로직 (가장 먼저 처리)
            if char_state.get("is_frozen", False):
                if current_time > char_state["frozen_end_time"]:
                    char_state["is_frozen"] = False
                    char_state["frozen_end_time"] = 0
                else:
                    # 빙결 상태일 때는 스턴, 혼란, 이동 속도 버프, 대시 모두 무시하며 움직임을 정지
                    char_state["is_stunned"] = False
                    char_state["is_confused"] = False
                    char_state["speed_boost_end_time"] = 0
                    char_state["is_dashing"] = False # 💨 대시 상태 강제 해제
                    char_state["vx"] = 0 # 이동 불가
            
            # 스턴 상태 해제 로직 (빙결 상태가 아닐 때만 유효)
            if char_state.get("is_stunned", False) and not char_state.get("is_frozen", False):
                if current_time > char_state["stun_end_time"]:
                    char_state["is_stunned"] = False
                    char_state["stun_end_time"] = 0
                else:
                    char_state["vx"] = 0 
            
            # 💨 대시 상태 해제 로직 (빙결 상태가 아닐 때만 유효)
            if char_state.get("is_dashing", False) and not char_state.get("is_frozen", False):
                if current_time > char_state["dash_end_time"]:
                    char_state["is_dashing"] = False
                    char_state["dash_end_time"] = 0
                    char_state["vx"] = 0 # 대시 종료 시 속도 0으로 초기화
                # 대시 중에는 키 입력 무시 (아래 입력 처리에서 분리)
            
            # 혼란 상태 해제 로직
            if char_state.get("is_confused", False) and current_time > char_state["confusion_end_time"]:
                char_state["is_confused"] = False
                char_state["confusion_end_time"] = 0
                
            # 이동 속도 버프 해제 로직
            if char_state.get("speed_boost_end_time", 0) > 0 and current_time > char_state["speed_boost_end_time"]:
                char_state["speed_boost_end_time"] = 0

            is_invincible = current_time < char_state.get("invincible_end_time", 0)
            char_state["is_invincible"] = is_invincible
        
        # 2. 게이지 및 이동 로직 (조커 및 아이스맨 기능 반영)
        for char_state in [p1, p2]:
            passive_gain = GAUGE_PASSIVE_GAIN_PER_MS * dt
            char_state["ultimate_gauge"] = min(100, char_state["ultimate_gauge"] + passive_gain)

        # P1 이동 처리 (빙결, 스턴, 대시 상태 반영)
        p1_speed = BASE_SPEED
        if current_time < p1.get("speed_boost_end_time", 0):
            p1_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

        # 🧊 빙결/스턴/대시 상태가 아닐 때만 키 입력 처리
        if not p1.get("is_stunned", False) and not p1.get("is_frozen", False) and not p1.get("is_dashing", False):
            is_confused = p1.get("is_confused", False)
            
            # 🚨 P1 이동 속도 계산 및 last_input_key 설정
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
        elif not p1.get("is_dashing", False):
            p1["vx"] = 0 # 스턴/빙결 상태일 때 움직임 정지 (대시 중이 아닐 경우)


        # P2 이동 처리 (빙결, 스턴, 대시 상태 반영)
        p2_speed = BASE_SPEED
        if current_time < p2.get("speed_boost_end_time", 0):
            p2_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

        # 🧊 빙결/스턴/대시 상태가 아닐 때만 키 입력 처리
        if not p2.get("is_stunned", False) and not p2.get("is_frozen", False) and not p2.get("is_dashing", False):
            is_confused = p2.get("is_confused", False)
            
            # 🚨 P2 이동 속도 계산 및 last_input_key 설정
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
        elif not p2.get("is_dashing", False):
            p2["vx"] = 0 # 스턴/빙결 상태일 때 움직임 정지 (대시 중이 아닐 경우)


        # --- 스킬 입력 처리 (빙결/스턴 상태 반영) ---
        # 🧊 빙결/스턴 상태일 때 스킬 입력 무시
        if not p1.get("is_stunned", False) and not p1.get("is_frozen", False):
            if keys[pygame.K_e]:
                new_projs = p1_skill1.activate(p1, p2, p1_skill_state.get("skill1", {}), world, p1_char, owner="p1")
                projectiles.extend(new_projs)
            if keys[pygame.K_r]:
                new_projs = p1_skill2.activate(p1, p2, p1_skill_state.get("skill2", {}), world, p1_char, owner="p1")
                projectiles.extend(new_projs)
            if keys[pygame.K_s]:
                new_projs = p1_ultimate.activate(p1, p2, p1_skill_state.get("ultimate", {}), world, p1_char, owner="p1")
                projectiles.extend(new_projs)
                
        # 🧊 빙결/스턴 상태일 때 스킬 입력 무시
        if not p2.get("is_stunned", False) and not p2.get("is_frozen", False):
            if keys[pygame.K_RETURN]:
                new_projs = p2_skill1.activate(p2, p1, p2_skill_state.get("skill1", {}), world, p2_char, owner="p2")
                projectiles.extend(new_projs)
            if keys[pygame.K_RSHIFT]:
                new_projs = p2_skill2.activate(p2, p1, p2_skill_state.get("skill2", {}), world, p2_char, owner="p2")
                projectiles.extend(new_projs)
            if keys[pygame.K_DOWN]:
                new_projs = p2_ultimate.activate(p2, p1, p2_skill_state.get("ultimate", {}), world, p2_char, owner="p2")
                projectiles.extend(new_projs)


        # --- [수정 1] 스킬 지속 시간/단계 업데이트 루프 추가 ---
        # 궁극기 활성화 중 1단계 -> 2단계 전환 및 기타 지속 스킬 업데이트를 처리합니다.
        ult_objects = {"p1": p1_ultimate, "p2": p2_ultimate}
        ult_states = {"p1": p1_skill_state.get("ultimate", {}), "p2": p2_skill_state.get("ultimate", {})}
        char_states = {"p1": p1, "p2": p2}
        
        new_projectiles_from_skills = []
        for owner_key, ult_obj in ult_objects.items():
            ult_state = ult_states[owner_key]
            char_state = char_states[owner_key]
            
            if isinstance(ult_obj, UltimateSkillBase) and ult_state.get("is_active"):
                # IcemanUltimateSkill.update() 호출: 1초가 지나면 ultimate_2 투사체를 반환합니다.
                ult_result = ult_obj.update(dt, world, char_state, ult_state, owner=owner_key)
                new_projectiles_from_skills.extend(ult_result)
                # 업데이트된 스킬 상태 저장 (IcemanUltimateSkill 내에서 ult2_activated가 업데이트됨)
                if owner_key == "p1":
                    p1_skill_state["ultimate"] = ult_state
                else:
                    p2_skill_state["ultimate"] = ult_state
                    
        projectiles.extend(new_projectiles_from_skills) 
        # --- [수정 1] 끝 ---


        # 물리 업데이트
        for char_state in [p1, p2]:
            
            # 💨 대시 이동 처리: 대시 중일 때는 중력/일반 이동 무시, vx는 IcemanDashSkill에서 설정된 값 사용
            if char_state.get("is_dashing", False) and not char_state.get("is_frozen", False):
                # 대시 중에는 중력이나 일반 vx 재계산을 하지 않고, 기존 vx를 사용해 이동만 합니다.
                char_state["x"] += char_state["vx"] * (dt / 1000)
            else:
                # 일반 이동/점프/낙하 처리 (대시 중이 아닐 때만)
                char_state["vy"] += gravity
                # 일반 이동 로직은 키 입력 처리에서 이미 p1["vx"] 등에 적용됨.
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
            
        # 📢 Character 클래스 업데이트에 is_confused, is_frozen 상태 전달
        p1_char.update(dt, p1.get("is_invincible", False), p1.get("is_confused", False), p1.get("is_frozen", False))
        p2_char.update(dt, p2.get("is_invincible", False), p2.get("is_confused", False), p2.get("is_frozen", False))

        # 발사체 업데이트
        new_projectiles = []
        explosion_effects = []
        for proj in projectiles:
            
            # 💨 캐릭터에 부착된 투사체 (대시 히트박스/이펙트) 위치 업데이트
            if hasattr(proj, 'attached_to_char') and proj.attached_to_char in ["p1", "p2"]:
                owner_key = proj.attached_to_char
                owner_state = p1 if owner_key == "p1" else p2
                
                # 투사체가 캐릭터의 중앙에 오도록 위치를 조정합니다.
                # 참고: IcemanDashSkill의 activate에서 위치를 히트박스 시작점에 맞추었으므로, 
                # 여기서는 위치 조정 로직을 그대로 두되, 대시 중이 아니면 움직임을 멈춥니다.
                if owner_state.get("is_dashing", False):
                    # 대시 중일 때만 위치를 업데이트합니다.
                    
                    # IcemanDashSkill의 activate에서 계산된 위치를 다시 계산하여 적용해야 합니다.
                    CHAR_SIZE = 200
                    # 대시 중에는 last_input_key가 설정되어 있다고 가정하거나, Character의 facing_right를 사용합니다.
                    is_facing_right = owner_state.get("last_input_key") in ['d', 'D', 'right']
                    # IcemanDashSkill의 effect_size는 300으로 가정
                    EFFECT_SIZE = 300 
                    
                    # 히트박스와 이펙트의 좌측 상단 위치 계산 (돌진 방향으로 오프셋)
                    if is_facing_right:
                        hitbox_x = owner_state["x"] + CHAR_SIZE
                    else:
                        hitbox_x = owner_state["x"] - EFFECT_SIZE
                        
                    proj.x = hitbox_x
                    proj.y = owner_state["y"]

                elif not owner_state.get("is_frozen", False):
                     # 대시가 끝났다면, 투사체의 active 상태는 스킬 클래스 내부 로직에 의해 관리됩니다.
                     # 여기서는 위치 업데이트를 멈춥니다.
                     pass 
                
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

            # --- [수정 2] 궁극기 2단계 수동 발동 로직 제거 ---
            # IcemanUltimateSkill의 update에서 처리되므로, 이 루프에서 제거합니다.
            
            # if proj.owner == "p1" and isinstance(p1_ultimate, IcemanUltimateSkill) and hasattr(proj, 'frame_duration_ms'):
            #     # ... (궁극기 2단계 수동 생성 로직 제거) ...
            #     pass 
            
            # elif proj.owner == "p2" and isinstance(p2_ultimate, IcemanUltimateSkill) and hasattr(proj, 'frame_duration_ms'):
            #     # ... (궁극기 2단계 수동 생성 로직 제거) ...
            #     pass
            # --- [수정 2] 끝 ---

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
                # 🧊 IceBlock 투사체는 충돌 처리를 하지 않음
                if hasattr(proj, 'is_ice_block'):
                    continue
                
                # 📢 1. 조커 기술 2: 혼란 상태 적용 (데미지 0)
                if hasattr(proj, 'causes_confusion') and proj.causes_confusion:
                    if current_time >= target_state.get("invincible_end_time", 0):
                        target_state["is_confused"] = True
                        target_state["confusion_end_time"] = current_time + proj.confusion_duration_ms 
                        proj.active = False # 혼란 총알은 1회 사용 후 사라짐
                    continue # 데미지 처리를 건너뛰고 다음 투사체로 이동

                # 📢 2. 가스 궁극기 DoT 처리 (is_gas_cloud 플래그 확인)
                if hasattr(proj, 'is_gas_cloud') and proj.damage > 0:
                    if current_time >= target_state.get("invincible_end_time", 0) and \
                             current_time - proj.last_damage_time >= proj.damage_interval:
                        deal_damage(target_state, target_char, attacker_state, proj.damage, current_time)
                        proj.last_damage_time = current_time # 데미지 적용 시간 업데이트
                    continue # 데미지 처리를 건너뛰고 다음 투사체로 이동 (단일 충돌 아님)
                    
                # 🧊 3. 아이스맨 궁극기 2단계 (광역 데미지 및 빙결)
                if hasattr(proj, 'is_ultimate_area') and proj.damage > 0 and proj.active:
                    # hit_once_only 속성을 확인하여 이미 타격했는지 확인
                    if hasattr(proj, 'hit_once_only') and proj.hit_once_only and hasattr(proj, 'hit_already') and proj.hit_already:
                         continue

                    if current_time >= target_state.get("invincible_end_time", 0):
                        deal_damage(target_state, target_char, attacker_state, proj.damage, current_time) 
                        
                        # 빙결 상태 적용
                        apply_freeze(target_state, proj.freeze_duration, current_time)
                        
                        # IceBlock 이펙트 생성 (중복 방지 로직 필요)
                        ice_effect = IceBlock(
                            x=target_state["x"], 
                            y=target_state["y"], 
                            size=CHAR_SIZE, # 캐릭터 크기와 동일하게
                            owner=proj.owner, 
                            duration_ms=proj.freeze_duration
                        )
                        projectiles.append(ice_effect)

                        # IceBlock을 생성하고 빙결을 적용했으므로, 이펙트는 한 번 타격했다고 표시
                        # hit_once_only인 경우, 이펙트의 active를 False로 설정하여 다음 프레임에 사라지게 함
                        if hasattr(proj, 'hit_once_only') and proj.hit_once_only:
                             # is_ultimate_area 이펙트가 타겟을 한 번만 타격하도록 구현해야 합니다.
                             # IcemanUltimateSkill의 update에서 생성된 ult2_effect는 hit_once_only=True입니다.
                             # 하지만 is_ultimate_area는 광역 히트박스이므로, 여기서는 해당 충돌 박스(proj)가 비활성화되면
                             # 다음 프레임에 바로 사라지게 됩니다. 
                             # 충돌 박스가 지속되어야 하므로, 충돌 박스 자체를 비활성화하는 대신 hit_already 플래그를 사용합니다.
                            # BUT! IcemanUltimateSkill.create_ult2_effect에서 hit_once_only=True로 설정했지만,
                            # 해당 이펙트는 3초간 지속되어야 합니다. 따라서 hit_once_only는 충돌 처리가 아니라
                            # **데미지/상태 이상 적용**을 한 번만 하도록 플래그로만 사용해야 합니다.
                            # 이를 위해 AnimatedEffect에 `targets_hit: list` 필드를 추가해야 하지만, 
                            # 현재 구조에서는 `proj.hit_already = True`를 통해 임시로 처리합니다. 
                            proj.hit_already = True # (이것은 임시 조치입니다. 실제로는 타겟별로 체크해야 함)
                            
                    continue

                # 4. 일반/기존 데미지 처리
                elif proj.damage > 0 and current_time >= target_state.get("invincible_end_time", 0):
                    
                    deal_damage(target_state, target_char, attacker_state, proj.damage, current_time) 
                    
                    if hasattr(proj, 'stuns_target') and proj.stuns_target:
                        apply_stun(target_state, duration_ms=proj.stun_duration_ms, current_time=current_time)
                    
                    is_persistent_proj = isinstance(proj, (MeleeHitbox, UltimateBeltEffect))
                    
                    # 일반 투사체(MeleeHitbox, UltimateBeltEffect 제외)는 충돌 시 비활성화
                    if proj.gravity == 0 and not is_persistent_proj:
                        proj.active = False
                    
                    # Leesaengseon Bomb (포물선 투사체)는 공중에서 피격 시 폭발 처리
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

        # 📢 최종 수정: 캐릭터 렌더링 시 Y 위치 조정 적용
        # pX["y"]는 충돌 박스 상단 Y 좌표 (GROUND_Y - HITBOX_HEIGHT)
        # 이미지 상단 Y = pX["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT
        p1_image_y = p1["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT 
        p2_image_y = p2["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT

        # 📢 Character 클래스 draw 호출에 is_frozen 상태 전달
        p1_char.draw(screen, p1["x"], p1_image_y, p2["x"], p1.get("is_invincible", False), p1.get("is_confused", False), p1.get("is_frozen", False))
        p2_char.draw(screen, p2["x"], p2_image_y, p1["x"], p2.get("is_invincible", False), p2.get("is_confused", False), p2.get("is_frozen", False))

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
        draw_confusion_status(screen, p1["x"], p1["y"], p1, font) 
        draw_frozen_status(screen, p1["x"], p1["y"], p1, font) # 🧊 빙결 상태 표시 추가
        
        draw_hp_bar(screen, p2_ui_x, 50, p2["hp"])
        draw_ultimate_gauge(screen, p2_ui_x, 75, p2["ultimate_gauge"])
        draw_stun_status(screen, p2["x"], p2["y"], p2, font)
        draw_confusion_status(screen, p2["x"], p2["y"], p2, font) 
        draw_frozen_status(screen, p2["x"], p2["y"], p2, font) # 🧊 빙결 상태 표시 추가


        pygame.display.flip()
        
    return "menu"