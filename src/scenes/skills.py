import pygame
from typing import List, Optional, Dict, Any

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
    def __init__(self, x: float, y: float, vx: float, img: Optional[pygame.Surface], damage: int = 10, owner: str = "p1", size: int = 80):
        self.x = x
        self.y = y
        self.vx = vx
        self.img = img
        self.damage = damage
        self.owner = owner
        self.active = True
        self.size = size # 충돌 판정을 위한 크기 (추가)

    def update(self, world: dict):
        """발사체 위치 업데이트 및 제거 조건 확인"""
        self.x += self.vx
        screen_w = world.get("screen_width", 1920)
        # 화면 밖으로 나가면 비활성화
        if self.x < -self.size or self.x > screen_w + self.size:
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
    재사용 가능한 애니메이션 이펙트 클래스.
    여러 프레임을 순차적으로 그리는 데 사용되며, 수명이 다하면 자동으로 비활성화됩니다.
    """
    def __init__(self, x, y, frames: List[pygame.Surface], frame_duration_ms: int, owner: str, size: int):
        # 이펙트는 데미지를 주지 않고, 투사체로 취급되어 world에서 update/draw만 됩니다.
        super().__init__(x, y, 0, frames[0] if frames else None, damage=0, owner=owner, size=size) 
        
        self.frames = frames
        self.frame_duration = frame_duration_ms
        self.num_frames = len(frames)
        self.current_frame_index = 0
        self.last_frame_time = pygame.time.get_ticks()
        
        # 총 지속 시간 설정 
        self.total_duration = self.num_frames * self.frame_duration
        self.end_time = pygame.time.get_ticks() + self.total_duration

    def update(self, world: dict):
        current_time = pygame.time.get_ticks()
        
        # 1. 애니메이션 프레임 업데이트
        if current_time - self.last_frame_time >= self.frame_duration:
            self.current_frame_index += 1
            self.last_frame_time = current_time
            
            if self.current_frame_index < self.num_frames:
                self.img = self.frames[self.current_frame_index]
            else:
                # 모든 프레임을 재생했으면 비활성화
                self.active = False

        # 2. 총 지속 시간 초과 확인
        if current_time > self.end_time:
             self.active = False
    
    def draw(self, screen: pygame.Surface):
        """현재 프레임을 화면에 그림"""
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))


# --- 스킬 1: 해골의 뼈 휘두르기 (근거리 공격) ---
class HaegolSwingSkill(Skill):
    """해골 캐릭터의 뼈 휘두르기 (근거리 공격)"""
    def __init__(self, cooldown_ms: int):
        super().__init__("haegol_swing", cooldown_ms=cooldown_ms) 
        
        # [수정 4a] 기본 근접 공격 크기 및 데미지
        self.default_hitbox_size = 150
        self.default_damage = 5
        
        # [수정 4b] 각성 시 근접 공격 크기 및 데미지 증가 (범위 확장)
        self.awakened_hitbox_size = 350 
        self.awakened_damage = 10 
        
        # [수정 1] 이펙트 크기 증가 (200 -> 300)
        self.effect_size = 300 
        
        self.effect_frames = self._load_effect_frames()

    def _load_effect_frames(self):
        """[수정 1] 이펙트 크기를 반영하여 이미지 로드 또는 플레이스홀더 생성"""
        frames = []
        loaded_successfully = False

        try:
            # 1. 실제 이미지 로드를 시도합니다.
            temp_frames = []
            for i in range(1, 4): # ultimate_skill_1, 2, 3
                path = f"assets/characters/haegol/ultimate_skill_{i}.png"
                img = pygame.image.load(path).convert_alpha()
                # 캐릭터 크기에 맞게 크기 조정 (self.effect_size = 300 사용)
                img = pygame.transform.scale(img, (self.effect_size, self.effect_size))
                temp_frames.append(img)
            
            # 모든 3개의 프레임이 성공적으로 로드되었다면 사용
            if len(temp_frames) == 3:
                frames = temp_frames
                loaded_successfully = True
        except Exception:
            # 로드 중 하나라도 실패하면 아래 플레이스홀더를 사용합니다.
            pass

        # 2. 로드에 실패했거나 프레임 수가 부족하면 플레이스홀더 생성 (청록색)
        if not loaded_successfully:
            print("EFFECT DEBUG: Loading ultimate_skill_x.png failed. Using CYAN Placeholder.")
            # 시인성이 높은 청록색(CYAN) 반투명 사각형 생성 (ALPHA=200)
            placeholder_surface = pygame.Surface((self.effect_size, self.effect_size), pygame.SRCALPHA)
            placeholder_surface.fill((0, 255, 255, 200)) # CYAN: (R, G, B, A)
            
            # 3 프레임 모두 플레이스홀더로 채웁니다.
            frames = [placeholder_surface, placeholder_surface, placeholder_surface]
        
        return frames

    # 각성 상태 체크 및 이펙트 생성 로직 수정
    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready():
            return []
            
        self.last_used = pygame.time.get_ticks()
        
        if user_obj:
            user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        
        is_awakened = user_obj and user_obj.state.get("is_awakened", False)

        # [수정 4] 각성 여부에 따라 데미지와 히트박스 크기 설정
        current_damage = self.awakened_damage if is_awakened else self.default_damage
        current_hitbox_size = self.awakened_hitbox_size if is_awakened else self.default_hitbox_size

        # Character 객체에서 현재 방향 상태를 가져옵니다.
        is_facing_right = user_obj.state.get("facing_right", True) if user_obj else (target["x"] > user["x"])
        direction = 1 if is_facing_right else -1

        # 1. 근접 공격 히트박스 생성
        # 히트박스 중심을 캐릭터 중심에서 '150px'만큼 전방에 위치시킴
        center_offset = (CHAR_SIZE // 2) + 150 * direction 
        hitbox_start_x = user["x"] + center_offset - current_hitbox_size // 2
        hitbox_y = user["y"] + CHAR_SIZE // 2 - current_hitbox_size // 2

        hitbox = MeleeHitbox(
            x=hitbox_start_x, 
            y=hitbox_y, 
            damage=current_damage, # 동적 데미지 적용
            owner=owner, 
            duration_ms=200, 
            size=current_hitbox_size # 동적 히트박스 크기 적용
        )
        projectiles = world.setdefault("projectiles", [])
        projectiles.append(hitbox)
        
        # 2. 각성 상태일 경우 찌르기 이펙트 추가
        if is_awakened and self.effect_frames:
            # 이펙트 위치를 캐릭터 중심에서 150px 전방에 배치
            effect_center_offset = (CHAR_SIZE // 2) + 150 * direction 
            effect_x = user["x"] + effect_center_offset - self.effect_size // 2
            effect_y = user["y"] + CHAR_SIZE // 2 - self.effect_size // 2
            
            frames_to_use = self.effect_frames
            
            # 방향 반전 로직
            if is_facing_right:
                # 캐릭터가 오른쪽을 볼 때 (direction=1) 프레임을 수평으로 뒤집어 오른쪽을 향하게 만듦
                frames_to_use = [pygame.transform.flip(f, True, False) for f in self.effect_frames]
            
            stab_effect = AnimatedEffect(
                x=effect_x,
                y=effect_y,
                frames=frames_to_use,
                frame_duration_ms=200, 
                owner=owner,
                size=self.effect_size
            )
            
            projectiles.append(stab_effect)
        
        return [hitbox]


# --- 스킬 2: 해골의 뼈 던지기 (원거리 공격) ---
class HaegolBoneSkill(Skill):
    """해골 캐릭터의 뼈 발사 스킬"""
    def __init__(self, cooldown_ms: int):
        # 기본 스킬 이미지 (skill1.png)
        img_path = "assets/characters/haegol/skill1.png"
        super().__init__("haegol_bone", cooldown_ms=cooldown_ms, img_path=img_path) 
        self.proj_size = 170
        self.damage = 10
        
        # 1. 기본 이미지 크기 조정
        if self.img:
            self.img = pygame.transform.scale(self.img, (self.proj_size, self.proj_size))
            
        # 2. [수정] 각성 상태 스킬 이미지 로드 및 크기 조정
        self.awakened_img = None
        try:
            # ultimate_skill2.png 파일을 로드합니다.
            awakened_path = "assets/characters/haegol/ultimate_skill2.png"
            img_ult = pygame.image.load(awakened_path).convert_alpha()
            self.awakened_img = pygame.transform.scale(img_ult, (self.proj_size, self.proj_size))
        except Exception:
            print("EFFECT DEBUG: Loading ultimate_skill2.png failed. Using default image.")
            self.awakened_img = self.img # 로드 실패 시 기본 이미지 사용

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        if not self.ready():
            return []
            
        self.last_used = pygame.time.get_ticks()
        
        if user_obj:
            user_obj.start_attack_animation() 

        CHAR_SIZE = 200
        
        is_awakened = user_obj and user_obj.state.get("is_awakened", False) # 각성 상태 확인

        # [수정] 각성 상태에 따라 사용할 이미지와 데미지 설정
        if is_awakened:
            proj_img = self.awakened_img
            current_damage = self.damage * 2 # 각성 시 데미지 2배
        else:
            proj_img = self.img
            current_damage = self.damage
        
        if user_obj:
            is_facing_right = user_obj.state.get("facing_right", True)
            direction = 1 if is_facing_right else -1
        else:
            direction = 1 if target["x"] > user["x"] else -1

        vx = 15 * direction
        
        # 발사체 시작 위치: 캐릭터의 팔에서 나가는 것처럼 보이도록 조정
        spawn_x = user["x"] + (CHAR_SIZE // 2 + 60 * direction) - self.proj_size // 2
        spawn_y = user["y"] + CHAR_SIZE // 2 - self.proj_size // 2
        
        proj = Projectile(spawn_x, spawn_y, vx, proj_img, damage=current_damage, owner=owner, size=self.proj_size)
        bones = world.setdefault("projectiles", [])
        bones.append(proj)
        
        return [proj]


# --- 궁극기: 해골의 각성 ---
class HaegolUltimateSkill(Skill):
    """[추가] 해골 캐릭터의 궁극기 (각성)"""
    def __init__(self, cooldown_ms: int):
        super().__init__("haegol_ultimate", cooldown_ms=cooldown_ms) 
        self.duration_ms = 12000 # 12초 지속

    def activate(self, user: dict, target: dict, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs):
        
        # 궁극기 게이지가 70 미만이면 발동 불가
        if user.get("ultimate_gauge", 0) < 70:
            return []

        if not self.ready():
            return []
            
        self.last_used = pygame.time.get_ticks()
        
        if user_obj:
            # Character 객체에게 각성 상태 시작을 알립니다.
            user_obj.start_awakening(self.duration_ms)
            
        # 게이지 소모
        user["ultimate_gauge"] = max(0, user["ultimate_gauge"] - 70)
        
        return []


def get_skills_for_character(codename: str) -> List[Skill]:
    """캐릭터 코드명에 따른 스킬 객체 리스트 [skill1, skill2, ultimate] 반환"""
    if codename == "haegol":
        # Skill 1 (뼈 휘두르기, E/Enter 키): 500ms 쿨다운
        swing_skill = HaegolSwingSkill(cooldown_ms=500) 
        # Skill 2 (뼈 던지기, R/RSHIFT 키): 1000ms 쿨다운
        bone_skill = HaegolBoneSkill(cooldown_ms=1000) 
        # Ultimate (각성, S/Down 키): 10000ms 쿨다운
        ultimate_skill = HaegolUltimateSkill(cooldown_ms=10000) 
        
        return [swing_skill, bone_skill, ultimate_skill]
        
    # 플레이스홀더: Haegol이 아닌 다른 캐릭터의 기본 쿨다운 설정
    return [
        Skill(f"{codename}_noop1", 500),    # Skill 1: 0.5초 쿨다운
        Skill(f"{codename}_noop2", 1000),   # Skill 2: 1.0초 쿨다운
        Skill(f"{codename}_ult", 10000)
    ]
