import pygame
import typing
import sys
import os
import random 
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

# 🧙‍♀️ 마녀 궁극기 처리를 위해 PoisonPotionUltimate 임포트 (witch_skills.py에 정의되어 있다고 가정)
from skills.witch_skills import PoisonPotionUltimate

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
CONFUSION_DURATION_MS = 3000 
MOVE_BOOST_PERCENTAGE = 0.5 

# 📢 디버그 상수: 충돌 박스 시각화 활성화/비활성화
DEBUG_DRAW_HITBOX = True

# 📢 캐릭터 충돌 박스 조정 상수 (기존 설정 유지)
CHAR_SIZE = 200 
HITBOX_WIDTH = 160 
HITBOX_HEIGHT = 160 

HITBOX_Y_OFFSET_FROM_IMAGE_TOP = CHAR_SIZE - HITBOX_HEIGHT 
ADJ_X_OFFSET = (CHAR_SIZE - HITBOX_WIDTH) / 2 

IMAGE_Y_ADJUSTMENT = 60 

# 📢 룰렛 관련 상수 추가
ROULETTE_SPIN_DURATION_MS = 3000  # 룰렛이 멈추는 데 걸리는 최소 시간 (3초)
ROULETTE_MAX_SPEED = 10          # 최대 회전 속도 (각도/프레임)
# =========================================================

