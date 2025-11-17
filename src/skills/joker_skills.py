# skills/joker_skills.py

import pygame
# Optional을 typing에서 임포트하도록 수정
from typing import List, Optional 

from .skills_base import Skill, UltimateSkillBase, Projectile, AnimatedEffect, _safe_load_and_scale
# --------------------------------------------------------------------------
# 📢 조커 (Joker) 스킬 투사체/이펙트 정의 (skills_base에서 Projectile, AnimatedEffect 상속)
# --------------------------------------------------------------------------

class JokerSpinningGun(Projectile):
    """조커의 기술 1: 회전하며 날아가는 총"""
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int, owner: str, size: int):
        # base_img를 self.img로 사용하는 것으로 가정하고, __init__ 인수를 수정
        super().__init__(x, y, vx, img, damage, owner, size) 
        self.base_img = img # 회전용 원본 이미지 저장
        self.current_angle = 0
        self.rotation_speed = 15
        
    def update(self, world: dict):
        super().update(world)
        
        if self.active:
            self.current_angle = (self.current_angle + self.rotation_speed) % 360
            
    def draw(self, screen: pygame.Surface):
        # self.base_img 대신 self.img를 사용하고, 회전된 이미지를 그립니다.
        if self.img:
            rotated_image = pygame.transform.rotate(self.img, self.current_angle)
            # 회전 중심을 투사체 위치 + 크기/2로 설정
            rect = rotated_image.get_rect(center=(self.x + self.size // 2, self.y + self.size // 2))
            screen.blit(rotated_image, rect.topleft)

class JokerConfusionBullet(Projectile):
    """조커의 기술 2: 혼란 상태를 유발하는 총알"""
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], owner: str, size: int, confusion_duration: int):
        # 혼란 총알은 데미지가 0이어야 함
        super().__init__(x, y, vx, img, damage=2, owner=owner, size=size) 
        self.causes_confusion = True
        self.confusion_duration_ms = confusion_duration
        
    def draw(self, screen: pygame.Surface):
        if self.img:
            super().draw(screen)
        else:
            # 이미지가 없을 경우 보라색 원으로 대체
            if self.active:
                pygame.draw.circle(screen, (128, 0, 128), (int(self.x + self.size/2), int(self.y + self.size/2)), int(self.size/2))


class JokerGasCloud(AnimatedEffect):
    """조커의 궁극기: 가스 구름 (지속 피해 DoT + 크기 변화)"""
    def __init__(self, x: float, y: float, initial_size: int, final_size: int, damage: int, owner: str, duration_ms: int, damage_interval_ms: int):
        
        gas_path = "assets/characters/joker/ultimate.png"
        
        # 1. 원본 이미지를 로드합니다. (initial_size 크기로 로드)
        gas_img = _safe_load_and_scale(gas_path, (initial_size, initial_size)) 

        # 초당 크기 변화율 (픽셀/초)
        scale_rate = (final_size - initial_size) / (duration_ms / 1000)
        
        # 💡 수정 1: frames 리스트를 먼저 정의합니다. (지역 변수로 사용)
        frames_list = [gas_img] if gas_img else [pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)]
        
        # 💡 수정 2: super() 호출 시 미리 정의한 frames_list를 전달합니다.
        super().__init__(
            x=x, 
            y=y, 
            frames=frames_list, 
            frame_duration_ms=duration_ms, 
            owner=owner, 
            size=initial_size,
            scale_factor=scale_rate 
        ) 
        
        # 💡 최종 수정 (핵심): self.frames 대신 지역 변수 frames_list를 사용하여 original_frame을 설정합니다.
        self.original_frame = frames_list[0] if frames_list else None 
        
        # 📢 self.img 초기화:
        self.img = self.original_frame 

        self.initial_size = initial_size
        self.final_size = final_size
        self.damage = damage
        self.is_gas_cloud = True 
        self.damage_interval = damage_interval_ms
        self.last_damage_time = pygame.time.get_ticks()
        self.start_time = pygame.time.get_ticks()
        self.duration_ms = duration_ms 
        
        # 충돌 박스 위치 조정을 위한 초기값 저장
        self.initial_x = x 
        self.GROUND_Y_EST = y + initial_size 

    def update(self, world: dict):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time
        
        if elapsed_time > self.duration_ms:
            self.active = False
            return
            
        # 크기 변화 로직: 현재 크기 계산
        self.current_size = min(self.final_size, self.initial_size + self.scale_factor * (elapsed_time / 1000))
        new_size = int(self.current_size)
        
        # 1. X 좌표 및 Y 좌표 업데이트 (충돌 박스 위치 조정)
        self.x = self.initial_x - (new_size - self.initial_size) / 2
        self.y = self.GROUND_Y_EST - new_size
        
        # 2. 이미지 리스케일링 (original_frame이 로드되었을 경우)
        if self.original_frame:
            try:
                # self.original_frame(self.frames[0])을 새로운 크기로 리스케일링
                self.img = pygame.transform.scale(self.original_frame, (new_size, new_size))
            except pygame.error:
                # 리스케일링 오류 시 이미지 보존
                pass 
            
        # 3. 가스 구름의 충돌 박스 크기 업데이트 
        self.size = new_size 


    def draw(self, screen: pygame.Surface):
        if self.active and self.img:
            # self.x, self.y는 이미 충돌 박스 위치이므로, 이미지를 그릴 위치와 동일합니다.
            screen.blit(self.img, (int(self.x), int(self.y)))
        # 📢 디버깅용: 이미지가 로드되지 않은 경우 사각형으로 위치 확인
        elif self.active and pygame.time.get_ticks() % 500 < 250:
            # 500ms 간격으로 깜빡이는 흰색 사각형 (디버그용)
            pygame.draw.rect(screen, (255, 255, 255), (int(self.x), int(self.y), self.size, self.size), 2)


