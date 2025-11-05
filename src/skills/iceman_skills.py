# skills/iceman_skills.py

import pygame
from typing import Optional, List
from .skills_base import Skill, UltimateSkillBase, MeleeHitbox, AnimatedEffect, _safe_load_and_scale, Projectile 
import os 

# =========================================================
# 🧊 Iceman 투사체/이펙트 정의
# =========================================================

class IceBlock(AnimatedEffect):
    """
    아이스맨 궁극기에 의해 얼려진 적 캐릭터 위치에 생성되는 시각적 이펙트.
    """
    def __init__(self, x: float, y: float, size: int, owner: str, duration_ms: int):
        ice_path = "assets/characters/iceman/ice.png" 
        
        ice_img = _safe_load_and_scale(ice_path, (size, size))
        frames_list = [ice_img] if ice_img else [pygame.Surface((size, size), pygame.SRCALPHA)]
        
        super().__init__(
            x=x,
            y=y,
            frames=frames_list,
            frame_duration_ms=duration_ms, 
            owner=owner,
            size=size,
            loops=1 # 한 번 재생 후 duration_ms 뒤 소멸
        )
        self.is_ice_block = True

# =========================================================
# 🧊 Iceman 스킬 정의
# =========================================================

class IcemanPunchSkill(Skill):
    """기술 1: 전방 주먹질 (근접 공격)"""
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/iceman/skill1.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path)
        self.hitbox_size = 150
        self.damage = 10
        
    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj and hasattr(user_obj, 'state') else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        
        center_offset = (CHAR_SIZE // 2) + 50 * direction 
        hitbox_start_x = user["x"] + center_offset - self.hitbox_size // 2
        hitbox_y = user["y"] 
        
        hitbox = MeleeHitbox(
            x=hitbox_start_x, 
            y=hitbox_y, 
            damage=self.damage, 
            owner=owner, 
            duration_ms=200, 
            size=self.hitbox_size
        )
        
        return [hitbox]


class IcemanDashSkill(Skill):
    """기술 2: 얼음 돌진 (데미지 + 1.5초 스턴)"""
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/iceman/skill2.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path)
        self.dash_distance = 250 # 돌진 거리
        self.dash_duration = 300 # ms
        self.stun_duration = 1500 # ms (1.5초)
        self.damage = 5
        self.effect_size = 300
        self.dash_speed = (self.dash_distance / self.dash_duration) * 1000 # 픽셀/초
        
        self.effect_frames = self._load_effect_frames()

    def _load_effect_frames(self) -> List[pygame.Surface]:
        path = "assets/characters/iceman/skill2.png"
        img = _safe_load_and_scale(path, (self.effect_size, self.effect_size))
        return [img] if img else []

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        if user.get("is_dashing", False): return []
        
        self.last_used = pygame.time.get_ticks()

        CHAR_SIZE = 200
        
        # 1. 방향 결정 로직
        last_input = user.get("last_input_key", None)
        
        if last_input in ['a', 'A', 'left']:
            direction = -1 
            is_facing_right = False
        elif last_input in ['d', 'D', 'right']:
            direction = 1 
            is_facing_right = True
        else:
            is_facing_right = user_obj.state.get("facing_right", True) if user_obj and hasattr(user_obj, 'state') else (target["x"] > user["x"])
            direction = 1 if is_facing_right else -1

        # 2. 캐릭터 상태 업데이트
        user["vx"] = self.dash_speed * direction # 픽셀/초
        user["dash_end_time"] = pygame.time.get_ticks() + self.dash_duration
        user["is_dashing"] = True 
        if user_obj: 
            user_obj.start_dash(self.dash_duration)
        
        # 3. 히트박스 및 이펙트 위치 계산 
        if is_facing_right:
            hitbox_x = user["x"] + CHAR_SIZE
        else:
            hitbox_x = user["x"] - self.effect_size

        hitbox_y = user["y"]

        # 4. MeleeHitbox 생성: 300ms 후 소멸
        hitbox_size = 200 
        hitbox = MeleeHitbox(
            x=hitbox_x, 
            y=hitbox_y, 
            damage=self.damage, 
            owner=owner, 
            duration_ms=self.dash_duration, # 300ms
            size=hitbox_size
        )
        hitbox.stuns_target = True
        hitbox.stun_duration_ms = self.stun_duration
        hitbox.attached_to_char = owner 
        hitbox.hit_already = False 
        
        # 5. 돌진 이펙트 생성
        frames_to_use = self.effect_frames
        
        # 🎯 이펙트 이미지 좌우 반전
        if not is_facing_right:
            frames_to_use = [pygame.transform.flip(f, True, False) for f in self.effect_frames if f is not None]

        dash_effect = AnimatedEffect(
            x=hitbox_x, 
            y=hitbox_y, 
            frames=frames_to_use, 
            frame_duration_ms=self.dash_duration, # 총 지속 시간 300ms
            owner=owner, 
            size=self.effect_size,
            loops=1 # 300ms 후 반드시 소멸되도록 명시 (skills_base.py 로직과 연동)
        )
        dash_effect.attached_to_char = owner 

        return [hitbox, dash_effect]


