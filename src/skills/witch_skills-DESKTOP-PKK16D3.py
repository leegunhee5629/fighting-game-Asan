import os
import pygame
from typing import List, Optional, Any

from .skills_base import Skill, UltimateSkillBase, Projectile, MeleeHitbox
try:
    from .skills_base import AnimatedEffect
except Exception:
    AnimatedEffect = None

ASSET_PATH = os.path.join("assets", "characters", "witch")


def _safe_load_image(path: str, size: Optional[tuple] = None) -> Optional[pygame.Surface]:
    """파일이 있고 로드 가능하면 Surface 반환, 아니면 None."""
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path)
        try:
            img = img.convert_alpha()
        except Exception:
            img = img.convert()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        return None


# --- 호환성 래퍼: gameplay가 기대하는 속성/메서드 보장 ---
class _CompatEntity:
    def __init__(self, base_obj: Any, x: float, y: float, size: int, damage: int, owner: str):
        self._base = base_obj
        self.x = x
        self.y = y
        self.size = int(size)
        self.damage = damage
        self.owner = owner
        self.active = True
        # 기본값
        self.gravity = getattr(base_obj, "gravity", 0) if base_obj is not None else 0
        # optional timing props used by gameplay
        if not hasattr(self, "last_damage_time"):
            self.last_damage_time = 0
        if not hasattr(self, "damage_interval"):
            self.damage_interval = 0

    def update(self, world: dict):
        # 우선 base 업데이트 시도
        try:
            if hasattr(self._base, "update"):
                self._base.update(world)
            else:
                # 기본 이동 처리 (vx 존재 시)
                vx = getattr(self._base, "vx", 0)
                vy = getattr(self._base, "vy", 0)
                # 작은 방어적 업데이트
                self.x = getattr(self._base, "x", self.x)
                self.y = getattr(self._base, "y", self.y)
        except Exception:
            pass

    def draw(self, screen: pygame.Surface):
        # 기본 base draw 시도
        try:
            if hasattr(self._base, "draw"):
                self._base.draw(screen)
                return
        except Exception:
            pass
        # fallback: simple rect
        try:
            s = max(1, int(self.size))
            rect = pygame.Rect(int(self.x), int(self.y), s, s)
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            surf.fill((0, 255, 0, 120))
            screen.blit(surf, rect.topleft)
        except Exception:
            pass


def _ensure_compat(obj, fallback_x=0, fallback_y=0, fallback_size=48, fallback_damage=0, fallback_owner="p1"):
    """obj가 gameplay가 기대하는 인터페이스를 만족하면 그대로, 아니면 래핑해서 반환."""
    if obj is None:
        return None
    # 이미 필요한 속성/메서드가 있으면 그대로 반환
    if all(hasattr(obj, attr) for attr in ("x", "y", "size", "damage", "owner", "active", "update", "draw")):
        return obj
    # 어쩌면 dict일 수도 있으므로 추출
    if isinstance(obj, dict):
        x = obj.get("x", obj.get("px", fallback_x))
        y = obj.get("y", obj.get("py", fallback_y))
        size = obj.get("size", obj.get("w", obj.get("width", fallback_size)))
        damage = obj.get("damage", fallback_damage)
        owner = obj.get("owner", fallback_owner)
        return _CompatEntity(obj, x, y, size, damage, owner)
    # 객체지만 일부 속성만 있는 경우
    x = getattr(obj, "x", getattr(obj, "px", fallback_x))
    y = getattr(obj, "y", getattr(obj, "py", fallback_y))
    size = getattr(obj, "size", None)
    if size is None:
        # try width/height
        w = getattr(obj, "w", None) or getattr(obj, "width", None)
        h = getattr(obj, "h", None) or getattr(obj, "height", None)
        if w is not None:
            size = w
        elif h is not None:
            size = h
        else:
            size = fallback_size
    damage = getattr(obj, "damage", fallback_damage)
    owner = getattr(obj, "owner", fallback_owner)
    return _CompatEntity(obj, x, y, size, damage, owner)


