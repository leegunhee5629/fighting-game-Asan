import pygame

def title(screen, current_scene):
  pygame.display.set_caption("Bounce Attack (REMASTERED)")

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
      return None
      
    if event.type == pygame.MOUSEBUTTONDOWN:
      if button_rect.collidepoint(event.pos):
        return "Characters"

  return "Title"