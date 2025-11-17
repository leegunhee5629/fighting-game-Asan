import pygame
import sys
import os 

from scenes.title import title
from scenes.characters import characters
from scenes.maps import maps
from maps.loading import map_loading

from gameplay import gameplay
from scenes.maps import map_config

# BGM 경로 정의
BGM_BATTLE_PATH = "assets/bgm/BGM07battle2.wav" # 사용하지 않지만 경로 정의는 유지
BGM_MENU_PATH = "assets/bgm/F1_starting_grid.mp3" # 통합 BGM

pygame.init()

GAME_VOLUME = 0.05 
pygame.mixer.music.set_volume(GAME_VOLUME)

screen = pygame.display.set_mode((1080, 720))

FPS = 120
clock = pygame.time.Clock()

current_screen = "Title"
past_screen = "Title"

screens = {
    "Title": title,
    "Characters": characters,
    "Maps": maps,
    "map_loading": map_loading,
}

FULLSCREEN_SCREENS = ["gameplay"]

# 📢 [수정 유지] Title을 제외하고 BGM을 계속 재생할 씬 목록 정의 (gameplay 포함)
CONTINUOUS_BGM_SCREENS = ["Characters", "Maps", "map_loading", "gameplay"]


while current_screen:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            current_screen = None
            continue
    
    
    # A. 화면 크기/마우스 전환 로직 (변화 없음)
    is_gameplay_mode = current_screen.lower() in FULLSCREEN_SCREENS
    
    if current_screen != past_screen or (is_gameplay_mode and not (screen.get_flags() & pygame.FULLSCREEN)):
        
        if is_gameplay_mode:
            if screen.get_flags() & pygame.FULLSCREEN == 0:
                pygame.mouse.set_visible(False)
                screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
        else:
            if screen.get_flags() & pygame.FULLSCREEN != 0:
                pygame.mouse.set_visible(True)
                screen = pygame.display.set_mode((1080, 720))
                
        past_screen = current_screen
    
    # B. 씬 실행 로직
    
    # 📢 [BGM 통합 로직]: Title에서 BGM 씬으로 넘어올 때 BGM을 켜줍니다.
    if current_screen in CONTINUOUS_BGM_SCREENS and not pygame.mixer.music.get_busy() and os.path.exists(BGM_MENU_PATH):
        try:
            # 혹시 모를 잔여 음악 정리
            if pygame.mixer.music.get_busy():
                 pygame.mixer.music.stop()
                 
            pygame.mixer.music.load(BGM_MENU_PATH)
            pygame.mixer.music.set_volume(GAME_VOLUME) 
            pygame.mixer.music.play(-1, fade_ms=1000) 
        except pygame.error as e:
            print(f"Menu BGM 로드/재생 오류: {e}")
            
            
    if current_screen == "gameplay":
        
        # 📢 [핵심 수정]: gameplay 씬 진입 직전, BGM이 중단되었다면 즉시 메뉴 BGM을 복구/재생
        # 이 코드는 gameplay 내부에서 BGM이 중단되는 경우를 방어하여 BGM 연속성을 보장합니다.
        if not pygame.mixer.music.get_busy() and os.path.exists(BGM_MENU_PATH):
            try:
                # 안전하게 중지 후 다시 로드 및 재생
                pygame.mixer.music.load(BGM_MENU_PATH)
                pygame.mixer.music.set_volume(GAME_VOLUME)
                # 빠른 복구를 위해 페이드 시간을 줄입니다.
                pygame.mixer.music.play(-1, fade_ms=100) 
            except pygame.error as e:
                print(f"Gameplay BGM 복구 오류: {e}")
                
        
        selected_map_codename = map_config['selected_map']
        map_image_path = f"assets/maps/{selected_map_codename}.png"
        
        next_screen = gameplay(screen, map_image_path)
            
        current_screen = next_screen


    elif current_screen in screens:
        
        # Title 씬으로 돌아갈 때만 BGM 중지
        if current_screen == "Title" and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
        # Title, Characters, Maps, map_loading 같은 일반 씬 실행
        current_screen = screens[current_screen](screen, current_screen)
    
    else:
        current_screen = None

    # C. 프레임 및 업데이트
    clock.tick(FPS)
    if pygame.display.get_init():
        pygame.display.update()

pygame.quit()
sys.exit()