def gameplay(screen, map_image_path):
    # 🌟 UnboundLocalError 해결 및 전역 변수 참조 제거 (로컬 변수로 충분)
    
    # 📢 [수정]: 마우스 포인터를 보이게 설정
    pygame.mouse.set_visible(True) 

    # 화면 크기를 동적으로 가져옵니다
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
    initial_y = GROUND_Y - HITBOX_HEIGHT
    
    p1 = {"x": 200, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, "max_hp": 100,
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0, 
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0, 
          "is_frozen": False, "frozen_end_time": 0, 
          "is_dashing": False, "dash_end_time": 0, "last_input_key": None,
          "status_effects": []} 
    p2 = {"x": SCREEN_WIDTH - 400, "y": initial_y, "vx": 0, "vy": 0, "on_ground": True, "hp": 100, "ultimate_gauge": 0, "max_hp": 100,
          "is_stunned": False, "stun_end_time": 0, "invincible_end_time": 0,
          "is_confused": False, "confusion_end_time": 0, "speed_boost_end_time": 0,
          "is_frozen": False, "frozen_end_time": 0,
          "is_dashing": False, "dash_end_time": 0, "last_input_key": None,
          "status_effects": []} 
    
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
    BASE_SPEED = 6 
    jump_power = -18
    gravity = 1
    
    # 폰트 로드
    try:
        font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 30)
        large_font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 60)
    except Exception:
        font = pygame.font.Font(None, 30)
        large_font = pygame.font.Font(None, 60)
        
    # 룰렛 이미지 로드 
    # 📢 [수정]: 룰렛 이미지 경로를 'assets/img'로 변경
    try:
        roulette_img = pygame.image.load(os.path.join("assets", "img", "roulette.png")).convert_alpha()
        roulette_pin_img = pygame.image.load(os.path.join("assets", "img", "pin.png")).convert_alpha()
        
        # 룰렛 크기 조정 (화면 너비의 약 40%)
        roulette_size = int(SCREEN_WIDTH * 0.4)
        roulette_img = pygame.transform.scale(roulette_img, (roulette_size, roulette_size))
        # 핀 크기 조정 (룰렛 크기의 약 10%)
        pin_size = int(roulette_size * 0.1)
        roulette_pin_img = pygame.transform.scale(roulette_pin_img, (pin_size, pin_size))
        
    except Exception:
        # 이미지 로드 실패 시 대체
        roulette_size = 300
        pin_size = 30
        roulette_img = pygame.Surface((roulette_size, roulette_size))
        roulette_img.fill((255, 255, 0)) # 노란색
        roulette_pin_img = pygame.Surface((pin_size, pin_size))
        roulette_pin_img.fill((0, 0, 0)) # 검은색
        
    # 룰렛 버튼 위치 정의 (클릭 체크 및 렌더링에 사용)
    BUTTON_WIDTH = 300
    BUTTON_HEIGHT = 60
    BUTTON_CENTER_Y = SCREEN_HEIGHT * 0.75
    BUTTON_CENTER_X = SCREEN_WIDTH // 2
    
    # 룰렛 돌리기 버튼 Rect
    roulette_spin_button_rect = pygame.Rect(
        BUTTON_CENTER_X - BUTTON_WIDTH // 2, 
        BUTTON_CENTER_Y - BUTTON_HEIGHT // 2, 
        BUTTON_WIDTH, 
        BUTTON_HEIGHT
    )
    
    # 다시 시작 버튼 Rect (위치 동일)
    restart_button_rect = roulette_spin_button_rect 

    # 게임 상태 변수
    game_state = "RUNNING" # RUNNING, ENDED, ROULETTE_SETUP, ROULETTE_SPINNING, ROULETTE_STOPPED
    winner_codename = None
    
    # 룰렛 상태 변수
    roulette_angle = 0.0
    roulette_speed = 0.0
    roulette_start_time = 0
    roulette_target_angle = 0
    
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

    def draw_confusion_status(screen, x, y, char_state, font):
        if char_state.get("is_confused", False):
            end_time = char_state.get("confusion_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"혼란: {remaining_time_s:.1f}s", True, (128, 0, 128)) # 보라색
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 30)) 

    def draw_stun_status(screen, x, y, char_state, font):
        if char_state.get("is_stunned", False):
            end_time = char_state.get("stun_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"기절: {remaining_time_s:.1f}s", True, (255, 0, 0))
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 60))
    
    def draw_frozen_status(screen, x, y, char_state, font):
        if char_state.get("is_frozen", False):
            end_time = char_state.get("frozen_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"빙결: {remaining_time_s:.1f}s", True, (0, 191, 255)) # 하늘색
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 90)) 

    def draw_poison_status(screen, x, y, char_state, font):
        is_poisoned = any(eff.get("type") == "poison" for eff in char_state.get("status_effects", []))
        if is_poisoned:
            poison_effect = next((eff for eff in char_state["status_effects"] if eff["type"] == "poison"), None)
            end_time = poison_effect.get("expires_at", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000

            text = font.render(f"독: {remaining_time_s:.1f}s", True, (0, 150, 0)) # 독 상태: 녹색
            screen.blit(text, (x + CHAR_SIZE // 2 - text.get_width() // 2, y + HITBOX_Y_OFFSET_FROM_IMAGE_TOP - 120))
            
    # 📢 텍스트 중앙 정렬 헬퍼
    def draw_text(screen, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x - text_surface.get_width() // 2, y - text_surface.get_height() // 2))

    # 📢 버튼 렌더링 헬퍼 (클릭 체크는 이제 외부 Rect를 사용)
    def create_button(text, rect: pygame.Rect, font):
        x = rect.centerx
        y = rect.centery
        
        # 룰렛 상태에서 마우스 오버 확인
        is_hover = rect.collidepoint(pygame.mouse.get_pos())
        
        button_color = (0, 150, 0) if is_hover else (0, 100, 0) # 어두운 녹색
        text_color = (255, 255, 255)
        
        # 버튼 그리기
        pygame.draw.rect(screen, button_color, rect, 0, 5) # 둥근 모서리
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, 5) # 테두리
        
        draw_text(screen, text, font, text_color, x, y)
        
        return rect, is_hover
        
    # 📢 룰렛 렌더링 헬퍼
    def draw_roulette(screen, angle, roulette_img, pin_img):
        # 룰렛 이미지 회전
        rotated_roulette = pygame.transform.rotate(roulette_img, angle)
        # 회전된 이미지의 새로운 중심을 기존 이미지의 중심과 일치시킵니다.
        new_rect = rotated_roulette.get_rect(center=roulette_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)).center)
        
        # 룰렛 렌더링
        screen.blit(rotated_roulette, new_rect)
        
        # 핀 고정 렌더링 (룰렛 중앙 상단에 위치)
        pin_x = SCREEN_WIDTH // 2
        pin_y = SCREEN_HEIGHT // 2 - roulette_size // 2
        screen.blit(pin_img, (pin_x - pin_size // 2, pin_y))


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

    def apply_freeze(defender_state, duration_ms, current_time):
        if not defender_state.get("is_frozen", False):
            defender_state["is_frozen"] = True
            defender_state["frozen_end_time"] = current_time + duration_ms
            
    def apply_poison_to_target(target: dict, source_obj) -> None:
        """독 속성이 있는 객체(투사체/히트박스)와 충돌 시 target에 독 상태효과로 등록."""
        
        if not getattr(source_obj, "causes_poison", False):
            return
            
        duration_ms = getattr(source_obj, "poison_duration", 2000)
        poison_dps = getattr(source_obj, "poison_dps", 0.015) 
        now = pygame.time.get_ticks()
        
        target.setdefault("status_effects", [])
        
        existing_poison = next((eff for eff in target["status_effects"] if eff["type"] == "poison"), None)
        
        if existing_poison:
            existing_poison["expires_at"] = now + int(duration_ms)
            existing_poison["dps"] = float(poison_dps) 
        else:
            target["status_effects"].append({
                "type": "poison",
                "started_at": now,
                "expires_at": now + int(duration_ms),
                "dps": float(poison_dps),
                "last_tick": now
            })

    def update_status_effects_for_entity(entity: dict) -> None:
        """프레임마다 호출: entity의 status_effects를 처리하여 연속 데미지 적용."""
        if not isinstance(entity, dict):
            return
        effects = entity.get("status_effects")
        if not effects:
            return
        now = pygame.time.get_ticks()
        new_effects = []
        for eff in effects:
            if now >= eff.get("expires_at", 0):
                continue
            if eff.get("type") == "poison":
                last = eff.get("last_tick", eff.get("started_at", now))
                elapsed_ms = now - last
                # 100ms마다 데미지 틱이 발생하도록 설정 
                if elapsed_ms >= 100: 
                    elapsed_s = elapsed_ms / 1000.0
                    max_hp = entity.get("max_hp", 100)
                    dmg = eff.get("dps", 0.0) * max_hp * 0.1 
                    entity["hp"] = max(0, entity.get("hp", 0) - int(dmg))
                    eff["last_tick"] = now
                new_effects.append(eff)
            else:
                new_effects.append(eff)
        entity["status_effects"] = new_effects
        
    # --- 메인 루프 ---
    while running:
        dt = clock.tick(60) # dt는 밀리초
        current_time = pygame.time.get_ticks()
        
        screen.blit(background, (0, 0))
        keys = pygame.key.get_pressed()

        # 📢 이벤트 루프 (게임 상태에 따라 다르게 처리)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            # RUNNING 상태에서만 키 입력 처리
            if game_state == "RUNNING" and event.type == pygame.KEYDOWN:
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

            # 룰렛/종료 화면에서의 마우스 클릭 처리
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                if game_state == "ROULETTE_SETUP":
                    # 📢 [수정]: 미리 정의된 Rect와 마우스 위치 충돌 체크
                    if roulette_spin_button_rect.collidepoint(mouse_pos):
                        game_state = "ROULETTE_SPINNING"
                        roulette_start_time = current_time
                        roulette_speed = ROULETTE_MAX_SPEED 
                        
                        roulette_target_angle = 360 * random.randint(3, 7) + random.randint(0, 359)
                        
                elif game_state == "ROULETTE_STOPPED":
                    # 📢 [수정]: '다시 시작' 버튼 클릭 시, 'Title' 씬으로 복귀
                    if restart_button_rect.collidepoint(mouse_pos):
                        return "Title" 

        # =========================================================
        # 📢 게임 상태 분기 처리 시작
        # =========================================================
        
        # --- 1. RUNNING 상태 (기존 게임 로직) ---
        if game_state == "RUNNING":
            
            # --- 상태 및 물리 업데이트 ---
            for char_state in [p1, p2]:
                
                # 🧊 빙결 상태 해제 로직 (가장 먼저 처리)
                if char_state.get("is_frozen", False):
                    if current_time > char_state["frozen_end_time"]:
                        char_state["is_frozen"] = False
                        char_state["frozen_end_time"] = 0
                    else:
                        char_state["is_stunned"] = False
                        char_state["is_confused"] = False
                        char_state["speed_boost_end_time"] = 0
                        char_state["is_dashing"] = False 
                        char_state["vx"] = 0 
                
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
                        char_state["vx"] = 0 
                
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
                
                # 🟢 독 상태 지속 데미지 업데이트
                update_status_effects_for_entity(char_state)

            # P1 이동 처리 (빙결, 스턴, 대시 상태 반영)
            p1_speed = BASE_SPEED
            if current_time < p1.get("speed_boost_end_time", 0):
                p1_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

            if not p1.get("is_stunned", False) and not p1.get("is_frozen", False) and not p1.get("is_dashing", False):
                is_confused = p1.get("is_confused", False)
                
                if is_confused:
                    if keys[pygame.K_a]: p1["vx"] = p1_speed 
                    elif keys[pygame.K_d]: p1["vx"] = -p1_speed 
                    else: p1["vx"] = 0
                else:
                    if keys[pygame.K_a]: p1["vx"] = -p1_speed
                    elif keys[pygame.K_d]: p1["vx"] = p1_speed
                    else: p1["vx"] = 0
                    
                if keys[pygame.K_w] and p1["on_ground"]:
                    p1["vy"] = jump_power
                    p1["on_ground"] = False
            elif not p1.get("is_dashing", False):
                p1["vx"] = 0 


            # P2 이동 처리 (빙결, 스턴, 대시 상태 반영)
            p2_speed = BASE_SPEED
            if current_time < p2.get("speed_boost_end_time", 0):
                p2_speed *= (1.0 + MOVE_BOOST_PERCENTAGE)

            if not p2.get("is_stunned", False) and not p2.get("is_frozen", False) and not p2.get("is_dashing", False):
                is_confused = p2.get("is_confused", False)
                
                if is_confused:
                    if keys[pygame.K_LEFT]: p2["vx"] = p2_speed 
                    elif keys[pygame.K_RIGHT]: p2["vx"] = -p2_speed 
                    else: p2["vx"] = 0
                else:
                    if keys[pygame.K_LEFT]: p2["vx"] = -p2_speed
                    elif keys[pygame.K_RIGHT]: p2["vx"] = p2_speed
                    else: p2["vx"] = 0
                    
                if keys[pygame.K_UP] and p2["on_ground"]:
                    p2["vy"] = jump_power
                    p2["on_ground"] = False
            elif not p2.get("is_dashing", False):
                p2["vx"] = 0 


            # --- 스킬 입력 처리 (빙결/스턴 상태 반영) ---
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


            # --- 스킬 지속 시간/단계 업데이트 루프 ---
            ult_objects = {"p1": p1_ultimate, "p2": p2_ultimate}
            ult_states = {"p1": p1_skill_state.get("ultimate", {}), "p2": p2_skill_state.get("ultimate", {})}
            char_states = {"p1": p1, "p2": p2}
            
            new_projectiles_from_skills = []
            for owner_key, ult_obj in ult_objects.items():
                ult_state = ult_states[owner_key]
                char_state = char_states[owner_key]
                
                if isinstance(ult_obj, UltimateSkillBase) and ult_state.get("is_active"):
                    ult_result = ult_obj.update(dt, world, char_state, ult_state, owner=owner_key)
                    new_projectiles_from_skills.extend(ult_result)
                    if owner_key == "p1":
                        p1_skill_state["ultimate"] = ult_state
                    else:
                        p2_skill_state["ultimate"] = ult_state
                        
            projectiles.extend(new_projectiles_from_skills) 


            # 물리 업데이트
            for char_state in [p1, p2]:
                
                if char_state.get("is_dashing", False) and not char_state.get("is_frozen", False):
                    char_state["x"] += char_state["vx"] * (dt / 1000)
                else:
                    char_state["vy"] += gravity
                    char_state["x"] += char_state["vx"]
                
                char_state["y"] += char_state["vy"]
                
                if char_state["y"] >= initial_y: 
                    char_state["y"] = initial_y
                    char_state["vy"] = 0
                    char_state["on_ground"] = True
                else:
                    char_state["on_ground"] = False

                char_state["x"] = max(0, min(SCREEN_WIDTH - CHAR_SIZE, char_state["x"]))
                
            p1_char.update(dt, p1.get("is_invincible", False), p1.get("is_confused", False), p1.get("is_frozen", False))
            p2_char.update(dt, p2.get("is_invincible", False), p2.get("is_confused", False), p2.get("is_frozen", False))

            # 발사체 업데이트
            new_projectiles = []
            explosion_effects = []
            for proj in projectiles:
                
                if hasattr(proj, 'attached_to_char') and proj.attached_to_char in ["p1", "p2"]:
                    owner_key = proj.attached_to_char
                    owner_state = p1 if owner_key == "p1" else p2
                    
                    if owner_state.get("is_dashing", False):
                        # CHAR_SIZE는 위에서 정의된 200
                        is_facing_right = owner_state.get("last_input_key") in ['d', 'D', 'right']
                        EFFECT_SIZE = 300 
                        
                        if is_facing_right:
                            hitbox_x = owner_state["x"] + CHAR_SIZE
                        else:
                            hitbox_x = owner_state["x"] - EFFECT_SIZE
                            
                        proj.x = hitbox_x
                        proj.y = owner_state["y"]

                    elif not owner_state.get("is_frozen", False):
                        pass 
                    
                proj.update(world)
                
                # 포물선 투사체(중력 $\neq 0$)의 바닥 충돌 처리 로직 통합
                if proj.gravity != 0 and proj.damage > 0 and proj.y + proj.size >= GROUND_Y and proj.active:
                    explosion_center_x = proj.x + proj.size / 2
                    explosion_center_y = GROUND_Y
                    proj.active = False
                    
                    if hasattr(proj, 'collision_skill_instance') and isinstance(proj.collision_skill_instance, PoisonPotionUltimate):
                        new_effects = proj.collision_skill_instance.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)
                        explosion_effects.extend(new_effects)
                        
                    elif isinstance(p1_skill2 if proj.owner == "p1" else p2_skill2, LeesaengseonBombSkill):
                        effect_creator = p1_skill2 if proj.owner == "p1" else p2_skill2
                        new_effects = effect_creator.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)
                        explosion_effects.extend(new_effects)

                
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
                    if hasattr(proj, 'is_ice_block'):
                        continue
                    
                    if hasattr(proj, 'causes_confusion') and proj.causes_confusion:
                        if current_time >= target_state.get("invincible_end_time", 0):
                            target_state["is_confused"] = True
                            target_state["confusion_end_time"] = current_time + proj.confusion_duration_ms 
                            proj.active = False 
                        continue

                    if hasattr(proj, 'is_gas_cloud') and proj.damage > 0:
                        apply_poison_to_target(target_state, proj)
                        continue 
                        
                    if hasattr(proj, 'is_ultimate_area') and proj.damage > 0 and proj.active:
                        if hasattr(proj, 'hit_once_only') and proj.hit_once_only and hasattr(proj, 'hit_already') and proj.hit_already:
                            continue

                        if current_time >= target_state.get("invincible_end_time", 0):
                            deal_damage(target_state, target_char, attacker_state, proj.damage, current_time) 
                            
                            apply_freeze(target_state, proj.freeze_duration, current_time)
                            
                            ice_effect = IceBlock(
                                x=target_state["x"], 
                                y=target_state["y"], 
                                size=CHAR_SIZE, 
                                owner=proj.owner, 
                                duration_ms=proj.freeze_duration
                            )
                            projectiles.append(ice_effect)

                            if hasattr(proj, 'hit_once_only') and proj.hit_once_only:
                                proj.hit_already = True 
                                
                        continue

                    elif proj.damage > 0 and current_time >= target_state.get("invincible_end_time", 0):
                        
                        is_proj_that_explodes = (proj.gravity != 0 and not isinstance(proj, (MeleeHitbox, UltimateBeltEffect)))
                        
                        if is_proj_that_explodes:
                            explosion_center_x = proj.x + proj.size / 2
                            explosion_center_y = proj.y + proj.size / 2
                            proj.active = False

                            if hasattr(proj, 'collision_skill_instance') and isinstance(proj.collision_skill_instance, PoisonPotionUltimate):
                                new_effects = proj.collision_skill_instance.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)
                                projectiles.extend(new_effects)

                            elif isinstance(p1_skill2 if proj.owner == "p1" else p2_skill2, LeesaengseonBombSkill):
                                effect_creator = p1_skill2 if proj.owner == "p1" else p2_skill2
                                new_effects = effect_creator.create_explosion_effect(explosion_center_x, explosion_center_y, proj.owner)
                                projectiles.extend(new_effects)
                                
                            continue

                        deal_damage(target_state, target_char, attacker_state, proj.damage, current_time) 
                        
                        if hasattr(proj, 'causes_poison') and proj.causes_poison:
                            apply_poison_to_target(target_state, proj)
                        
                        if hasattr(proj, 'stuns_target') and proj.stuns_target:
                            apply_stun(target_state, duration_ms=proj.stun_duration_ms, current_time=current_time)
                        
                        is_persistent_proj = isinstance(proj, (MeleeHitbox, UltimateBeltEffect))
                        
                        if proj.gravity == 0 and not is_persistent_proj:
                            proj.active = False
                            
                            if hasattr(proj, 'collision_effect_class') and proj.collision_effect_class:
                                effect_size = getattr(proj, 'collision_effect_size', 100)
                                effect_class = proj.collision_effect_class
                                
                                effect_x = target_state["x"] + CHAR_SIZE // 2 - effect_size // 2
                                effect_y = target_state["y"] + CHAR_SIZE // 2 - effect_size // 2
                                
                                new_effect = effect_class(
                                    x=effect_x, 
                                    y=effect_y, 
                                    owner=proj.owner, 
                                    size=effect_size
                                )
                                projectiles.append(new_effect)
                            
            # --- 렌더링 ---
            
            for proj in projectiles:
                proj.draw(screen)

            p1_image_y = p1["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT 
            p2_image_y = p2["y"] - HITBOX_Y_OFFSET_FROM_IMAGE_TOP + IMAGE_Y_ADJUSTMENT

            p1_char.draw(screen, p1["x"], p1_image_y, p2["x"], p1.get("is_invincible", False), p1.get("is_confused", False), p1.get("is_frozen", False))
            p2_char.draw(screen, p2["x"], p2_image_y, p1["x"], p2.get("is_invincible", False), p2.get("is_confused", False), p2.get("is_frozen", False))

            if DEBUG_DRAW_HITBOX:
                draw_hitbox(screen, p1_rect.x, p1_rect.y, HITBOX_WIDTH, HITBOX_HEIGHT, color=(255, 0, 0))
                draw_hitbox(screen, p2_rect.x, p2_rect.y, HITBOX_WIDTH, HITBOX_HEIGHT, color=(255, 0, 0))
                
                pygame.draw.line(screen, (255, 255, 0), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)
                
                for proj in projectiles:
                    draw_hitbox(screen, proj.x, proj.y, proj.size, proj.size, color=(0, 255, 0))


            # UI 렌더링
            p2_ui_x = SCREEN_WIDTH - 250
            draw_hp_bar(screen, 50, 50, p1["hp"], p1["max_hp"])
            draw_ultimate_gauge(screen, 50, 75, p1["ultimate_gauge"])
            draw_stun_status(screen, p1["x"], p1["y"], p1, font)
            draw_confusion_status(screen, p1["x"], p1["y"], p1, font) 
            draw_frozen_status(screen, p1["x"], p1["y"], p1, font) 
            draw_poison_status(screen, p1["x"], p1["y"], p1, font) 
            
            draw_hp_bar(screen, p2_ui_x, 50, p2["hp"], p2["max_hp"])
            draw_ultimate_gauge(screen, p2_ui_x, 75, p2["ultimate_gauge"])
            draw_stun_status(screen, p2["x"], p2["y"], p2, font)
            draw_confusion_status(screen, p2["x"], p2["y"], p2, font) 
            draw_frozen_status(screen, p2["x"], p2["y"], p2, font) 
            draw_poison_status(screen, p2["x"], p2["y"], p2, font) 

            
            # 📢 승리 조건 확인
            if p1["hp"] <= 0:
                game_state = "ENDED"
                winner_codename = p2_codename
                
            elif p2["hp"] <= 0:
                game_state = "ENDED"
                winner_codename = p1_codename
                
        # --- 2. ENDED 상태 (승리 화면 표시 후 ROULETTE_SETUP으로 전환) ---
        elif game_state == "ENDED":
            winner_name = get_charactername_by_codename(winner_codename)
            draw_text(screen, f"{winner_name} 승리!", large_font, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            
            pygame.display.flip()
            pygame.time.wait(2000) 
            game_state = "ROULETTE_SETUP"


        # --- 3. ROULETTE_SETUP 상태 (룰렛과 '돌리기' 버튼 표시) ---
        elif game_state == "ROULETTE_SETUP":
            draw_text(screen, "승리 보너스 룰렛!", large_font, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.2)
            draw_roulette(screen, roulette_angle, roulette_img, roulette_pin_img)
            
            # 📢 버튼 렌더링 (create_button 함수를 통해 호버 효과 적용)
            create_button("룰렛 돌리기", roulette_spin_button_rect, font)

        
        # --- 4. ROULETTE_SPINNING 상태 (룰렛 회전 및 감속) ---
        elif game_state == "ROULETTE_SPINNING":
            
            elapsed_time = current_time - roulette_start_time
            
            total_spin_time = ROULETTE_SPIN_DURATION_MS + 2000 
            
            if elapsed_time < total_spin_time:
                deceleration_factor = max(0.0, 1.0 - (elapsed_time / total_spin_time))
                roulette_speed = ROULETTE_MAX_SPEED * deceleration_factor
            else:
                roulette_speed = 0.0
                # 📢 [수정]: 속도가 0이 되면 ROULETTE_STOPPED 상태로 전환
                if roulette_speed == 0.0:
                    game_state = "ROULETTE_STOPPED"
            
            # 📢 룰렛 각도 업데이트 (roulette_speed가 0이 아닐 때 회전)
            roulette_angle = (roulette_angle + roulette_speed * (dt / 16.66)) % 360.0

            draw_text(screen, "룰렛이 돌아가는 중...", font, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.2)
            draw_roulette(screen, roulette_angle, roulette_img, roulette_pin_img)
        
        # --- 5. ROULETTE_STOPPED 상태 (결과 및 다시 시작 버튼 표시) ---
        elif game_state == "ROULETTE_STOPPED":
            
            # 📢 [수정]: 구체적인 결과 텍스트 대신 '룰렛 종료' 텍스트 표시
            draw_text(screen, "룰렛 종료", large_font, (255, 255, 255), SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.2)
            
            draw_roulette(screen, roulette_angle, roulette_img, roulette_pin_img)
            
            # 📢 다시 시작 버튼 렌더링
            create_button("다시 시작", restart_button_rect, font)

        
        pygame.display.flip()
        
    return "Title"