# ---------------- 스킬 구현 ----------------
class HealPotionSkill(Skill):
    def __init__(self, name: str, cooldown_ms: int):
        try:
            super().__init__(name, cooldown_ms=cooldown_ms, img_path=os.path.join(ASSET_PATH, "skill1.png"))
        except TypeError:
            try:
                super().__init__(name, cooldown_ms=cooldown_ms)
            except Exception:
                super().__init__(name)

    def activate(self, user: dict, target: Any, skill_state: dict, world: dict, user_obj=None, **kwargs) -> List:
        # 준비 체크(안전)
        ready_fn = getattr(self, "ready", None)
        try:
            if callable(ready_fn) and not ready_fn():
                return []
        except Exception:
            return []

        # last_used 갱신
        if hasattr(self, "last_used"):
            try:
                self.last_used = pygame.time.get_ticks()
            except Exception:
                pass

        # 회복: 최대체력의 15% (정수)
        max_hp = int(user.get("max_hp", 100))
        heal_amount = max(1, int(max_hp * 0.15))
        user["hp"] = min(max_hp, int(user.get("hp", 0)) + heal_amount)

        # 필요하면 스킬 상태(쿨다운 정보) 업데이트
        try:
            if isinstance(skill_state, dict):
                skill_state.setdefault("last_used_by", {}).update({self.name: pygame.time.get_ticks()})
        except Exception:
            pass

        # 사용자 오브젝트 애니메이션 트리거(있으면)
        if user_obj and hasattr(user_obj, "start_skill_animation"):
            try:
                user_obj.start_skill_animation(self.name)
            except Exception:
                pass

        # 회복 스킬은 반환 객체가 필요없음 -> 빈 리스트 반환 (gameplay가 호출 결과에 의존하지 않도록)
        return []


class StaffStrikeSkill(Skill):
    def __init__(self, name: str, cooldown_ms: int):
        try:
            super().__init__(name, cooldown_ms=cooldown_ms, img_path=os.path.join(ASSET_PATH, "skill2.png"))
        except TypeError:
            try:
                super().__init__(name, cooldown_ms=cooldown_ms)
            except Exception:
                super().__init__(name)
        self.hitbox_size = 150
        self.hitbox_damage = 6
        self.awakened_hitbox_size = 320
        self.awakened_damage = 12
        self.effect_size = 280
        self._assets_loaded = False
        self._effect_frames: List[pygame.Surface] = []
        self.hitbox_duration_ms = 120

    def _load_assets_once(self):
        if self._assets_loaded:
            return
        frames = []
        for i in range(1, 4):
            path = os.path.join(ASSET_PATH, f"effect_{i}.png")
            img = _safe_load_image(path, size=(self.effect_size, self.effect_size))
            if img:
                frames.append(img)
        self._effect_frames = frames
        self._assets_loaded = True

    class _SimpleHitbox:
        """gameplay가 기대하는 최소 인터페이스를 보장하는 히트박스."""
        def __init__(self, x, y, size, damage, owner, duration_ms=120):
            self.x = float(x)
            self.y = float(y)
            self.size = int(size)
            self.damage = int(damage)
            self.owner = owner
            self.active = True
            self.gravity = 0
            self.created_at = pygame.time.get_ticks()
            self.duration_ms = int(duration_ms)
            self.last_damage_time = 0
            self.damage_interval = 0

        def update(self, world):
            try:
                if pygame.time.get_ticks() - self.created_at > self.duration_ms:
                    self.active = False
            except Exception:
                pass

        def draw(self, screen):
            try:
                s = max(2, int(self.size))
                surf = pygame.Surface((s, s), pygame.SRCALPHA)
                surf.fill((200, 180, 50, 120))
                screen.blit(surf, (int(self.x), int(self.y)))
            except Exception:
                pass

    def _make_hitbox(self, x, y, w, h, damage, owner):
        # 우선 프로젝트의 MeleeHitbox 시도 후 실패하면 _SimpleHitbox 반환
        try:
            hb = MeleeHitbox(x, y, w, h, damage, owner)
            # 보장 속성 추가
            if not hasattr(hb, "active"):
                hb.active = True
            if not hasattr(hb, "size"):
                hb.size = int(w)
            if not hasattr(hb, "update"):
                hb.update = lambda world: None
            if not hasattr(hb, "draw"):
                hb.draw = lambda screen: None
            return hb
        except Exception:
            return StaffStrikeSkill._SimpleHitbox(x, y, w, damage, owner, duration_ms=self.hitbox_duration_ms)

    def activate(self, user: dict, target: Any, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs) -> List:
        # ready/쿨다운 검사
        ready_fn = getattr(self, "ready", None)
        try:
            if callable(ready_fn) and not ready_fn():
                return []
        except Exception:
            return []

        # last_used 갱신
        if hasattr(self, "last_used"):
            try:
                self.last_used = pygame.time.get_ticks()
            except Exception:
                pass

        awakened = bool(skill_state.get("awakened", False)) if isinstance(skill_state, dict) else False
        size = self.awakened_hitbox_size if awakened else self.hitbox_size
        damage = self.awakened_damage if awakened else self.hitbox_damage

        ux = float(user.get("x", 0))
        uy = float(user.get("y", 0))
        facing = 1 if user.get("facing", 1) >= 0 else -1

        frontal_offset = int(size / 2) + 20
        hit_x = ux + facing * frontal_offset
        hit_y = uy

        hitbox = self._make_hitbox(hit_x, hit_y, size, size, damage, owner)
        if hitbox is None:
            return []

        # 선택적 속성 부여
        try:
            setattr(hitbox, "duration_ms", self.hitbox_duration_ms)
        except Exception:
            pass
        try:
            setattr(hitbox, "knockback", (facing * 8, -4))
        except Exception:
            pass

        # 이펙트 로드 및 추가
        self._load_assets_once()
        results: List[Any] = [hitbox]
        if self._effect_frames and AnimatedEffect is not None:
            try:
                ef = AnimatedEffect(frames=self._effect_frames, x=hit_x, y=hit_y, loop=False)
                results.append(ef)
            except Exception:
                try:
                    ef = AnimatedEffect(self._effect_frames, hit_x, hit_y, False)
                    results.append(ef)
                except Exception:
                    pass

        # 애니메이션 트리거
        if user_obj and hasattr(user_obj, "start_skill_animation"):
            try:
                user_obj.start_skill_animation(self.name)
            except Exception:
                pass

        return results


