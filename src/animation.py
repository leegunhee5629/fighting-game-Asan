import pygame
import os
from typing import Optional, Dict, Any, List # List, Dict, Any 타입 힌트 추가

class Character:
    # 캐릭터 파트 크기 정의
    BODY_SIZE = (200, 200)
    HAND_SIZE = (200, 200)
    ATTACK_DURATION_MS = 300 
    
    def __init__(self, codename: str, x: float, y: float):
        self.codename = codename
        
        # 물리 및 게임 플레이 상태
        self.state: Dict[str, Any] = {
            "x": x,
            "y": y,
            "vx": 0,
            "vy": 0,
            "on_ground": True,
            "hp": 100,
            "ultimate_gauge": 0,
            "facing_right": True, # 방향 상태
            "is_awakened": False,         # [추가] 각성 상태 플래그
            "awakening_end_time": 0,      # [추가] 각성 상태 종료 시간
        }

        # 애니메이션 상태
        self.attack_timer = 0
        self.is_attacking = False

        # 이미지 로드 (head, body, hands)
        self.images = self._load_parts() 

    def _safe_load_image(self, part_name: str, size: tuple) -> Optional[pygame.Surface]:
        """안전하게 이미지를 로드하고 크기를 조정합니다."""
        path = os.path.join("assets", "characters", self.codename, f"{part_name}.png")
        if not os.path.exists(path):
             # print(f"Warning: Could not find image for {self.codename}/{part_name}. Check path: {path}")
             return None
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            return img
        except pygame.error:
            # print(f"Warning: Could not load image for {self.codename}/{part_name}. Check path: {path}")
            return None

    def _load_parts(self):
        """캐릭터의 모든 파트(머리, 몸통, 오른손, 왼손)와 각성 헤드를 로드합니다."""
        return {
            "head": self._safe_load_image("head", self.BODY_SIZE), 
            "body": self._safe_load_image("body", self.BODY_SIZE), # 몸통은 예비용으로 유지
            "righthand": self._safe_load_image("righthand", self.HAND_SIZE),
            "lefthand": self._safe_load_image("lefthand", self.HAND_SIZE), 
            
            # [추가] 각성 헤드 애니메이션 프레임 로드
            "head_gak_1": self._safe_load_image("head_gak_1", self.BODY_SIZE),
            "head_gak_2": self._safe_load_image("head_gak_2", self.BODY_SIZE),
        }

    def start_attack_animation(self):
        """공격 애니메이션을 시작합니다."""
        self.is_attacking = True
        self.attack_timer = self.ATTACK_DURATION_MS
        
    def start_awakening(self, duration_ms: int):
        """[추가] 각성 상태를 시작하고 종료 타이머를 설정합니다."""
        if not self.state["is_awakened"]:
            self.state["is_awakened"] = True
            self.state["awakening_end_time"] = pygame.time.get_ticks() + duration_ms

    def update(self, dt: int):
        """캐릭터의 애니메이션 타이머, 방향 및 각성 상태를 업데이트합니다."""
        current_time = pygame.time.get_ticks()
        
        # 1. 공격 타이머 업데이트
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_timer = 0
                
        # 2. [추가] 각성 상태 타이머 업데이트
        if self.state["is_awakened"] and current_time > self.state["awakening_end_time"]:
            self.state["is_awakened"] = False
            self.state["awakening_end_time"] = 0 # 리셋
            
        # 3. 방향 업데이트 (정지 상태에서는 마지막 방향 유지)
        if self.state["vx"] > 0:
            self.state["facing_right"] = True
        elif self.state["vx"] < 0:
            self.state["facing_right"] = False

    def draw(self, screen: pygame.Surface):
        """캐릭터의 파트를 화면에 그립니다. (머리 + 두 손)"""
        
        # 1. 그릴 위치 (정수형으로 변환)
        x, y = int(self.state["x"]), int(self.state["y"])
        
        # 2. [수정] 본체 대신 머리 그리기 (각성 애니메이션 적용)
        main_img = None
        
        # A. 각성 상태일 경우, 해골 특유의 애니메이션 적용 (0.2초 주기)
        if self.state["is_awakened"] and self.codename == "haegol":
            current_time = pygame.time.get_ticks()
            frame_index = (current_time // 200) % 2 # 200ms = 0.2초
            
            if frame_index == 0:
                main_img = self.images.get("head_gak_1")
            else:
                main_img = self.images.get("head_gak_2")
        
        # B. 일반 상태일 경우, 기본 head 사용 (없으면 body 사용)
        if main_img is None:
             main_img = self.images.get("head") or self.images.get("body")
        
        # C. 최종 그리기
        if main_img:
            # 현재 방향에 따라 이미지 뒤집기
            draw_img = main_img
            if not self.state["facing_right"]:
                draw_img = pygame.transform.flip(main_img, True, False)
            
            screen.blit(draw_img, (x, y))
            
        # 3. 오른손 그리기 (공격 애니메이션 적용)
        hand_img_right = self.images["righthand"]
        if hand_img_right:
            
            # 공격 애니메이션 계산 (앞뒤 스윙)
            attack_swing = 0
            if self.is_attacking:
                # 0 (시작) -> ATTACK_DURATION_MS / 2 (최고) -> 0 (종료)
                progress = 1 - (abs(self.attack_timer - self.ATTACK_DURATION_MS / 2) / (self.ATTACK_DURATION_MS / 2))
                attack_swing = 40 * progress # 최대 40픽셀 앞으로 이동

            # 기본 오프셋 (캐릭터 몸통 기준)
            hand_offset_x = 70
            hand_offset_y = 0
            
            draw_hand_right = hand_img_right
            if self.state["facing_right"]:
                # 오른쪽을 볼 때: X + 오프셋 + 공격 스윙
                hand_x = x + hand_offset_x + attack_swing
            else:
                # 왼쪽을 볼 때: 이미지 뒤집기, X + (몸통 크기 - 오프셋 - 손 크기) - 공격 스윙
                draw_hand_right = pygame.transform.flip(hand_img_right, True, False)
                hand_x = x + self.BODY_SIZE[0] - hand_offset_x - self.HAND_SIZE[0] - attack_swing
            
            hand_y = y + hand_offset_y
            screen.blit(draw_hand_right, (int(hand_x), int(hand_y)))


        # 4. 왼손 그리기 (정적 위치)
        hand_img_left = self.images["lefthand"]
        if hand_img_left:
            
            # 기본 오프셋 (오른손보다 약간 뒤, 아래로 위치)
            hand_offset_x = -70 
            hand_offset_y = 0
            
            draw_hand_left = hand_img_left
            if self.state["facing_right"]:
                # 오른쪽을 볼 때: X + 오프셋 
                hand_x_left = x + hand_offset_x
            else:
                # 왼쪽을 볼 때: 이미지 뒤집기, X + (몸통 크기 - 오프셋 - 손 크기)
                draw_hand_left = pygame.transform.flip(hand_img_left, True, False)
                hand_x_left = x + self.BODY_SIZE[0] - hand_offset_x - self.HAND_SIZE[0]

            hand_y_left = y + hand_offset_y
            screen.blit(draw_hand_left, (int(hand_x_left), int(hand_y_left)))
