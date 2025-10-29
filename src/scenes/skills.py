import pygame
from typing import List, Optional

class Skill:
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
        return pygame.time.get_ticks() - self.last_used >= self.cooldown

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, **kwargs) -> List:
        self.last_used = pygame.time.get_ticks()
        return []

    def update(self, dt: int, world: dict):
        pass

    def draw(self, screen: pygame.Surface):
        pass

class Projectile:
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int = 10, owner: str = "p1"):
        self.x = x
        self.y = y
        self.vx = vx
        self.img = img
        self.damage = damage
        self.owner = owner
        self.active = True

    def update(self, world: dict):
        self.x += self.vx
        screen_w = world.get("screen_width", 1920)
        if self.x < -200 or self.x > screen_w + 200:
            self.active = False

    def draw(self, screen: pygame.Surface):
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))

# --- 예시 스킬: 해골의 뼈 발사 ---
class HaegolBoneSkill(Skill):
    def __init__(self):
        img_path = "assets/characters/haegol/skill1.png"
        super().__init__("haegol_bone", cooldown_ms=2000, img_path=img_path)
        if self.img:
            self.img = pygame.transform.scale(self.img, (80, 80))

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, owner: str = "p1", **kwargs):
        if not self.ready():
            return []
        self.last_used = pygame.time.get_ticks()
        direction = 1 if target["x"] > user["x"] else -1
        vx = 15 * direction
        spawn_x = user["x"] + (100 if owner == "p1" else -100)
        spawn_y = user["y"] + 80
        proj = Projectile(spawn_x, spawn_y, vx, self.img, damage=10, owner=owner)
        bones = world.setdefault("projectiles", [])
        bones.append(proj)
        return [proj]

def get_skills_for_character(codename: str):
    if codename == "haegol":
        return [HaegolBoneSkill(), None, None]
    # 플레이스홀더
    return [Skill("noop1", 1000), Skill("noop2", 5000), Skill("ult", 10000)]