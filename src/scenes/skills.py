import pygame
import os 
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
        
        # Character 객체의 애니메이션을 시작합니다.
        if user_obj:
            user_obj.start_attack_animation()
        
        return []

    def update(self, dt: int, world: dict):
        """지속 스킬에 사용될 수 있으나, Projectile에는 사용되지 않음"""
        pass

    def draw(self, screen: pygame.Surface):
        """지속 스킬의 시각적 효과를 그릴 때 사용될 수 있음"""
        pass

class Projectile:
    """발사체 객체의 기본 클래스 (gameplay.py에서 객체로 인식됨)"""
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int = 10, owner: str = "p1", size: int = 80, vy: float = 0, gravity: float = 0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy        # 포물선 운동을 위한 Y축 속도
        self.gravity = gravity # 포물선 운동을 위한 중력값
        self.img = img
        self.damage = damage
        self.owner = owner
        self.active = True
        self.size = size 
        self.stuns_target = False # 타격 시 상대방 기절 여부

    def update(self, world: dict):
        """발사체 위치 업데이트 및 제거 조건 확인 (중력/vy 적용)"""
        self.vy += self.gravity # 중력 적용
        self.x += self.vx
        self.y += self.vy
        
        screen_w = world.get("screen_width", 1920)
        screen_h = world.get("screen_height", 1080) # Y 경계를 위한 변수 추가
        
        # 화면 밖으로 나가면 비활성화 (y 경계 추가)
        if self.x < -self.size or self.x > screen_w + self.size or self.y > screen_h:
            self.active = False

    def draw(self, screen: pygame.Surface):
        """발사체를 화면에 그림"""
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))


class MeleeHitbox(Projectile):
    """근접 공격 판정을 위한 발사체 (수명 제한)"""
    def __init__(self, x, y, damage, owner, duration_ms=200, size=120):
        super().__init__(x, y, 0, None, damage, owner, size) 
        self.life_timer = pygame.time.get_ticks() + duration_ms
        
    def update(self, world: dict):
        """수명이 다하면 비활성화"""
        if pygame.time.get_ticks() > self.life_timer:
            self.active = False

    def draw(self, screen: pygame.Surface):
        """근접 히트박스는 애니메이션으로 대체되므로 시각적으로 그리지 않습니다."""
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
        
        # 초기 이미지 스케일링 안전성 강화
        if self.img:
            try:
                self.img = pygame.transform.scale(self.img, (self.initial_size, self.initial_size))
            except Exception:
                 self.img = None


    def update(self, world: dict):
        current_time = pygame.time.get_ticks()
        
        # 1. 총 지속 시간 초과 확인
        if current_time > self.end_time:
            self.active = False
            return

        # 2. 애니메이션 프레임 업데이트
        if self.num_frames > 1 and current_time - self.last_frame_time >= self.frame_duration:
            self.current_frame_index += 1
            self.last_frame_time = current_time
            
            if self.current_frame_index < self.num_frames:
                self.img = self.base_frames[self.current_frame_index]
            else:
                self.active = False 
                
        # 3. 크기 변화 업데이트 (scale_factor가 0이 아닐 경우)
        if self.scale_factor != 0:
            elapsed_time_s = (current_time - self.start_time) / 1000
            
            self.current_size = int(self.initial_size + self.scale_factor * elapsed_time_s)
            
            if self.img and self.current_frame_index < len(self.base_frames):
                try:
                    new_size = max(1, self.current_size)
                    
                    self.img = pygame.transform.scale(self.base_frames[self.current_frame_index], 
                                                     (new_size, new_size))
                except Exception:
                    pass
        
        # Projectile의 x 경계 확인 (y 경계는 gameplay에서 하거나 Projectile에 맡김)
        screen_w = world.get("screen_width", 1920)
        if self.x < -self.current_size or self.x > screen_w + self.current_size:
             self.active = False


    def draw(self, screen: pygame.Surface):
        """현재 프레임을 화면에 그림"""
        if self.img:
            # 크기 확대에 따른 중심 보정
            draw_x = int(self.x - (self.current_size - self.initial_size) / 2)
            draw_y = int(self.y - (self.current_size - self.initial_size) / 2)
            screen.blit(self.img, (draw_x, draw_y))


