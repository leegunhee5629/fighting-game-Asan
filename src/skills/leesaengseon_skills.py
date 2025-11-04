# skills/leesaengseon_skills.py

import pygame
from .skills_base import Skill, UltimateSkillBase, Projectile, MeleeHitbox, AnimatedEffect, UltimateBeltEffect, _safe_load_and_scale
from typing import List

# 1. 기술 1: 생선 소환 (투사체)
class LeesaengseonFishSkill(Skill):
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/skill1.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path)
        self.proj_size = 100
        self.damage = 3
        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        vx = 20 * direction 
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 50 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        proj = Projectile(spawn_x, spawn_y, vx, self.img, damage=self.damage, owner=owner, size=self.proj_size)
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(proj)
        
        return [proj]

# 2. 기술 2: 비린내 폭탄 (포물선 + 폭발 애니메이션 + 기절)
class LeesaengseonBombSkill(Skill):
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/skill2.png"
        super().__init__(name, cooldown_ms=cooldown_ms, img_path=img_path)
        self.proj_size = 80
        self.damage = 7
        self.stun_duration_ms = 1000 
        
        self.explosion_size_initial = 50 
        self.explosion_size_final = 200 
        self.explosion_duration = 500 
        
        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))
        
        self.effect_img = _safe_load_and_scale("assets/characters/leesaengseon/skill2_effect.png", 
                                               (self.explosion_size_final, self.explosion_size_final))

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        
        vx = 10 * direction
        vy = -18 
        
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 50 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        bomb = Projectile(spawn_x, spawn_y, vx, self.img, 
                              damage=self.damage, owner=owner, size=self.proj_size, 
                              vy=vy, gravity=1) 
                              
        bomb.stuns_target = True
        
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(bomb)
        
        return [bomb]
        
    def create_explosion_effect(self, x, y, owner):
        """폭발 이펙트 및 히트박스 생성 (gameplay.py에서 호출됨)"""
        scale_factor = (self.explosion_size_final - self.explosion_size_initial) / (self.explosion_duration / 1000)
        
        frames = [self.effect_img or pygame.Surface((self.explosion_size_final, self.explosion_size_final), pygame.SRCALPHA)]
        
        effect = AnimatedEffect(
            x=x - self.explosion_size_initial / 2, 
            y=y - self.explosion_size_initial / 2,
            frames=frames,
            frame_duration_ms=self.explosion_duration, 
            owner=owner,
            size=self.explosion_size_initial,
            scale_factor=scale_factor 
        )
        
        hitbox = MeleeHitbox(
            x=x - self.explosion_size_final / 2, 
            y=y - self.explosion_size_final / 2,
            damage=self.damage,
            owner=owner,
            duration_ms=200, 
            size=self.explosion_size_final 
        )
        hitbox.stuns_target = True 

        return [effect, hitbox]

# 3. 궁극기: 마지막 만찬 (맵 가로지르는 광역 피해)
class LeesaengseonUltimateSkill(UltimateSkillBase):
    def __init__(self, name: str, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/ultimate.png"
        super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=40, img_path=img_path) 
        self.duration_ms = 4000 
        self.belt_height = 240 
        self.belt_speed = 10 
        self.damage = 25 

        self.base_img = _safe_load_and_scale(img_path, (1920, self.belt_height)) 

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        # 1. 쿨다운이 아닌지 확인
        if not self.ready(): 
            return []
            
        # 2. ⚡ 게이지 체크: 게이지 부족 시 즉시 종료 (40% 체크)
        if user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return []
            
        # 3. 쿨다운 리셋 및 게이지 소모
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
            
        # 4. 궁극기 효과 발동
        GROUND_Y = world.get("GROUND_Y", 950) 
        screen_w = world.get("screen_width", 1920)
        new_projectiles = []
        
        belt = UltimateBeltEffect(
            x=-screen_w, 
            y=GROUND_Y - self.belt_height, 
            vx=self.belt_speed, 
            img=self.base_img, 
            damage=self.damage, 
            owner=owner, 
            size=self.belt_height, 
            duration_ms=self.duration_ms,
            screen_w=screen_w
        )
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(belt)
        new_projectiles.append(belt)
        
        return new_projectiles