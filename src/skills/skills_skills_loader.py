# skills/skills_loader.py (수정)

from typing import List
# 각 캐릭터별 스킬 클래스를 임포트합니다.
from .haegol_skills import HaegolSwingSkill, HaegolBoneSkill, HaegolUltimateSkill
from .leesaengseon_skills import LeesaengseonFishSkill, LeesaengseonBombSkill, LeesaengseonUltimateSkill
from .joker_skills import JokerGunTossSkill, JokerConfusionBulletSkill, JokerUltimateGasSkill
# 🧊 아이스맨 스킬 임포트
from .iceman_skills import IcemanPunchSkill, IcemanDashSkill, IcemanUltimateSkill
from .skills_base import Skill # 타입 힌트용

def get_skills_for_character(codename: str) -> List[Skill]:
    """캐릭터 코드명에 따른 스킬 객체 리스트 [skill1, skill2, ultimate] 반환"""
    if codename == "haegol":
        swing_skill = HaegolSwingSkill(name="haegol_swing", cooldown_ms=500) 
        bone_skill = HaegolBoneSkill(name="haegol_bone", cooldown_ms=1000) 
        ultimate_skill = HaegolUltimateSkill(name="haegol_ultimate", cooldown_ms=100) 
        return [swing_skill, bone_skill, ultimate_skill]
        
    elif codename == "leesaengseon":
        fish_skill = LeesaengseonFishSkill(name="leesaengseon_fish", cooldown_ms=600) 
        bomb_skill = LeesaengseonBombSkill(name="leesaengseon_bomb", cooldown_ms=3000) 
        ultimate_skill = LeesaengseonUltimateSkill(name="leesaengseon_ultimate", cooldown_ms=150) 
        return [fish_skill, bomb_skill, ultimate_skill]
        
    elif codename == "joker":
        gun_toss_skill = JokerGunTossSkill(name="joker_gun_toss", cooldown_ms=1500) 
        confusion_bullet_skill = JokerConfusionBulletSkill(name="joker_confusion_bullet", cooldown_ms=5000) 
        ultimate_gas_skill = JokerUltimateGasSkill(name="joker_ultimate_gas", cooldown_ms=180) 
        return [gun_toss_skill, confusion_bullet_skill, ultimate_gas_skill]
    # 🧊 Iceman 스킬 추가
    elif codename == "iceman":
        punch_skill = IcemanPunchSkill(name="iceman_punch", cooldown_ms=500)
        dash_skill = IcemanDashSkill(name="iceman_dash", cooldown_ms=3000)
        ultimate_skill = IcemanUltimateSkill(name="iceman_ultimate", cooldown_ms=180)
        return [punch_skill, dash_skill, ultimate_skill]
        
    return []