# --- 기존 캐릭터: 해골 스킬 (유지) ---
class HaegolSwingSkill(Skill):
    """해골 캐릭터의 뼈 휘두르기 (근거리 공격)"""
    def __init__(self, cooldown_ms: int):
        super().__init__("haegol_swing", cooldown_ms=cooldown_ms) 
        self.default_hitbox_size = 150
        self.default_damage = 5
        self.awakened_hitbox_size = 350 
        self.awakened_damage = 10 
        self.effect_size = 300 
        self.effect_frames = self._load_effect_frames()

    def _load_effect_frames(self):
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
            # print("EFFECT DEBUG: Loading ultimate_skill_x.png failed. Using CYAN Placeholder.")
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
            if is_facing_right:
                frames_to_use = [pygame.transform.flip(f, True, False) for f in self.effect_frames]
            stab_effect = AnimatedEffect(x=effect_x, y=effect_y, frames=frames_to_use, frame_duration_ms=200, owner=owner, size=self.effect_size)
            projectiles.append(stab_effect)
        return [hitbox]

class HaegolBoneSkill(Skill):
    """해골 캐릭터의 뼈 발사 스킬"""
    def __init__(self, cooldown_ms: int):
        img_path = "assets/characters/haegol/skill1.png"
        super().__init__("haegol_bone", cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 170
        self.damage = 10
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
            proj_img = self.awakened_img
            current_damage = self.damage * 2 
        else:
            proj_img = self.img
            current_damage = self.damage
        if user_obj:
            is_facing_right = user_obj.state.get("facing_right", True)
            direction = 1 if is_facing_right else -1
        else:
            direction = 1 if target["x"] > user["x"] else -1
        vx = 15 * direction
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 60 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        proj = Projectile(spawn_x, spawn_y, vx, proj_img, damage=current_damage, owner=owner, size=self.proj_size)
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(proj)
        return [proj]

class HaegolUltimateSkill(Skill):
    """해골 캐릭터의 궁극기 (각성)"""
    def __init__(self, cooldown_ms: int):
        super().__init__("haegol_ultimate", cooldown_ms=cooldown_ms) 
        self.duration_ms = 12000 

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if user.get("ultimate_gauge", 0) < 70: return []
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        if user_obj: user_obj.start_awakening(self.duration_ms)
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - 70)
        return []

# --- NEW CHARACTER: 이생선 (Leesaengseon) 스킬 추가 ---

# 1. 기술 1: 생선 소환 (투사체)
class LeesaengseonFishSkill(Skill):
    def __init__(self, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/skill1.png"
        super().__init__("leesaengseon_fish", cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 100
        self.damage = 15
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
    def __init__(self, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/skill2.png"
        super().__init__("leesaengseon_bomb", cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 80
        self.damage = 10
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
class LeesaengseonUltimateSkill(Skill):
    def __init__(self, cooldown_ms: int):
        img_path = "assets/characters/leesaengseon/ultimate.png"
        super().__init__("leesaengseon_ultimate", cooldown_ms=cooldown_ms, img_path=img_path) 
        self.duration_ms = 4000 
        self.belt_height = 240 
        self.belt_speed = 10 
        self.damage = 5 

        self.base_img = _safe_load_and_scale(img_path, (1920, self.belt_height)) 

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if user.get("ultimate_gauge", 0) < 70: return []
        if not self.ready(): return []
        self.last_used = pygame.time.get_ticks()
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - 70)
        if user_obj: user_obj.start_attack_animation() 
        
        GROUND_Y = world.get("GROUND_Y", 950) 
        screen_w = world.get("screen_width", 1920)
        
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
        return [belt]

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
        # 벨트가 화면을 완전히 지나가면 비활성화 (x > screen_w)
        if self.x > self.screen_w:
            self.active = False
            
    def draw(self, screen: pygame.Surface):
        if self.img:
            # 맵 전체 너비로 그립니다.
            screen.blit(self.img, (int(self.x), int(self.y)))
            
# --- get_skills_for_character 함수 ---

def get_skills_for_character(codename: str) -> List[Skill]:
    """캐릭터 코드명에 따른 스킬 객체 리스트 [skill1, skill2, ultimate] 반환"""
    if codename == "haegol":
        swing_skill = HaegolSwingSkill(cooldown_ms=500) 
        bone_skill = HaegolBoneSkill(cooldown_ms=1000) 
        ultimate_skill = HaegolUltimateSkill(cooldown_ms=10000) 
        return [swing_skill, bone_skill, ultimate_skill]
        
    elif codename == "leesaengseon":
        fish_skill = LeesaengseonFishSkill(cooldown_ms=600) 
        bomb_skill = LeesaengseonBombSkill(cooldown_ms=3000) 
        ultimate_skill = LeesaengseonUltimateSkill(cooldown_ms=15000) 
        return [fish_skill, bomb_skill, ultimate_skill]
        
    # 플레이스홀더
    return [
        Skill(f"{codename}_noop1", 500), 
        Skill(f"{codename}_noop2", 1000), 
        Skill(f"{codename}_ult", 10000)
    ]