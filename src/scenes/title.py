import pygame
# 📢 [추가]: 캐릭터 선택 상태 초기화를 위해 scenes.characters 모듈을 가져옵니다.
import scenes.characters

def title(screen, current_scene):
    pygame.display.set_caption("Bounce Attack (REMASTERED)")

    background = pygame.image.load("assets/img/background.png")
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
    screen.blit(background, (0, 0))

    button_rect = pygame.Rect(440, 620, 200, 60)

    try:
        font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 50)
    except Exception:
        font = pygame.font.Font(None, 50)
        
    text_str = "게임 시작"

    blink = (pygame.time.get_ticks() // 750) % 2

    if blink:
        outline_color = (0, 0, 0)
        offsets = [-3, -2, -1, 0, 1, 2, 3]
        for dx in offsets:
            for dy in offsets:
                if dx != 0 or dy != 0:
                    outline = font.render(text_str, True, outline_color)
                    outline_rect = outline.get_rect(center=(button_rect.centerx + dx, button_rect.centery + dy + 20))
                    screen.blit(outline, outline_rect)

        text = font.render(text_str, True, (255, 255, 255))
        text_rect = text.get_rect(center=(button_rect.centerx, button_rect.centery + 20))
        screen.blit(text, text_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                # 📢 [핵심 수정]: 캐릭터 선택 씬으로 전환하기 전에 모든 데이터를 초기화합니다.
                scenes.characters.character_config["selected_1p"] = None
                scenes.characters.character_config["selected_2p"] = None
                scenes.characters.process = 0       # P1 선택 단계로 강제 진입
                scenes.characters.start_time = None # Characters 씬에서 다시 설정하도록 초기화

                return "Characters"

    return "Title"