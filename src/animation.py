import pygame
import os
from typing import Optional, Dict, Any, List

class Character:
    # --- 설정 상수 ---
    # 📌 이 크기를 변경하면 모든 부위가 이 크기에 맞춰 조정됩니다.
    BODY_SIZE = (200, 200) 
    # ➡️ 요청에 따라 머리/몸통과 같은 크기로 설정하여 손 크기를 키웠습니다.
    HAND_SIZE = (200, 200) 
    
    ATTACK_DURATION_MS = 300
    ATTACK_SWING_PIXELS = 40 # 공격 시 최대 손 전진 거리
    AWAKENING_ANIM_SPEED_MS = 200 # 각성 시 프레임 전환 속도
    HIT_ANIM_DURATION_MS = 150 # 피격 시 짧은 애니메이션/깜빡임 시간
    # --- (설정 상수 종료) ---
    
    # 📌 __init__ 시그니처 수정: gameplay.py에서 전달하는 4개의 인자를 받도록 변경
    def __init__(self, codename: str, player_id: int, state_dict: Dict[str, Any], skill_state_dict: Dict[str, Any]):
        self.codename = codename
        self.player_id = player_id
        
        # NOTE: self.state는 gameplay.py에서 전달된 딕셔너리를 직접 참조합니다.
        # 이 객체는 애니메이션 및 시각적 정보만 관리하며, 물리 상태는 외부에서 관리됩니다.
        self.state = state_dict 
        self.skill_state = skill_state_dict # 스킬 상태도 저장

        # 애니메이션 상태
        self.attack_timer = 0
        self.is_attacking = False
        self.hit_timer = 0 # 피격 애니메이션 타이머 추가
        
        # 📢 혼란 상태 저장을 위한 변수 (gameplay.py에서 전달받아 사용)
        self.is_confused = False

        # facing_right, is_awakened 등은 이제 self.state 딕셔너리에 포함되어야 하지만,
        # 기존 코드 호환성을 위해 self.state에 없는 경우 기본값을 설정합니다.
        if "facing_right" not in self.state:
            self.state["facing_right"] = True

        # 이미지 로드 (head, body, hands, awakened heads)
        self.images = self._load_parts()

    def _safe_load_image(self, part_name: str, size: tuple) -> Optional[pygame.Surface]:
        """안전하게 이미지를 로드하고 크기를 조정합니다."""
        path = os.path.join("assets", "characters", self.codename, f"{part_name}.png")
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            # 📌 로드 시 고정된 상수 크기로 스케일링
            img = pygame.transform.scale(img, size) 
            return img
        except pygame.error:
            return None

    def _load_parts(self):
        """캐릭터의 모든 파트(머리, 오른손, 왼손)와 각성 헤드를 로드합니다."""
        # BODY_SIZE를 head와 body에 사용, HAND_SIZE를 손에 사용
        return {
            # 기본 부위
            "head": self._safe_load_image("head", self.BODY_SIZE), # ⬅️ 모든 캐릭터 head.png 사용
            "body": self._safe_load_image("body", self.BODY_SIZE), # 몸통은 예비용
            "righthand": self._safe_load_image("righthand", self.HAND_SIZE),
            "lefthand": self._safe_load_image("lefthand", self.HAND_SIZE),
            
            # 각성 헤드 애니메이션 프레임 (haegol 전용이라 가정)
            "head_gak_1": self._safe_load_image("head_gak_1", self.BODY_SIZE),
            "head_gak_2": self._safe_load_image("head_gak_2", self.BODY_SIZE),
            
            # 🚨 joker_face 로직 삭제
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

    # ✅ TypeError 해결: is_confused 인자 추가
    def update(self, dt: int, is_invincible: bool, is_confused: bool = False):
        """
        캐릭터의 애니메이션 타이머 및 각성 상태를 업데이트합니다. 
        is_confused 상태를 내부적으로 저장합니다.
        """
        current_time = pygame.time.get_ticks()
        
        # 📢 혼란 상태 저장
        self.is_confused = is_confused 
        
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
            
        # 4. 방향 업데이트 (draw에서 처리하므로 여기서는 생략)

    # ✅ is_confused 인자 추가 및 처리
    def draw(self, screen: pygame.Surface, current_x: float, current_y: float, opponent_x: float, is_invincible: bool, is_confused: bool = False):
        """캐릭터의 파트를 화면에 그립니다. (머리 + 두 손)"""
        
        # 0. 방향 업데이트: 상대방 위치를 기준으로 방향을 결정합니다.
        if current_x < opponent_x:
            self.state["facing_right"] = True
        elif current_x > opponent_x:
            self.state["facing_right"] = False
            
        # 0.5. 무적 깜빡임 효과 (무적 상태 + 깜빡임 주기에 해당하면 그리지 않음)
        if is_invincible and (pygame.time.get_ticks() // 100 % 2) == 0:
            return 
        
        # 1. 그릴 위치 (캐릭터 바운딩 박스 좌상단)
        x, y = int(current_x), int(current_y) # 전달받은 최신 위치 사용
        body_width = self.BODY_SIZE[0]
        hand_width = self.HAND_SIZE[0]
        facing_right = self.state["facing_right"]
        
        # 2. 머리 이미지 결정 (각성 애니메이션 적용)
        # 🚨 수정: 모든 캐릭터는 head.png 또는 body.png 사용
        main_img = self.images.get("head") or self.images.get("body") 
        
        if self.state.get("is_awakened", False) and self.codename == "haegol":
            current_time = pygame.time.get_ticks()
            # AWAKENING_ANIM_SPEED_MS 주기로 프레임 전환
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
            
            # 3.5. 피격 시 흔들림 효과 (hit_timer가 활성화된 경우)
            offset_x = 0
            if self.hit_timer > 0:
                # 5ms마다 4픽셀 좌우로 흔들림
                offset_x = 4 if (pygame.time.get_ticks() // 50 % 2) == 0 else -4 

            screen.blit(draw_img, (x + offset_x, y)) # (x, y)는 전체 캐릭터 박스의 좌상단
            
            # 🚨 4. 혼란 상태 오버레이 (캐릭터를 그린 후 덮어씀)
            if is_confused:
                overlay = pygame.Surface(draw_img.get_size(), pygame.SRCALPHA)
                # 은은한 보라색 (128, 0, 128)에 투명도(alpha) 80 적용
                overlay.fill((128, 0, 128, 80)) 
                screen.blit(overlay, (x + offset_x, y)) 
            
            
        # 5. 오른손/왼손 오프셋 및 스윙 계산
        
        # 공격 스윙 계산 (0 -> 최고점 -> 0)
        attack_swing_offset = 0
        if self.is_attacking:
            # 0 (시작) -> ATTACK_DURATION_MS / 2 (최고) -> 0 (종료)
            progress = 1 - (abs(self.attack_timer - self.ATTACK_DURATION_MS / 2) / (self.ATTACK_DURATION_MS / 2))
            attack_swing_offset = self.ATTACK_SWING_PIXELS * progress 

        # --- 기본 부위별 오프셋 정의 ---
        R_BASE_OFFSET_X = 100 
        R_BASE_OFFSET_Y = 0 
        L_BASE_OFFSET_X = -100 
        L_BASE_OFFSET_Y = 0 
        
        # --- 오른손 그리기 (공격 애니메이션 적용) ---
        hand_img_right = self.images["righthand"]
        if hand_img_right:
            
            draw_hand_right = hand_img_right
            if facing_right:
                # 오른쪽 바라볼 때: 오른손은 오른쪽에
                hand_x = x + R_BASE_OFFSET_X + attack_swing_offset
            else:
                # 왼쪽 바라볼 때: 오른손은 왼쪽에 배치. 이미지 뒤집기
                draw_hand_right = pygame.transform.flip(hand_img_right, True, False)
                hand_x = x + body_width - R_BASE_OFFSET_X - hand_width - attack_swing_offset
            
            hand_y = y + R_BASE_OFFSET_Y
            screen.blit(draw_hand_right, (int(hand_x), int(hand_y)))


        # --- 왼손 그리기 (정적 위치) ---
        hand_img_left = self.images["lefthand"]
        if hand_img_left:
            
            draw_hand_left = hand_img_left
            if facing_right:
                # 오른쪽 바라볼 때: 왼손은 왼쪽에 
                hand_x_left = x + L_BASE_OFFSET_X
            else:
                # 왼쪽 바라볼 때: 왼손은 오른쪽에 배치. 이미지 뒤집기
                draw_hand_left = pygame.transform.flip(hand_img_left, True, False)
                hand_x_left = x + body_width - L_BASE_OFFSET_X - hand_width

            hand_y_left = y + L_BASE_OFFSET_Y
            screen.blit(draw_hand_left, (int(hand_x_left), int(hand_y_left)))