import pygame
import sys

pygame.mixer.init()
pygame.mixer.music.load("assets/bgm/Coldplay_Viva_La_Vida.mp3")
pygame.mixer.music.set_volume(0.5)

def title(screen):
  pygame.display.set_caption("Bounce Attack (REMASTERED) - Title Scene")

  if not pygame.mixer.music.get_busy():
    pygame.mixer.music.play(0)

  background = pygame.image.load("assets/img/background.png")
  background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
  screen.blit(background, (0, 0))

  button_rect = pygame.Rect(440, 620, 200, 60)

  font = pygame.font.Font("assets/font/NotoSansKR-Bold.ttf", 50)
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
      pygame.mixer.music.stop()
      return None
      
    if event.type == pygame.MOUSEBUTTONDOWN:
      if button_rect.collidepoint(event.pos):
        pygame.mixer.music.stop()
        return "Characters"

  return "Title"