class IcemanUltimateSkill(UltimateSkillBase):
    """궁극기: 얼음 지대 생성 및 빙결"""
    def __init__(self, name: str, cooldown_ms: int):
        super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=60.0) 
        self.damage = 10
        self.duration_ms = 4000 
        self.initial_effect_size = 200
        self.final_effect_size = 800
        self.freeze_duration = 5000 
        self.ult1_duration = 1000 # 1단계 지속 시간
        
        # 이미지 로드 (ultimate_1.png, ultimate_2.png)
        self.ult1_frames = self._load_frames("ultimate_1", self.initial_effect_size)
        self.ult2_frames = self._load_frames("ultimate_2", self.final_effect_size)
        
    def _load_frames(self, key: str, size: int) -> List[pygame.Surface]:
        frames = []
        try:
            path = f"assets/characters/iceman/{key}.png" 
            img = _safe_load_and_scale(path, (size, size))
            
            if img:
                frames.append(img)
            else:
                placeholder = pygame.Surface((size, size), pygame.SRCALPHA)
                placeholder.fill((0, 0, 255, 128)) 
                frames = [placeholder]
        except Exception:
            placeholder = pygame.Surface((size, size), pygame.SRCALPHA)
            placeholder.fill((0, 0, 255, 128)) 
            frames = [placeholder]
            
        return frames

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready() or user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return []
            
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
            
        GROUND_Y = world.get("GROUND_Y", 950)
        char_center_x = user["x"] + 100
        
        # 1단계 이펙트 (1초 지속)
        ult1_effect = AnimatedEffect(
            x=char_center_x - self.initial_effect_size / 2,
            y=GROUND_Y - self.initial_effect_size, 
            frames=self.ult1_frames,
            frame_duration_ms=self.ult1_duration, # 1초
            owner=owner,
            size=self.initial_effect_size,
            loops=1 
        )
        
        skill_state["is_active"] = True
        skill_state["start_time"] = pygame.time.get_ticks()
        skill_state["ult2_activated"] = False 
        
        return [ult1_effect]

    def update(self, dt: int, world: dict, user_state: dict, skill_state: dict, user_obj=None, owner: str = "p1"):
        """궁극기 활성화 중 시간 경과를 체크하고 2단계로 전환합니다."""
        # 이 스킬 상태는 gameplay.py의 스킬 업데이트 루프에서 전달되어야 합니다.
        if not skill_state.get("is_active"):
            return []

        current_time = pygame.time.get_ticks()
        start_time = skill_state.get("start_time", 0)
        
        # 1단계 (1초)가 끝났고, 아직 2단계가 활성화되지 않았다면 2단계 시작
        if not skill_state.get("ult2_activated") and current_time - start_time >= self.ult1_duration:
            skill_state["ult2_activated"] = True
            
            # 캐릭터 위치와 Ground_Y를 기반으로 2단계 이펙트 생성 위치 결정
            GROUND_Y = world.get("GROUND_Y", 950)
            char_center_x = user_state["x"] + 100 # 캐릭터 중앙 x 좌표
            
            # 2단계 이펙트 생성 및 충돌박스 역할 수행
            new_projectiles = self.create_ult2_effect(
                x=char_center_x, 
                y=GROUND_Y, 
                owner=owner, 
                world=world
            )
            
            # 2단계에서 생성된 투사체(이펙트)를 반환
            return new_projectiles 

        # 2단계까지 모두 완료되었는지 체크 (총 지속 시간 4000ms)
        if current_time - start_time >= self.duration_ms:
            skill_state["is_active"] = False # 궁극기 종료
            
        return []

    def create_ult2_effect(self, x: float, y: float, owner: str, world: dict, *args, **kwargs) -> List[Projectile]:
        """궁극기 2단계 (광역 데미지 및 빙결) 이펙트 생성 및 반환"""
        
        _ = world 
        _ = args
        _ = kwargs
        
        ult2_effect = AnimatedEffect(
            x=x - self.final_effect_size / 2, # x를 중앙으로 정렬
            y=y - self.final_effect_size, # y를 바닥에 정렬
            frames=self.ult2_frames,
            frame_duration_ms=self.duration_ms - self.ult1_duration, # 3000ms
            owner=owner,
            size=self.final_effect_size,
            loops=1 # 3초 후 소멸되도록 명시
        )
        # 🌟 2단계 기능 속성 부여
        ult2_effect.damage = self.damage 
        ult2_effect.is_ultimate_area = True 
        ult2_effect.freeze_duration = self.freeze_duration 
        ult2_effect.hit_once_only = True # 광역 데미지/빙결은 한 번만 적용
        
        return [ult2_effect]