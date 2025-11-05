import pygame
import os
from typing import Optional, Dict, Any, List

class Character:
    # --- 설정 상수 ---
    BODY_SIZE = (200, 200) 
    HAND_SIZE = (200, 200) 
    
    ATTACK_DURATION_MS = 300
    ATTACK_SWING_PIXELS = 40 
    AWAKENING_ANIM_SPEED_MS = 200 
    HIT_ANIM_DURATION_MS = 150 
    # --- (설정 상수 종료) ---
    
    def __init__(self, codename: str, player_id: int, state_dict: Dict[str, Any], skill_state_dict: Dict[str, Any]):
        self.codename = codename
        self.player_id = player_id
        
        self.state = state_dict 
        self.skill_state = skill_state_dict 

        # 애니메이션 상태
        self.attack_timer = 0
        self.is_attacking = False
        self.hit_timer = 0
        
        # 📢 상태 변수
        self.is_confused = False
        self.is_frozen = False 
        
        # 💨 대시 관련 상태 변수 추가
        self.is_dashing = False
        self.dash_timer = 0
        
        if "facing_right" not in self.state:
            self.state["facing_right"] = True

        self.images = self._load_parts()

    def _safe_load_image(self, part_name: str, size: tuple) -> Optional[pygame.Surface]:
        """안전하게 이미지를 로드하고 크기를 조정합니다."""
        path = os.path.join("assets", "characters", self.codename, f"{part_name}.png")
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size) 
            return img
        except pygame.error:
            return None

    def _load_parts(self):
        """캐릭터의 모든 파트(머리, 오른손, 왼손)와 각성 헤드를 로드합니다."""
        return {
            "head": self._safe_load_image("head", self.BODY_SIZE), 
            "body": self._safe_load_image("body", self.BODY_SIZE), 
            "righthand": self._safe_load_image("righthand", self.HAND_SIZE),
            "lefthand": self._safe_load_image("lefthand", self.HAND_SIZE),
            
            "head_gak_1": self._safe_load_image("head_gak_1", self.BODY_SIZE),
            "head_gak_2": self._safe_load_image("head_gak_2", self.BODY_SIZE),
        }

    def start_attack_animation(self):
        """공격 애니메이션을 시작합니다."""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.ATTACK_DURATION_MS
            
    def start_hit_animation(self):
        """[추가] 피격 시 짧은 시각 효과를 위한 타이머를 시작합니다."""
        self.hit_timer = self.HIT_ANIM_DURATION_MS

    def start_awakening(self, duration_ms: int):
        """[추가] 각성 상태를 시작하고 종료 타이머를 설정합니다."""
        if not self.state.get("is_awakened", False):
            self.state["is_awakened"] = True
            self.state["awakening_end_time"] = pygame.time.get_ticks() + duration_ms

    def start_dash(self, dash_duration_ms: int):
        """대시 애니메이션 상태를 시작합니다."""
        self.is_dashing = True
        self.dash_timer = dash_duration_ms
        
    def update(self, dt: int, is_invincible: bool, is_confused: bool = False, is_frozen: bool = False):
        """
        캐릭터의 애니메이션 타이머 및 각성/대시 상태를 업데이트합니다.
        """
        current_time = pygame.time.get_ticks()
        
        # 📢 상태 저장
        self.is_confused = is_confused 
        self.is_frozen = is_frozen 
        
        # 1. 공격 타이머 업데이트
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_timer = 0
                
        # 2. 피격 타이머 업데이트
        if self.hit_timer > 0:
            self.hit_timer -= dt
            
        # 3. 각성 상태 타이머 업데이트
        if self.state.get("is_awakened", False) and current_time > self.state.get("awakening_end_time", 0):
            self.state["is_awakened"] = False
            self.state["awakening_end_time"] = 0 
            
        # 💨 4. 대시 타이머 업데이트
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_timer = 0

    def draw(self, screen: pygame.Surface, current_x: float, current_y: float, opponent_x: float, 
             is_invincible: bool, is_confused: bool = False, is_frozen: bool = False):
        """캐릭터의 파트를 화면에 그립니다. (머리 + 두 손)"""
        
        # 0. 방향 업데이트
        if current_x < opponent_x:
            self.state["facing_right"] = True
        elif current_x > opponent_x:
            self.state["facing_right"] = False
            
        # 0.5. 무적 깜빡임 효과
        if is_invincible and (pygame.time.get_ticks() // 100 % 2) == 0:
            return 
        
        # 1. 그릴 위치
        x, y = int(current_x), int(current_y) 
        body_width = self.BODY_SIZE[0]
        hand_width = self.HAND_SIZE[0]
        facing_right = self.state["facing_right"]
        
        # 2. 머리 이미지 결정
        main_img = self.images.get("head") or self.images.get("body") 
        
        if self.state.get("is_awakened", False) and self.codename == "haegol":
            current_time = pygame.time.get_ticks()
            frame_index = (current_time // self.AWAKENING_ANIM_SPEED_MS) % 2 
            
            if frame_index == 0:
                main_img = self.images.get("head_gak_1") or main_img
            else:
                main_img = self.images.get("head_gak_2") or main_img
        
        # 3. 머리/몸통 그리기
        if main_img:
            draw_img = main_img
            if not facing_right:
                draw_img = pygame.transform.flip(main_img, True, False)
            
            # 3.5. 피격 시 흔들림 효과
            offset_x = 0
            if self.hit_timer > 0:
                offset_x = 4 if (pygame.time.get_ticks() // 50 % 2) == 0 else -4 

            screen.blit(draw_img, (x + offset_x, y)) 
            
            # 4. 혼란 상태 오버레이
            if is_confused:
                overlay = pygame.Surface(draw_img.get_size(), pygame.SRCALPHA)
                overlay.fill((128, 0, 128, 80)) 
                screen.blit(overlay, (x + offset_x, y)) 
                
            # 5. 빙결 상태 오버레이
            if is_frozen:
                overlay = pygame.Surface(draw_img.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 191, 255, 100)) 
                screen.blit(overlay, (x + offset_x, y)) 
            
            
        # 6. 오른손/왼손 오프셋 및 스윙 계산
        
        attack_swing_offset = 0
        if self.is_attacking and not is_frozen: 
            progress = 1 - (abs(self.attack_timer - self.ATTACK_DURATION_MS / 2) / (self.ATTACK_DURATION_MS / 2))
            attack_swing_offset = self.ATTACK_SWING_PIXELS * progress 

        # --- 기본 부위별 오프셋 정의 ---
        R_BASE_OFFSET_X = 100 
        R_BASE_OFFSET_Y = 0 
        L_BASE_OFFSET_X = -100 
        L_BASE_OFFSET_Y = 0 
        
        # --- 오른손 그리기 ---
        hand_img_right = self.images["righthand"]
        if hand_img_right:
            
            draw_hand_right = hand_img_right
            if facing_right:
                hand_x = x + R_BASE_OFFSET_X + attack_swing_offset
            else:
                draw_hand_right = pygame.transform.flip(hand_img_right, True, False)
                hand_x = x + body_width - R_BASE_OFFSET_X - hand_width - attack_swing_offset
            
            hand_y = y + R_BASE_OFFSET_Y
            if not is_frozen:
                screen.blit(draw_hand_right, (int(hand_x), int(hand_y)))


        # --- 왼손 그리기 ---
        hand_img_left = self.images["lefthand"]
        if hand_img_left:
            
            draw_hand_left = hand_img_left
            if facing_right:
                hand_x_left = x + L_BASE_OFFSET_X
            else:
                draw_hand_left = pygame.transform.flip(hand_img_left, True, False)
                hand_x_left = x + body_width - L_BASE_OFFSET_X - hand_width

            hand_y_left = y + L_BASE_OFFSET_Y
            if not is_frozen:
                screen.blit(draw_hand_left, (int(hand_x_left), int(hand_y_left)))