# --------------------------------------------------------------------------
# 📢 조커 (Joker) 스킬 정의
# --------------------------------------------------------------------------

class JokerGunTossSkill(Skill):
    """조커의 기술 1: 총 투척 (회전 투사체)"""
    def __init__(self, name: str, cooldown_ms: int): 
        img_path = "assets/characters/joker/skill1.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 100
        self.damage = 8
        self.vx = 12
        self.vy = -10
        self.gravity = 0.6
        
        # 이미지는 투사체 생성 시점에 JokerSpinningGun에 전달
        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        
        # 캐릭터 중앙에서 약간 앞으로 발사
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 50 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        # 투사체 이미지 복사본을 생성하지 않고 전달
        gun = JokerSpinningGun(
            x=spawn_x, 
            y=spawn_y, 
            vx=self.vx * direction, 
            img=self.img, # 스케일링된 이미지 사용
            damage=self.damage, 
            owner=owner, 
            size=self.proj_size
        )
        gun.vy = self.vy
        gun.gravity = self.gravity
        
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(gun)
        
        return [gun]


class JokerConfusionBulletSkill(Skill):
    """조커의 기술 2: 혼란 총알 발사 (데미지 없음, 혼란 적용)"""
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/joker/skill2.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 30
        self.vx = 25
        # gameplay.py의 CONFUSION_DURATION_MS 사용 (3000ms)을 가정
        self.confusion_duration = 3000 

        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 80 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        proj_img = self.img
        # 총알은 뒤집지 않고, 이미지가 없을 경우를 대비하여 None 체크
        if proj_img is not None and not is_facing_right: 
             proj_img = pygame.transform.flip(proj_img, True, False)
        
        # JokerConfusionBullet 생성 시 damage=0이 자동으로 적용됨
        bullet = JokerConfusionBullet(
            x=spawn_x, 
            y=spawn_y, 
            vx=self.vx * direction, 
            img=proj_img, 
            owner=owner, 
            size=self.proj_size,
            confusion_duration=self.confusion_duration
        )
        
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(bullet)
        
        return [bullet]

class JokerUltimateGasSkill(UltimateSkillBase):
    """조커의 궁극기: 웃음 가스 구름 및 이동 속도 버프"""
    def __init__(self, name: str, cooldown_ms: int):
        super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=50) 
        
        self.boost_duration = 4000
        self.gas_duration = 15000 
        
        self.gas_size_initial = 100
        self.gas_size_final = 600 
        
        self.gas_dot_damage = 2
        self.gas_damage_interval = 500 # 0.5초당 데미지
        
    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        # 1. 쿨다운이 아닌지 확인
        if not self.ready(): 
            return []
            
        # 2. ⚡ 게이지 체크: 게이지 부족 시 즉시 종료 (50% 체크)
        if user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return [] 
        
        # 3. 쿨다운 리셋 및 게이지 소모
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
            
        # 4. 궁극기 효과 발동
        current_time = pygame.time.get_ticks()
        GROUND_Y = world.get("GROUND_Y", 950) 
        new_projectiles = []

        # 4-1. 이동 속도 버프 적용
        user["speed_boost_end_time"] = current_time + self.boost_duration
        
        # 4-2. 가스 구름 투사체 생성
        char_center_x = user["x"] + 100
        gas_cloud_y = GROUND_Y - self.gas_size_initial 
        
        gas_cloud = JokerGasCloud(
            x=char_center_x - self.gas_size_initial / 2, 
            y=gas_cloud_y, 
            initial_size=self.gas_size_initial,
            final_size=self.gas_size_final,
            damage=self.gas_dot_damage, 
            owner=owner,
            duration_ms=self.gas_duration,
            damage_interval_ms=self.gas_damage_interval
        )
        
        new_projectiles.append(gas_cloud)
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(gas_cloud)
        
        return new_projectiles