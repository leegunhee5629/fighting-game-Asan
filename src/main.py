import pygame

import sys

from scenes.title import title

from scenes.characters import characters

from scenes.maps import maps

from maps.loading import map_loading



from gameplay import gameplay

from scenes.maps import map_config



pygame.init()



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



# 풀스크린을 사용할 씬 목록을 명확히 정의합니다.

FULLSCREEN_SCREENS = ["gameplay"]



while current_screen:

   

    # print(f"DEBUG: Current Screen = {current_screen}, Past Screen = {past_screen}") # <--- 디버그용 출력



    # 1. 매 프레임마다 화면을 검은색으로 초기화

    # (각 씬 내부에서 처리하지만, 혹시 몰라 메인 루프 시작 시에도 호출 가능)

    # screen.fill((0, 0, 0))

   

    # A. 화면 크기/마우스 전환 로직 (씬 이름 기반으로 명확하게 수정)

    is_gameplay_mode = current_screen.lower() in FULLSCREEN_SCREENS

   

    # 씬 전환이 일어났거나, 현재 씬이 풀스크린 모드여야 하는데 현재 창 모드인 경우

    if current_screen != past_screen or (is_gameplay_mode and not (screen.get_flags() & pygame.FULLSCREEN)):

       

        if is_gameplay_mode:

            # 전투 씬 진입: 풀스크린 (1920x1080)

            if screen.get_flags() & pygame.FULLSCREEN == 0:

                # print("DEBUG: Switching to FULLSCREEN") # 디버그용

                pygame.mouse.set_visible(False)

                # 현재 시스템 해상도에 맞추어 풀스크린으로 전환됩니다.

                screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)

        else:

            # 메뉴/로딩 씬 진입: 창 모드 (1080x720)

            if screen.get_flags() & pygame.FULLSCREEN != 0:

                # print("DEBUG: Switching to WINDOWED") # 디버그용

                pygame.mouse.set_visible(True)

                screen = pygame.display.set_mode((1080, 720))

               

        past_screen = current_screen

   

    # B. 씬 실행 로직

    if current_screen == "gameplay":

        # print("DEBUG: Calling gameplay function") # 디버그용

        # 맵 로딩이 완료되면 "gameplay" 씬으로 진입합니다.

        selected_map_codename = map_config['selected_map']

        map_image_path = f"assets/maps/{selected_map_codename}.png"

       

        # gameplay 함수를 직접 호출하고 다음 씬을 받습니다.

        current_screen = gameplay(screen, map_image_path)



    elif current_screen in screens:

        # Title, Characters, Maps, map_loading 같은 일반 씬 실행

        current_screen = screens[current_screen](screen, current_screen)

   

    else:

        # 알 수 없는 씬 이름이 반환되면 종료

        current_screen = None



    # C. 프레임 및 업데이트

    clock.tick(FPS)

    if pygame.display.get_init():

        pygame.display.update()



pygame.quit()

sys.exit()

