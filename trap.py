# trap.py

class Trap:
  def __init__(self, x, y, damage):
    self.x = x
    self.y = y
    self.damage = damage
    self.active = True

  def trigger(self, player):
    if self.active and self.collides_with(player):
      player.take_damage(self.damage)
      self.active = False

  def collides_with(self, player):
    # 간단한 충돌 판정 (예시)
    return self.x == player.x and self.y == player.y

# main.py에서 사용 예시:
# from trap import Trap
# trap = Trap(100, 200, 10)
# trap.trigger(player)
