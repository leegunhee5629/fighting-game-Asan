import os
import pygame
import copy
from typing import Dict, Any, List, Tuple

# 📢 [핵심 수정 1] pygame.mixer.init() 제거. main.py에서 초기화됩니다.

# 📢 [추가] main.py에서 GAME_VOLUME을 가져와 사용합니다.
try:
    import main 
    SHARED_VOLUME = main.GAME_VOLUME
except (ImportError, AttributeError):
    # main 모듈이 없거나 GAME_VOLUME이 없을 경우 기본값 0.5 사용
    SHARED_VOLUME = 0.5 

# 📢 Pygame 폰트 및 믹서 초기화가 main.py에서 이미 되었어야 합니다.
# 필요한 경우, 안전을 위해 mixer만 초기화합니다. (main.py에 init이 있다면 불필요)
if not pygame.mixer.get_init():
    pygame.mixer.init()
    
# 📢 [수정]: 이 파일은 'Character' 씬의 로직과 캐릭터 데이터를 정의합니다.

character_config: Dict[str, Any] = {
    "character_list": [
        {"name": "이생선", "codename": "leesaengseon", "rect": pygame.Rect(40, 380, 85, 85)},
        {"name": "해골", "codename": "haegol", "rect": pygame.Rect(150, 380, 85, 85)},
        {"name": "조커", "codename": "joker", "rect": pygame.Rect(260, 380, 85, 85)},
        {"name": "아이스맨", "codename": "iceman", "rect": pygame.Rect(370, 380, 85, 85)},
        {"name": "마녀", "codename": "witch", "rect": pygame.Rect(480, 380, 85, 85)},
    ],
    "selected_1p": None,
    "selected_2p": None,
}

_default_skill_template = {
    "skill1": {"cooldown": 500, "last_used": 0, "active": False},
    "skill2": {"cooldown": 1000, "last_used": 0, "active": False},
    "ultimate": {"cooldown": 10000, "last_used": 0, "active": False},
}

character_skill_state: Dict[str, Dict[str, Any]] = {}

for c in [c["codename"] for c in character_config["character_list"]]:
    char_state = {k: v.copy() for k, v in _default_skill_template.items()}
    char_state["is_stunned"] = False # 기절 상태 플래그
    char_state["stun_end_time"] = 0  # 기절 종료 시간
    character_skill_state[c] = char_state

# 캐릭터별 쿨다운 튜닝
if "haegol" in character_skill_state:
    character_skill_state["haegol"]["skill1"]["cooldown"] = 500
    character_skill_state["haegol"]["skill2"]["cooldown"] = 1000
    character_skill_state["haegol"]["ultimate"]["cooldown"] = 10000
    
if "leesaengseon" in character_skill_state:
    character_skill_state["leesaengseon"]["skill1"]["cooldown"] = 600
    character_skill_state["leesaengseon"]["skill2"]["cooldown"] = 3000
    character_skill_state["leesaengseon"]["ultimate"]["cooldown"] = 15000

text_1p = None
text_2p = None
start_time = None
# 0: 대기, 1: P1 선택 중, 2: P2 선택 중, 3: 선택 완료 및 맵 이동 대기
process = 0 

def get_charactername_by_codename(codename: str | None) -> str | None:
    if not codename:
        return None
    for char in character_config["character_list"]:
        if char["codename"] == codename:
            return char["name"]
    return None

def _safe_load_image(path: str, size: Tuple[int, int] | None = None) -> pygame.Surface | None:
    if not path or not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        return None

