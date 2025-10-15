import pygame
from scenes.characters import character_config

class Player:
    def __init__(self, codename, x, y, controls):
        self.codename = codename
        self.x = x
        self.y = y
        self.speed = 5
        self.controls = controls
        self.image = pygame.image.load(f"assets/characters/{codename}/body.png")
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def handle_input(self, keys):
        if keys[self.controls['left']]:
            self.x -= self.speed
        if keys[self.controls['right']]:
            self.x += self.speed
        if keys[self.controls['up']]:
            self.y -= self.speed
        if keys[self.controls['down']]:
            self.y += self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

def gameplay(screen, background_img):
    # 배경 그리기
    background = pygame.image.load(background_img)
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
    screen.blit(background, (0, 0))

    # 캐릭터 선택 정보 가져오기
    p1_code = character_config["selected_1p"] or "leesaengseon"
    p2_code = character_config["selected_2p"] or "haegol"

    # 플레이어 객체 생성 (최초 1회만)
    if not hasattr(gameplay, "players"):
        gameplay.players = [
            Player(p1_code, 300, 500, {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s}),
            Player(p2_code, 800, 500, {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP, 'down': pygame.K_DOWN}),
        ]

    keys = pygame.key.get_pressed()
    for player in gameplay.players:
        player.handle_input(keys)
        player.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "Title"

    return "swimming_pool"  # 맵 이름에 따라 다르게 반환 가능