class PoisonPotionUltimate(UltimateSkillBase):
    def __init__(self, name: str, cooldown_ms: int):
        try:
            super().__init__(name, cooldown_ms=cooldown_ms, ult_cost=100, img_path=os.path.join(ASSET_PATH, "ultimate.png"))
        except TypeError:
            try:
                super().__init__(name, cooldown_ms=cooldown_ms)
            except Exception:
                super().__init__(name)
        self.ult_cost = getattr(self, "ult_cost", 100)
        self._assets_loaded = False
        self.projectile_img: Optional[pygame.Surface] = None

    def _load_assets_once(self):
        if self._assets_loaded:
            return
        proj_path = os.path.join(ASSET_PATH, "skill3.png")
        img = _safe_load_image(proj_path, size=(64, 64))
        if img is None:
            ult_path = os.path.join(ASSET_PATH, "ultimate.png")
            img = _safe_load_image(ult_path, size=(64, 64))
        self.projectile_img = img
        self._assets_loaded = True

    def activate(self, user: dict, target: Any, skill_state: dict, world: dict, user_obj=None, owner: str = "p1", **kwargs) -> List:
        # 준비/쿨다운 확인
        ready_fn = getattr(self, "ready", None)
        try:
            if callable(ready_fn) and not ready_fn():
                return []
        except Exception:
            return []

        # 궁극기 게이지 확인
        required = getattr(self, "ult_cost", 100)
        gauge = None
        gauge_key = None
        if isinstance(skill_state, dict):
            for key in ("ult", "ultimate_gauge", "ult_gauge", "ultimate"):
                if key in skill_state:
                    gauge = skill_state.get(key, 0)
                    gauge_key = key
                    break
        if gauge is None and isinstance(user, dict):
            for key in ("ult", "ultimate_gauge", "ult_gauge", "ultimate"):
                if key in user:
                    gauge = user.get(key, 0)
                    gauge_key = key
                    break
        if gauge is None:
            gauge = 0

        if gauge < required:
            return []

        # 게이지 차감
        try:
            if isinstance(skill_state, dict) and gauge_key in skill_state:
                skill_state[gauge_key] = max(0, skill_state.get(gauge_key, 0) - required)
            elif isinstance(user, dict) and gauge_key in user:
                user[gauge_key] = max(0, user.get(gauge_key, 0) - required)
        except Exception:
            pass

        if hasattr(self, "last_used"):
            try:
                self.last_used = pygame.time.get_ticks()
            except Exception:
                pass

        self._load_assets_once()

        ux = user.get("x", 0)
        uy = user.get("y", 0)
        facing = 1 if user.get("facing", 1) >= 0 else -1
        vx = facing * 14
        proj_x = ux + facing * 30
        proj_y = uy - 10
        base_damage = 20

        # Projectile 생성 방어
        base_proj = None
        try:
            base_proj = Projectile(x=proj_x, y=proj_y, vx=vx, img=self.projectile_img, damage=base_damage, owner=owner, size=48, gravity=0.25)
        except TypeError:
            try:
                base_proj = Projectile(proj_x, proj_y, vx, base_damage, owner)
            except Exception:
                base_proj = None

        if base_proj is None:
            # fallback: dict 기반 임시 투사체
            tmp = {"x": proj_x, "y": proj_y, "vx": vx, "size": 48, "damage": base_damage, "owner": owner, "gravity": 0.25, "active": True}
            proj = _ensure_compat(tmp, fallback_x=proj_x, fallback_y=proj_y, fallback_size=48, fallback_damage=base_damage, fallback_owner=owner)
        else:
            proj = _ensure_compat(base_proj, fallback_x=proj_x, fallback_y=proj_y, fallback_size=48, fallback_damage=base_damage, fallback_owner=owner)

        # 독 속성
        try:
            setattr(proj, "causes_poison", True)
            setattr(proj, "poison_duration", 2000)
            setattr(proj, "poison_dps", 0.015)
        except Exception:
            pass

        if user_obj and hasattr(user_obj, "start_skill_animation"):
            try:
                user_obj.start_skill_animation(self.name)
            except Exception:
                pass

        return [proj]