def characters(screen: pygame.Surface, current_scene: str) -> str | None:
    global character_config, text_1p, text_2p, start_time, process

    # 📢 [핵심 수정]: process == 3 상태에서 초기화되는 버그 수정
    if current_scene == "Characters" and process == 0:
        character_config["selected_1p"] = None
        character_config["selected_2p"] = None
        start_time = pygame.time.get_ticks() 
        process = 1 # P1 선택 단계로 강제 진입

    # 배경 및 화면 설정
    pygame.display.set_caption("Bounce Attack (REMASTERED) - 캐릭터 선택")

    background = _safe_load_image("assets/img/characters.png", (screen.get_width(), screen.get_height()))
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill((30, 120, 60))

    try:
        font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 40)
        small_font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 24)
    except Exception:
        font = pygame.font.Font(None, 40)
        small_font = pygame.font.Font(None, 24)

    # elapsed 계산
    elapsed = pygame.time.get_ticks() - start_time if start_time is not None else 0

    # 단계별 문구 표시 및 다음 씬 전환 로직
    blink = (pygame.time.get_ticks() // 750) % 2

    if process == 1: # P1 선택 중
        text_1p = font.render("선택 준비", True, (255, 255, 0))
        text_2p = font.render("Player 2", True, (255, 255, 255))
        if blink:
            text_1p = font.render("", True, (0, 255, 0))
    
    elif process == 2: # P2 선택 중
        text_1p_name = get_charactername_by_codename(character_config["selected_1p"]) or "확정"
        text_1p = font.render(text_1p_name, True, (0, 255, 0))
        text_2p = font.render("선택 준비", True, (255, 255, 0))
        if blink:
            text_2p = font.render("", True, (0, 255, 0))
    
    elif process == 3: # 선택 완료, 맵 이동 대기
        text_1p_name = get_charactername_by_codename(character_config["selected_1p"]) or "오류"
        text_2p_name = get_charactername_by_codename(character_config["selected_2p"]) or "오류"
        text_1p = font.render(text_1p_name, True, (0, 255, 0))
        text_2p = font.render(text_2p_name, True, (0, 255, 0))
        
        # 선택 완료 후 딜레이 (3초 대기 후 맵 씬으로 이동)
        if elapsed > 3000:
            return "Maps"
    
    else: # 예외 처리 (process 0)
        text_1p = font.render("Player 1", True, (255, 255, 255))
        text_2p = font.render("Player 2", True, (255, 255, 255))


    # 텍스트 렌더링
    text_1p_rect = text_1p.get_rect(center=(300, 70))
    text_2p_rect = text_2p.get_rect(center=(screen.get_width() - 300, 70))
    screen.blit(text_1p, text_1p_rect)
    screen.blit(text_2p, text_2p_rect)

    # 마우스 위치로 hover 코드네임 계산
    mouse_pos = pygame.mouse.get_pos()
    hover_codename = None
    for char in character_config["character_list"]:
        is_hovered = char["rect"].collidepoint(mouse_pos)
        
        if is_hovered:
            hover_codename = char["codename"]

    # 미리보기 그리기
    def _draw_preview_for_player(player_idx, centerx, centery):
        # 확정된 선택
        sel = character_config["selected_1p"] if player_idx == 1 else character_config["selected_2p"]
        
        # 표시할 코드네임을 결정합니다.
        show_codename = None
        
        if process == 1 and player_idx == 1:
            # P1 선택 중: hover 또는 이미 선택된 것 표시
            show_codename = hover_codename or sel
        elif process == 2 and player_idx == 2:
            # P2 선택 중: hover 또는 이미 선택된 것 표시
            show_codename = hover_codename or sel
        else:
            # 확정된 선택만 표시
            show_codename = sel 

        if not show_codename:
            return

        path = f"assets/characters/{show_codename}/body.png"
        img = _safe_load_image(path, (200, 200))
        if img:
            screen.blit(img, img.get_rect(center=(centerx, centery)))
        else:
            # 📢 [UI 수정]: 이미지 로드 실패 시 이름만 빨간색으로 표시
            name = get_charactername_by_codename(show_codename) or show_codename
            label = small_font.render(f"No Image: {name}", True, (255, 0, 0)) # 빨간색으로 오류 표시
            screen.blit(label, label.get_rect(center=(centerx, centery)))

    _draw_preview_for_player(1, text_1p_rect.centerx, text_1p_rect.centery + 130)
    _draw_preview_for_player(2, text_2p_rect.centerx, text_2p_rect.centery + 130)

    # 이벤트 처리: 좌클릭으로 hover된 캐릭터를 확정
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
            
        # ESC 키로 타이틀 화면 복귀
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # 상태 초기화 및 Title 씬 복귀
            character_config["selected_1p"] = None
            character_config["selected_2p"] = None
            process = 0 # Title로 돌아갈 때는 0으로 초기화
            return "Title"
            
        # 초기 0.5초 딜레이 (elapsed > 500)는 유지하여 씬 로드 직후 실수로 클릭되는 것을 방지합니다.
        if event.type == pygame.MOUSEBUTTONDOWN and elapsed > 500: 
            if event.button == 1 and hover_codename:
                if process == 1:
                    # P1 선택 확정
                    character_config["selected_1p"] = hover_codename
                    process = 2 # 즉시 P2 선택 단계로 전환
                
                elif process == 2:
                    # P2 선택 확정 및 상태 변경
                    character_config["selected_2p"] = hover_codename
                    start_time = pygame.time.get_ticks() 
                    process = 3 # 선택 완료 단계로 전환 (3초 후 맵 이동)

    return "Characters"