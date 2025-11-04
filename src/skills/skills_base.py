# skills/skills_base.py

import pygame
import os
import math
from typing import List, Optional, Dict, Any

# 헬퍼 함수: 이미지 로드 및 크기 조정
def _safe_load_and_scale(path, size):
    if not path or not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    except Exception:
        # 파일이 없을 때 디버깅을 위해 에러 메시지 주석 처리
        # print(f"Error loading and scaling image at: {path}")
        return None

# --- 기본 클래스 ---

class Skill:
    """모든 스킬의 기본 클래스"""
    def __init__(self, name: str, cooldown_ms: int, img_path: Optional[str] = None):
        self.name = name
        self.cooldown = cooldown_ms
        self.last_used = 0
        self.img = None
        if img_path:
            try:
                self.img = pygame.image.load(img_path).convert_alpha()
            except Exception:
                self.img = None

    def ready(self) -> bool:
        """스킬이 쿨다운이 끝나서 사용할 준비가 되었는지 확인"""
        return pygame.time.get_ticks() - self.last_used >= self.cooldown

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, **kwargs) -> List:
        """
        스킬을 발동하고 애니메이션을 시작합니다.
        user는 character.state 딕셔너리, user_obj는 Character 인스턴스입니다.
        """
        if not self.ready():
            return []
            
        self.last_used = pygame.time.get_ticks()
        
        # Character 객체의 애니메이션을 시작합니다. (Character 클래스는 외부에서 import)
        if user_obj:
            user_obj.start_attack_animation()
        
        return []

    def update(self, dt: int, world: dict):
        """지속 스킬에 사용될 수 있으나, Projectile에는 사용되지 않음"""
        pass

    def draw(self, screen: pygame.Surface):
        """지속 스킬의 시각적 효과를 그릴 때 사용될 수 있음"""
        pass

class UltimateSkillBase(Skill):
    """궁극기 클래스의 기본 틀"""
    def __init__(self, name: str, cooldown_ms: int, ult_cost: int, **kwargs):
        super().__init__(name, cooldown_ms, **kwargs)
        self.ult_cost_percent = ult_cost 

    # 💡 수정: UltimateSkillBase에서는 쿨다운만 체크하고 게이지 소모 로직은 제거합니다.
    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        
        # 쿨다운 리셋은 여기서 수행하지 않습니다. 상속 클래스에서 게이지 체크 후 수행
        if user_obj: user_obj.start_attack_animation() 
        
        return []

class Projectile:
    """발사체 객체의 기본 클래스 (gameplay.py에서 객체로 인식됨)"""
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int = 10, owner: str = "p1", size: int = 80, vy: float = 0, gravity: float = 0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy        # 포물선 운동을 위한 Y축 속도
        self.gravity = gravity # 포물선 운동을 위한 중력값
        self.base_img = img # 회전을 위해 base_img 저장
        self.img = img
        self.damage = damage
        self.owner = owner
        self.active = True
        self.size = size 
        self.stuns_target = False 
        self.causes_confusion = False 

    def update(self, world: dict):
        self.vy += self.gravity # 중력 적용
        self.x += self.vx
        self.y += self.vy
        
        screen_w = world.get("screen_width", 1920)
        screen_h = world.get("screen_height", 1080)
        
        if self.x < -self.size or self.x > screen_w + self.size or self.y > screen_h:
            self.active = False

    def draw(self, screen: pygame.Surface):
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))


class MeleeHitbox(Projectile):
    """근접 공격 판정을 위한 발사체 (수명 제한)"""
    def __init__(self, x, y, damage, owner, duration_ms=200, size=120):
        super().__init__(x, y, 0, None, damage, owner, size) 
        self.life_timer = pygame.time.get_ticks() + duration_ms
        
    def update(self, world: dict):
        if pygame.time.get_ticks() > self.life_timer:
            self.active = False

    def draw(self, screen: pygame.Surface):
        pass

class AnimatedEffect(Projectile):
    """
    재사용 가능한 애니메이션 이펙트 클래스. (크기 변화 애니메이션 로직 추가)
    """
    def __init__(self, x, y, frames: List[pygame.Surface], frame_duration_ms: int, owner: str, size: int, scale_factor: float = 0.0):
        super().__init__(x, y, 0, frames[0] if frames else None, damage=0, owner=owner, size=size) 
        
        self.base_frames = frames 
        self.frame_duration = frame_duration_ms
        self.num_frames = len(frames)
        self.current_frame_index = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.start_time = pygame.time.get_ticks()

        self.scale_factor = scale_factor
        self.initial_size = size
        self.current_size = size
        
        self.total_duration = self.frame_duration if self.num_frames == 1 else (self.num_frames * self.frame_duration)
        self.end_time = self.start_time + self.total_duration
        
        if self.img:
            try:
                self.img = pygame.transform.scale(self.img, (self.initial_size, self.initial_size))
            except Exception:
                   self.img = None


    def update(self, world: dict):
        current_time = pygame.time.get_ticks()
        
        if current_time > self.end_time:
            self.active = False
            return

        if self.num_frames > 1 and current_time - self.last_frame_time >= self.frame_duration:
            self.current_frame_index += 1
            self.last_frame_time = current_time
            
            if self.current_frame_index < self.num_frames:
                self.img = self.base_frames[self.current_frame_index]
            else:
                self.active = False 
                
        if self.scale_factor != 0:
            elapsed_time_s = (current_time - self.start_time) / 1000
            
            self.current_size = int(self.initial_size + self.scale_factor * elapsed_time_s)
            
            if self.current_size <= 0: 
                   self.current_size = 1
            
            if self.base_frames and self.current_frame_index < len(self.base_frames):
                current_base_img = self.base_frames[self.current_frame_index]
                try:
                    new_size = max(1, self.current_size)
                    self.img = pygame.transform.scale(current_base_img, (new_size, new_size))
                except Exception:
                   pass
            
            screen_w = world.get("screen_width", 1920)
            if self.x < -self.current_size or self.x > screen_w + self.current_size:
                   self.active = False


    def draw(self, screen: pygame.Surface):
        if self.img:
            draw_x = int(self.x - (self.current_size - self.initial_size) / 2)
            draw_y = int(self.y - (self.current_size - self.initial_size) / 2)
            screen.blit(self.img, (draw_x, draw_y))
            
# 이생선 궁극기를 위해 이펙트 클래스를 베이스 파일에 유지
class UltimateBeltEffect(Projectile):
    def __init__(self, x, y, vx, img, damage, owner, size, duration_ms, screen_w):
        super().__init__(x, y, vx, img, damage, owner, size, vy=0, gravity=0)
        self.start_time = pygame.time.get_ticks()
        self.end_time = self.start_time + duration_ms
        self.screen_w = screen_w
        self.proj_width = screen_w

    def update(self, world: dict):
        current_time = pygame.time.get_ticks()
        if current_time > self.end_time:
            self.active = False
            return
        self.x += self.vx
        if self.x > self.screen_w:
            self.active = False
            
    def draw(self, screen: pygame.Surface):
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))