import pygame
import os
from typing import List, Dict, Any

# AnimatedEffect, Projectile, MeleeHitbox, UltimateSkillBase 등을 사용하기 위해 skills_base에서 임포트
# (skills_base.py 파일이 프로젝트 루트에 있다고 가정)
# 만약 skills_base가 다른 위치에 있다면 from .skills_base 대신 경로를 수정해야 합니다.
from .skills_base import Skill, UltimateSkillBase, Projectile, MeleeHitbox, AnimatedEffect, _safe_load_and_scale 

ASSET_PATH = os.path.join("assets", "characters", "witch")


# --- 이펙트 구현 클래스 (AnimatedEffect 상속) ---

# 회복 이펙트: 위로 올라가며 사라짐
class HealEffect(AnimatedEffect):
    def __init__(self, x, y, owner, size):
        img_path = os.path.join(ASSET_PATH, "skill1.png")
        loaded_img = _safe_load_and_scale(img_path, (size, size))
        
        if not loaded_img:
            green_circle = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(green_circle, (50, 255, 50, 180), (size // 2, size // 2), size // 2)
            frames = [green_circle]
        else:
            frames = [loaded_img]
        
        super().__init__(x, y, frames=frames, frame_duration_ms=100, owner=owner, size=size, loops=1)
        self.vy = -3
        self.gravity = 0 
        self.duration_ms = 800
        self.end_time = pygame.time.get_ticks() + self.duration_ms
        self.initial_y = y
        
    def update(self, world: Dict[str, Any]):
        super().update(world)
        
        current_time = pygame.time.get_ticks()
        if current_time > self.end_time:
            self.active = False
            return
            
        

# 독 폭발 이펙트: 작게 시작해서 빠르게 커지며 사라짐
class PoisonEffect(AnimatedEffect):
    def __init__(self, x, y, owner, size):
        img_path = os.path.join(ASSET_PATH, "ultimate_effect.png")
        loaded_img = _safe_load_and_scale(img_path, (size, size))
        frames = [loaded_img] if loaded_img else [pygame.Surface((1, 1), pygame.SRCALPHA)]
        
        super().__init__(x, y, frames=frames, frame_duration_ms=100, owner=owner, size=size, 
                          scale_factor=300, loops=1) 
        self.duration_ms = 500 
        self.end_time = pygame.time.get_ticks() + self.duration_ms
        
    def update(self, world: Dict[str, Any]):
        super().update(world)
        
        if pygame.time.get_ticks() > self.end_time:
             self.active = False
             return


# 🟢 [수정됨]: 독 포션 전용 투사체 클래스 (TypeError 해결)
class PoisonPotionProjectile(Projectile):
    def __init__(self, x, y, vx, img, damage, owner, size, gravity, vy=0):
        # **핵심 수정**: vy=vy 인수를 제거하고 vy를 위치 인수로만 전달하여 중복 오류를 해결
        super().__init__(x, y, vx, img, damage, owner, size, gravity, vy)
        # 이 투사체는 충돌 시 독 디버프를 유발하지 않고,
        # 충돌 후 생성되는 MeleeHitbox(폭발)이 독 디버프를 걸게 됩니다.
        self.is_ultimate_proj = True 


# --- 마녀 스킬 클래스 ---

class HealPotionSkill(Skill):
    def __init__(self):
        super().__init__("heal_potion", cooldown_ms=5000, img_path=os.path.join(ASSET_PATH, "skill1.png"))
        self.heal_amount_percent = 0.05

    def activate(self, user: Dict[str, Any], target: Dict[str, Any], skill_state: Dict[str, Any], world: Dict[str, Any], user_obj=None, **kwargs) -> List[Any]:
        if not self.ready():
            return []

        self.last_used = pygame.time.get_ticks()

        max_hp = user.get("max_hp", 100)
        heal_amount = max_hp * self.heal_amount_percent
        user["hp"] = min(max_hp, user["hp"] + heal_amount)

        if user_obj:
            user_obj.start_attack_animation()

        CHAR_SIZE = user.get("size", 200)
        effect_size = 100
        effect_x = user["x"] + CHAR_SIZE // 2 - effect_size // 2
        effect_y = user["y"] + CHAR_SIZE // 2 - effect_size // 2
        
        heal_effect = HealEffect(x=effect_x, y=effect_y, owner=user.get("owner", "p1"), size=effect_size)

        return [heal_effect] 


class StaffStrikeSkill(Skill):
    def __init__(self):
        super().__init__("staff_strike", cooldown_ms=500, img_path=os.path.join(ASSET_PATH, "skill2.png"))
        # 🔨 [추가]: 근접 공격 이펙트 로드
        self.effect_size = 150 # 이펙트 크기
        self.effect_frames = self._load_strike_effect()

    def _load_strike_effect(self):
        frames = []
        # 공격 애니메이션 이미지 (skill2.png)를 이펙트 프레임으로 사용합니다.
        img_path = os.path.join(ASSET_PATH, "skill2.png")
        loaded_img = _safe_load_and_scale(img_path, (self.effect_size, self.effect_size))
        
        if loaded_img:
            # 애니메이션 대신 단일 이미지에 회전 효과를 주려면 단일 프레임을 사용합니다.
            frames = [loaded_img] 
        else:
            # 로드 실패 시 디버깅용 파란색 박스
            placeholder = pygame.Surface((self.effect_size, self.effect_size), pygame.SRCALPHA)
            placeholder.fill((0, 0, 255, 100))
            frames = [placeholder]
        return frames


    def activate(self, user: Dict[str, Any], target: Dict[str, Any], skill_state: Dict[str, Any], world: Dict[str, Any], user_obj=None, owner="p1", **kwargs) -> List[Any]:
        if not self.ready():
            return []

        self.last_used = pygame.time.get_ticks()
        if user_obj:
            user_obj.start_attack_animation()

        CHAR_SIZE = user.get("size", 200)
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1
        
        # 1. 히트박스 생성 (충돌 판정)
        hitbox_size = 120
        # 지팡이가 캐릭터 앞에 위치하도록 오프셋 조정
        center_offset = (CHAR_SIZE // 2) + 150 * direction 
        hitbox_x = user["x"] + center_offset - hitbox_size // 2
        hitbox_y = user["y"] + CHAR_SIZE // 2 - hitbox_size // 2
        
        hitbox = MeleeHitbox(x=hitbox_x, y=hitbox_y, damage=5, owner=owner, duration_ms=250, size=hitbox_size)
        
        # 2. 🔨 [핵심 수정]: 애니메이티드 이펙트 생성 (시각적 회전)
        effects_to_add = [hitbox]
        
        if self.effect_frames:
            effect_x = user["x"] + center_offset - self.effect_size // 2
            effect_y = user["y"] + CHAR_SIZE // 2 - self.effect_size // 2
            
            frames_to_use = self.effect_frames
            
            # 해골 스킬처럼 방향에 따라 이미지 좌우 반전 적용 (시각적 회전)
            # 기본 이미지가 오른쪽 스윙이라고 가정하고, 왼쪽을 볼 때 뒤집습니다.
            if not is_facing_right:
                frames_to_use = [pygame.transform.flip(f, True, False) for f in self.effect_frames]
            
            strike_effect = AnimatedEffect(x=effect_x, y=effect_y, frames=frames_to_use, 
                                           frame_duration_ms=100, owner=owner, size=self.effect_size, loops=1)
            effects_to_add.append(strike_effect)

        # MeleeHitbox와 AnimatedEffect를 모두 반환
        return effects_to_add


# 궁극기: 독 물약 투척 (포물선 투사체)
class PoisonPotionUltimate(UltimateSkillBase):
# ... (이하 코드는 변경 없음) ...
    def __init__(self):
        super().__init__("poison_potion_ultimate", cooldown_ms=10000, ult_cost=50, img_path=os.path.join(ASSET_PATH, "ultimate.png"))
        
        proj_size = 100
        self.projectile_size = proj_size
        # 궁극기 이미지 로드 및 대체 로직
        self.projectile_img = _safe_load_and_scale(os.path.join(ASSET_PATH, "ultimate.png"), (proj_size, proj_size))
        
        if not self.projectile_img:
            red_square = pygame.Surface((proj_size, proj_size))
            red_square.fill((255, 0, 0))
            self.projectile_img = red_square
            
        # 폭발 설정
        self.explosion_size = 150
        self.explosion_duration = 500
        self.damage = 20 # 궁극기 피해량

    def activate(self, user: Dict[str, Any], target: Dict[str, Any], skill_state: Dict[str, Any], world: Dict[str, Any], user_obj=None, owner="p1", **kwargs) -> List[Any]:
        # 게이지 및 쿨다운 조건 확인
        if not self.ready() or user.get("ultimate_gauge", 0) < self.ult_cost_percent: 
            return []

        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - self.ult_cost_percent)
        
        if user_obj:
            user_obj.start_attack_animation()

        CHAR_SIZE = user.get("size", 200)
        direction = 1 if user_obj and user_obj.state.get("facing_right", True) else -1
        
        proj_x = user["x"] + (CHAR_SIZE // 2) + direction * 50
        proj_y = user["y"] + (CHAR_SIZE * 0.3) 

        # PoisonPotionProjectile 사용 및 포물선 속도 설정
        poison_proj = PoisonPotionProjectile( 
            x=proj_x,
            y=proj_y,
            vx=direction * 1,
            vy=1, # 포물선 운동을 위한 초기 수직 속도
            img=self.projectile_img, 
            damage=self.damage,
            owner=owner,
            size=self.projectile_size,
            gravity=0.2,
        )
        
        # 충돌 시 처리 로직을 위해 스킬 인스턴스 자체를 투사체에 저장
        poison_proj.collision_skill_instance = self 

        projectiles = world.setdefault("projectiles", [])
        projectiles.append(poison_proj)

        return [poison_proj]
    
    # 폭발 이펙트/히트박스 생성 함수
    def create_explosion_effect(self, x, y, owner) -> List[Any]:
        """독 포션 충돌 시 독 폭발 이펙트 및 히트박스 생성"""
        
        # 1. 이펙트 생성
        effect = PoisonEffect(
            x=x, # 투사체가 충돌한 위치
            y=y,
            owner=owner,
            size=self.explosion_size
        )
        
        # 2. 히트박스 생성 (폭발 피해 및 독 디버프 적용)
        hitbox = MeleeHitbox(
            x=x - self.explosion_size / 2, 
            y=y - self.explosion_size / 2,
            damage=self.damage,
            owner=owner,
            duration_ms=200, 
            size=self.explosion_size
        )
        
        # 히트박스가 충돌 시 독 디버프를 걸도록 설정
        hitbox.causes_poison = True
        hitbox.poison_duration = 15000
        hitbox.poison_dps = 0.001

        return [effect, hitbox]