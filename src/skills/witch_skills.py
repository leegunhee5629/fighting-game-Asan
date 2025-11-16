import pygame
import os
from .skills_base import Skill, UltimateSkillBase, Projectile, MeleeHitbox

ASSET_PATH = os.path.join("assets", "characters", "witch")

#  회복 물약 스킬
class HealPotionSkill(Skill):
    def __init__(self):
        super().__init__("Heal Potion", cooldown_ms=5000, img_path=os.path.join(ASSET_PATH, "skill1.png"))

    def activate(self, user, target, skill_state, world, user_obj=None, **kwargs):
        if not self.ready():
            return []

        self.last_used = pygame.time.get_ticks()

        # 회복 로직
        max_hp = user.get("max_hp", 100)
        heal_amount = max_hp * 0.015
        user["hp"] = min(max_hp, user["hp"] + heal_amount)

        # 애니메이션 시작
        if user_obj:
            user_obj.start_attack_animation()

        # 회복 이펙트 (선택적)
        return []

"""
#  지팡이 타격 스킬
class StaffStrikeSkill(Skill):
    def __init__(self):
        super().__init__("Staff Strike", cooldown_ms=1500, img_path=os.path.join(ASSET_PATH, "skill2.png"))

    def activate(self, user, target, skill_state, world, user_obj=None, owner="p1", **kwargs):
        if not self.ready():
            return []

        self.last_used = pygame.time.get_ticks()
        if user_obj:
            user_obj.start_attack_animation()

        # 근접 타격 판정 생성
        hitbox_x = user["x"] + (80 if owner == "p1" else -80)
        hitbox_y = user["y"]
        hitbox = MeleeHitbox(x=hitbox_x, y=hitbox_y, damage=10, owner=owner, duration_ms=250, size=100)
        return [hitbox]
"""

#  궁극기: 독 포션
class PoisonPotionUltimate(UltimateSkillBase):
    def __init__(self):
        super().__init__("Poison Potion", cooldown_ms=10000, ult_cost=100, img_path=os.path.join(ASSET_PATH, "ultimate.png"))
        self.projectile_img = pygame.image.load(os.path.join(ASSET_PATH, "skill3.png")).convert_alpha() if os.path.exists(os.path.join(ASSET_PATH, "skill3.png")) else None

    def activate(self, user, target, skill_state, world, user_obj=None, owner="p1", **kwargs):
        if not self.ready():
            return []

        self.last_used = pygame.time.get_ticks()
        if user_obj:
            user_obj.start_attack_animation()

        # 투사체 생성 (독병 던지기)
        direction = 1 if owner == "p1" else -1
        proj_x = user["x"] + direction * 50
        proj_y = user["y"] - 40

        poison_proj = Projectile(
            x=proj_x,
            y=proj_y,
            vx=direction * 15,
            img=self.projectile_img,
            damage=20,
            owner=owner,
            size=80,
            gravity=0.5
        )
        poison_proj.causes_poison = True
        poison_proj.poison_duration = 2000  # 2초
        poison_proj.poison_dps = 0.015      # 1.5% 초당 데미지

        return [poison_proj]