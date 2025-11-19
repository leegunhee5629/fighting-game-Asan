# skills/joker_skills.py

import pygame
from typing import List, Optional 

# skills_base에서 Projectile, AnimatedEffect 등을 임포트
from .skills_base import Skill, UltimateSkillBase, Projectile, AnimatedEffect, _safe_load_and_scale
# --------------------------------------------------------------------------
# 📢 조커 (Joker) 스킬 투사체/이펙트 정의
# --------------------------------------------------------------------------

class JokerSpinningGun(Projectile):
    """
    (참고용: 기술 1이 Projectile로 변경되어 현재 사용되지 않음)
    원래 조커의 기술 1: 회전하며 날아가는 총
    """
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int, owner: str, size: int):
        super().__init__(x, y, vx, img, damage, owner, size) 
        self.base_img = img 
        self.current_angle = 0
        self.rotation_speed = 15
        
    def update(self, world: dict):
        super().update(world)
        
        if self.active:
            self.current_angle = (self.current_angle + self.rotation_speed) % 360
            
    def draw(self, screen: pygame.Surface):
        if self.img:
            rotated_image = pygame.transform.rotate(self.img, self.current_angle)
            rect = rotated_image.get_rect(center=(self.x + self.size // 2, self.y + self.size // 2))
            screen.blit(rotated_image, rect.topleft)

class JokerConfusionBullet(Projectile):
    """조커의 기술 2: 혼란 상태를 유발하는 총알"""
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], owner: str, size: int, confusion_duration: int):
        # 혼란 총알은 데미지가 0이어야 함
        super().__init__(x, y, vx, img, damage=0, owner=owner, size=size) 
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
        
        # frames 리스트를 먼저 정의합니다.
        frames_list = [gas_img] if gas_img else [pygame.Surface((initial_size, initial_size), pygame.SRCALPHA)]
        
        # super() 호출
        super().__init__(
            x=x, 
            y=y, 
            frames=frames_list, 
            frame_duration_ms=duration_ms, 
            owner=owner, 
            size=initial_size,
            scale_factor=scale_rate 
        ) 
        
        # self.frames 대신 지역 변수 frames_list를 사용하여 original_frame을 설정합니다.
        self.original_frame = frames_list[0] if frames_list else None 
        
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
                self.img = pygame.transform.scale(self.original_frame, (new_size, new_size))
            except pygame.error:
                pass 
            
        # 3. 가스 구름의 충돌 박스 크기 업데이트 
        self.size = new_size 


    def draw(self, screen: pygame.Surface):
        if self.active and self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))
        # 📢 디버깅용: 이미지가 로드되지 않은 경우 사각형으로 위치 확인
        elif self.active and pygame.time.get_ticks() % 500 < 250:
            pygame.draw.rect(screen, (255, 255, 255), (int(self.x), int(self.y), self.size, self.size), 2)


# --------------------------------------------------------------------------
# 📢 조커 (Joker) 스킬 정의
# --------------------------------------------------------------------------

class JokerGunTossSkill(Skill):
    """
    ✅ 수정됨: 이선생 기술 1과 동일하게, 기본 Projectile을 사용하며 직선으로 날아갑니다.
    조커의 기술 1: 총 투척 (일반 투사체)
    """
    def __init__(self, name: str, cooldown_ms: int): 
        img_path = "assets/characters/joker/skill1.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path) 
        # 이선생과 동일하게 size=200, damage=3, vx=20으로 맞춤
        self.proj_size = 70 
        self.damage = 6
        self.vx = 20
        
        # 이미지는 투사체 생성 시점에 Projectile에 전달
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
        
        # 💡 궁극기 버프 확인 및 데미지 적용
        final_damage = self.damage
        if user.get("skill1_damage_boost_end_time", 0) > pygame.time.get_ticks():
            final_damage *= user.get("skill1_damage_multiplier", 1.0) # 기본값 1.0
        
        proj = Projectile(
            x=spawn_x, 
            y=spawn_y, 
            vx=self.vx * direction, 
            img=self.img, 
            damage=int(final_damage), # 데미지 적용
            owner=owner, 
            size=self.proj_size
        )
        
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(proj)
        
        return [proj]


class JokerConfusionBulletSkill(Skill):
    """조커의 기술 2: 혼란 총알 발사 (데미지 없음, 혼란 적용)"""
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/joker/skill2.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 30
        self.vx = 25
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
        if proj_img is not None and not is_facing_right: 
            proj_img = pygame.transform.flip(proj_img, True, False)
        
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
    """
    ✅ 최종 수정됨: 웃음 가스 구름 생성 및 6초 동안 기술 1 데미지 2배, 이동 속도 2배 버프 적용
    조커의 궁극기: 웃음 가스 구름 및 강력한 버프
    """
    def __init__(self, name: str, cooldown_ms: int):
        super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=50) 
        
        self.boost_duration = 6000 # 💡 6초 (6000ms)
        self.gas_duration = 15000 
        
        self.gas_size_initial = 100
        self.gas_size_final = 600 
        
        self.gas_dot_damage = 10
        self.gas_damage_interval = 500 # 0.5초당 데미지
        
        # 📢 버프 값
        self.skill1_damage_multiplier = 3.0 
        self.speed_multiplier = 2.0
        
    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        # 1. 쿨다운 및 게이지 체크 (기존 로직 유지)
        if not self.ready(): 
            return []
            
        if user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return [] 
        
        # 2. 쿨다운 리셋 및 게이지 소모
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
            
        # 3. 궁극기 버프 적용 (6초)
        current_time = pygame.time.get_ticks()
        end_time = current_time + self.boost_duration
        
        # 🚀 이동 속도 버프
        user["speed_boost_end_time"] = end_time
        user["speed_multiplier"] = self.speed_multiplier 
        
        # 🔫 기술 1 데미지 버프
        user["skill1_damage_boost_end_time"] = end_time
        user["skill1_damage_multiplier"] = self.skill1_damage_multiplier
        
        # 4. 가스 구름 투사체 생성 (지속 피해 효과)
        GROUND_Y = world.get("GROUND_Y", 950) 
        new_projectiles = []
        
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