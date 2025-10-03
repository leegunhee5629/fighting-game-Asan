import pygame
import sys

pygame.init()

abs = 'asb'

# 기본 설정
WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2인 대전 격투 게임")
clock = pygame.time.Clock()

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)

# 폰트
font = pygame.font.SysFont(None, 48)

# 캐릭터 데이터 (단순 색상 박스로 표현)
characters = [
    {"name": "캐릭터1", "color": RED},
    {"name": "캐릭터2", "color": BLUE},
    {"name": "캐릭터3", "color": GREEN},
    {"name": "캐릭터4", "color": (200, 200, 0)},
    {"name": "캐릭터5", "color": (200, 0, 200)},
]

# 플레이어 상태
class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, 50, 100)
        self.color = color
        self.vel = 5
        self.jump_power = 15
        self.on_ground = True
        self.y_vel = 0
        self.controls = controls
        self.gauge = 0
        self.blocking = False

    def handle_input(self, keys):
        # 이동
        if keys[self.controls["left"]]:
            self.rect.x -= self.vel
        if keys[self.controls["right"]]:
            self.rect.x += self.vel

        # 점프
        if keys[self.controls["jump"]] and self.on_ground:
            self.y_vel = -self.jump_power
            self.on_ground = False

        # 가드
        self.blocking = keys[self.controls["guard"]]

    def update(self):
        # 중력 적용
        self.y_vel += 1
        self.rect.y += self.y_vel

        # 바닥 충돌
        if self.rect.bottom >= HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.y_vel = 0
            self.on_ground = True

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        if self.blocking:
            pygame.draw.rect(surface, WHITE, self.rect, 5)

# 조작키 설정
p1_controls = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "jump": pygame.K_w,
    "guard": pygame.K_s,
    "attack": pygame.K_h,
    "skill1": pygame.K_q,
    "skill2": pygame.K_r,
    "ult": pygame.K_j,
}

p2_controls = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "jump": pygame.K_UP,
    "guard": pygame.K_DOWN,
    "attack": pygame.K_KP0,
    "skill1": pygame.K_KP1,
    "skill2": pygame.K_KP2,
    "ult": pygame.K_KP3,
}

# 캐릭터 선택 화면
def character_select():
    p1_choice, p2_choice = None, None
    selecting_p1 = True
    cursor = 0

    while True:
        screen.fill(BLACK)
        title = font.render("캐릭터 선택", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        # 캐릭터 표시
        for i, char in enumerate(characters):
            x = 100 + i*120
            y = 200
            rect = pygame.Rect(x, y, 80, 80)
            pygame.draw.rect(screen, char["color"], rect)
            name = font.render(char["name"], True, WHITE)
            screen.blit(name, (x, y+90))
            if i == cursor:
                pygame.draw.rect(screen, WHITE, rect, 5)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if selecting_p1:
                    if event.key == pygame.K_a:
                        cursor = (cursor - 1) % len(characters)
                    elif event.key == pygame.K_d:
                        cursor = (cursor + 1) % len(characters)
                    elif event.key == pygame.K_h:
                        p1_choice = characters[cursor]
                        selecting_p1 = False
                        cursor = 0
                else:
                    if event.key == pygame.K_LEFT:
                        cursor = (cursor - 1) % len(characters)
                    elif event.key == pygame.K_RIGHT:
                        cursor = (cursor + 1) % len(characters)
                    elif event.key == pygame.K_KP0 or event.key == pygame.K_n:
                        p2_choice = characters[cursor]
                        return p1_choice, p2_choice

# 메인 게임 루프
def game_loop(p1_char, p2_char):
    p1 = Player(200, HEIGHT-150, p1_char["color"], p1_controls)
    p2 = Player(600, HEIGHT-150, p2_char["color"], p2_controls)

    running = True
    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        p1.handle_input(keys)
        p2.handle_input(keys)

        p1.update()
        p2.update()

        p1.draw(screen)
        p2.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    p1_char, p2_char = character_select()
    game_loop(p1_char, p2_char)
