# skills/haegol_skills.py

import pygame
from .skills_base import Skill, UltimateSkillBase, MeleeHitbox, AnimatedEffect, _safe_load_and_scale
from typing import List

class HaegolSwingSkill(Skill):
    """해골 캐릭터의 뼈 휘두르기 (근거리 공격)"""
    def __init__(self, name: str, cooldown_ms: int):
        super().__init__(name, cooldown_ms=cooldown_ms) 
        self.default_hitbox_size = 150
        self.default_damage = 5
        self.awakened_hitbox_size = 350 
        self.awakened_damage = 10 
        self.effect_size = 300 
        self.effect_frames = self._load_effect_frames()

    def _load_effect_frames(self):
        # ... (기존 _load_effect_frames 로직 유지) ...
        frames = []
        loaded_successfully = False
        try:
            temp_frames = []
            for i in range(1, 4): 
                path = f"assets/characters/haegol/ultimate_skill_{i}.png"
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (self.effect_size, self.effect_size))
                temp_frames.append(img)
            if len(temp_frames) == 3:
                frames = temp_frames
                loaded_successfully = True
        except Exception:
            pass
        if not loaded_successfully:
            placeholder_surface = pygame.Surface((self.effect_size, self.effect_size), pygame.SRCALPHA)
            placeholder_surface.fill((0, 255, 255, 200)) 
            frames = [placeholder_surface, placeholder_surface, placeholder_surface]
        return frames

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 
        CHAR_SIZE = 200
        is_awakened = user_obj and user_obj.state.get("is_awakened", False)
        current_damage = self.awakened_damage if is_awakened else self.default_damage
        current_hitbox_size = self.awakened_hitbox_size if is_awakened else self.default_hitbox_size
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        center_offset = (CHAR_SIZE // 2) + 150 * direction 
        hitbox_start_x = user["x"] + center_offset - current_hitbox_size // 2
        hitbox_y = user["y"] + CHAR_SIZE // 2 - current_hitbox_size // 2
        hitbox = MeleeHitbox(x=hitbox_start_x, y=hitbox_y, damage=current_damage, owner=owner, duration_ms=200, size=current_hitbox_size)
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(hitbox)
        
        if is_awakened and self.effect_frames:
            effect_center_offset = (CHAR_SIZE // 2) + 150 * direction 
            effect_x = user["x"] + effect_center_offset - self.effect_size // 2
            effect_y = user["y"] + CHAR_SIZE // 2 - self.effect_size // 2
            
            frames_to_use = self.effect_frames
            
            # 🔄 수정된 로직: 이펙트 회전을 반대로 설정합니다.
            # 캐릭터가 오른쪽을 보는데 (is_facing_right=True), 이펙트는 왼쪽으로 회전해야 한다고 가정합니다.
            if is_facing_right:
                 # 오른쪽을 볼 때 (direction=1) 프레임을 뒤집어 (왼쪽으로 회전하는 것처럼) 보이게 합니다.
                 frames_to_use = [pygame.transform.flip(f, True, False) for f in self.effect_frames]
            
            # 캐릭터가 왼쪽을 볼 때는 (is_facing_right=False) 기본 프레임을 사용하여,
            # (기본 프레임이 오른쪽으로 회전하는 이미지라면) 왼쪽으로 회전하는 것처럼 보이게 합니다.
            # (이전의 'if not is_facing_right' 로직을 다시 제거했습니다.)
            
            stab_effect = AnimatedEffect(x=effect_x, y=effect_y, frames=frames_to_use, frame_duration_ms=200, owner=owner, size=self.effect_size)
            projectiles.append(stab_effect)
            
        return [hitbox]

class HaegolBoneSkill(Skill):
    """해골 캐릭터의 뼈 발사 스킬"""
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/haegol/skill1.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path)
        self.proj_size = 170
        self.damage = 5
        
        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))
        
        self.awakened_img = None
        try:
            awakened_path = "assets/characters/haegol/ultimate_skill2.png"
            img_ult = pygame.image.load(awakened_path).convert_alpha()
            self.awakened_img = pygame.transform.scale(img_ult, (self.proj_size, self.proj_size))
        except Exception:
            self.awakened_img = self.img 

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 
        
        CHAR_SIZE = 200
        is_awakened = user_obj and user_obj.state.get("is_awakened", False) 
        
        if is_awakened:
            base_proj_img = self.awakened_img
            current_damage = self.damage * 2 
        else:
            base_proj_img = self.img
            current_damage = self.damage
            
        from .skills_base import Projectile 
            
        if user_obj:
            is_facing_right = user_obj.state.get("facing_right", True)
            direction = 1 if is_facing_right else -1
        else:
            direction = 1 if target["x"] > user["x"] else -1
            is_facing_right = (direction == 1)
            
        proj_img = base_proj_img
        
        # 🔄 수정된 로직: 투사체 회전을 반대로 설정합니다.
        # 기존: 왼쪽을 볼 때 뒤집음 (정방향)
        # 수정: 오른쪽을 볼 때 뒤집음 (반대 방향)
        # 이렇게 하면, 투사체의 방향성이 캐릭터가 보는 방향과 반대가 됩니다.
        if proj_img and is_facing_right:
             proj_img = pygame.transform.flip(proj_img, True, False)
            
        vx = 15 * direction
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 60 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        proj = Projectile(spawn_x, spawn_y, vx, proj_img, damage=current_damage, owner=owner, size=self.proj_size)
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(proj)
        
        return [proj]

class HaegolUltimateSkill(UltimateSkillBase):
    """해골 캐릭터의 궁극기 (각성)"""
    def __init__(self, name: str, cooldown_ms: int):
        super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=70) 
        self.duration_ms = 12000 

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        # 1. 쿨다운이 아닌지 확인 (UltimateSkillBase.activate 대신 직접 체크)
        if not self.ready(): 
            return []
            
        # 2. ⚡ 게이지 체크: 게이지 부족 시 즉시 종료 (70% 체크)
        if user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return []
            
        # 3. 쿨다운 리셋 및 게이지 소모 (성공적으로 발동할 때만 소모)
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
            
        # 4. 궁극기 발동 (각성)
        if user_obj: user_obj.start_awakening(self.duration_ms)
        
        return []