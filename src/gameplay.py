import pygame
import copy
from scenes.characters import character_config, character_skill_state
from scenes.skills import get_skills_for_character
from animation import Character # Character 클래스 import

pygame.init()

def gameplay(screen, map_image_path):
    pygame.display.set_caption("Bounce Attack (REMASTERED) - Gameplay")
    background = pygame.image.load(map_image_path)
    background = pygame.transform.scale(background, (screen.get_width(), screen.get_height()))
    
    sel1 = character_config.get("selected_1p")
    sel2 = character_config.get("selected_2p")

    # 캐릭터 크기 상수 (animation.py와 동일하게 200x200 사용)
    CHAR_SIZE = 200
    screen_h = screen.get_height()

    # 모든 캐릭터가 동일하게 적용될 지면 높이 (수영장 바닥 높이)
    GROUND_Y = screen_h - CHAR_SIZE 
    
    p1_start_x = 100
    p2_start_x = screen.get_width() - 300 
    
    p1_char = Character(sel1, p1_start_x, GROUND_Y)
    p2_char = Character(sel2, p2_start_x, GROUND_Y)

    # p1, p2는 Character 객체의 상태 딕셔너리를 직접 참조합니다.
    p1 = p1_char.state
    p2 = p2_char.state

    # 스킬 객체 가져오기 (Skill 객체 리스트: [skill1, skill2, ultimate])
    p1_skills = get_skills_for_character(sel1) if sel1 else [None, None, None]
    p2_skills = get_skills_for_character(sel2) if sel2 else [None, None, None]

    p1_skill1 = p1_skills[0] # 근접 공격
    p1_skill2 = p1_skills[1] # 원거리 공격
    p1_ultimate = p1_skills[2] # 궁극기

    p2_skill1 = p2_skills[0]
    p2_skill2 = p2_skills[1]
    p2_ultimate = p2_skills[2]

    # 발사체 / 월드
    projectiles = []
    world = {"projectiles": projectiles, "screen_width": screen.get_width()}

    p1_skill_state = copy.deepcopy(character_skill_state.get(sel1, {}))
    p2_skill_state = copy.deepcopy(character_skill_state.get(sel2, {}))

    # 물리 상수
    speed = 6
    jump_power = -18
    gravity = 1
    
    font = pygame.font.Font(None, 30)
    
    clock = pygame.time.Clock()
    running = True
    
    def draw_hp_bar(screen, x, y, hp, color):
        """HP 바를 그립니다."""
        hp = max(0, min(100, hp))
        pygame.draw.rect(screen, (255, 0, 0), (x, y, 100, 10))
        pygame.draw.rect(screen, color, (x, y, hp, 10))

    def draw_ultimate_gauge(screen, x, y, gauge, color):
        """궁극기 게이지 바를 그립니다."""
        gauge = max(0, min(100, gauge))
        pygame.draw.rect(screen, (128, 128, 128), (x, y, 100, 10))
        
        # 궁극기 준비 완료 상태일 때 노란색 테두리
        if gauge >= 70:
            pygame.draw.rect(screen, (255, 255, 0), (x - 2, y - 2, 104, 14), 2)

        pygame.draw.rect(screen, color, (x, y, gauge, 10))
        
    def draw_awakening_status(screen, x, y, char_state, font):
        """각성 상태 타이머를 그립니다."""
        if char_state.get("is_awakened", False):
            end_time = char_state.get("awakening_end_time", 0)
            remaining_time_ms = max(0, end_time - pygame.time.get_ticks())
            remaining_time_s = remaining_time_ms / 1000
            
            text = font.render(f"각성: {remaining_time_s:.1f}s", True, (255, 255, 0))
            screen.blit(text, (x, y))


    def deal_damage(attacker, defender, base_damage):
        """
        데미지를 주고 게이지를 채웁니다. 
        공격자 버프(주는 피해 증가), 방어자 디버프(받는 피해 감소) 로직 포함.
        """
        
        # 1. 공격자 버프 적용 (주는 피해 50% 증가)
        damage_multiplier = 1.0
        if attacker.get("is_awakened", False):
            damage_multiplier += 0.5 # 1.5배

        # 2. 방어자 디버프 적용 (받는 피해 50% 감소)
        defense_multiplier = 1.0
        if defender.get("is_awakened", False):
            defense_multiplier -= 0.5 # 0.5배

        final_damage = base_damage * damage_multiplier * defense_multiplier
        final_damage = max(0, final_damage) # 데미지는 최소 0

        defender["hp"] -= final_damage
        if defender["hp"] < 0:
            defender["hp"] = 0
            
        # 게이지 충전
        attacker["ultimate_gauge"] = min(100, attacker["ultimate_gauge"] + 10)
        defender["ultimate_gauge"] = min(100, defender["ultimate_gauge"] + 5)


    def _safe_get_prop(obj, key, default_val=None):
        """객체 속성 또는 딕셔너리 키를 안전하게 반환합니다."""
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict):
            return obj.get(key, default_val)
        return default_val
    
    while running:
        dt = clock.tick(60) # delta time for updates
        
        screen.blit(background, (0, 0))
        keys = pygame.key.get_pressed()

        # 이벤트 처리 (게임 종료)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        # P1 이동 처리
        if keys[pygame.K_a]:
            p1["vx"] = -speed
        elif keys[pygame.K_d]:
            p1["vx"] = speed
        else:
            p1["vx"] = 0
        if keys[pygame.K_w] and p1["on_ground"]:
            p1["vy"] = jump_power
            p1["on_ground"] = False

        # P2 이동 처리
        if keys[pygame.K_LEFT]:
            p2["vx"] = -speed
        elif keys[pygame.K_RIGHT]:
            p2["vx"] = speed
        else:
            p2["vx"] = 0
        if keys[pygame.K_UP] and p2["on_ground"]:
            p2["vy"] = jump_power
            p2["on_ground"] = False

        # --- P1 스킬 입력 처리 (근거리: E, 원거리: R, 궁극기: S) ---
        if keys[pygame.K_e] and p1_skill1 and p1_skill1.ready(): # 근접 공격 (기술 1)
            p1_skill1.activate(p1, p2, p1_skill_state.get("skill1", {}), world, p1_char, owner="p1")
        if keys[pygame.K_r] and p1_skill2 and p1_skill2.ready(): # 원거리 공격 (기술 2)
            p1_skill2.activate(p1, p2, p1_skill_state.get("skill2", {}), world, p1_char, owner="p1")
        if keys[pygame.K_s] and p1_ultimate and p1_ultimate.ready(): # 궁극기
            p1_ultimate.activate(p1, p2, p1_skill_state.get("ultimate", {}), world, p1_char, owner="p1")
            
        # --- P2 스킬 입력 처리 (근거리: ENTER, 원거리: RSHIFT, 궁극기: DOWN) ---
        if keys[pygame.K_RETURN] and p2_skill1 and p2_skill1.ready(): # 근접 공격 (기술 1)
            p2_skill1.activate(p2, p1, p2_skill_state.get("skill1", {}), world, p2_char, owner="p2")
        if keys[pygame.K_RSHIFT] and p2_skill2 and p2_skill2.ready(): # 원거리 공격 (기술 2)
            p2_skill2.activate(p2, p1, p2_skill_state.get("skill2", {}), world, p2_char, owner="p2")
        if keys[pygame.K_DOWN] and p2_ultimate and p2_ultimate.ready(): # 궁극기
            p2_ultimate.activate(p2, p1, p2_skill_state.get("ultimate", {}), world, p2_char, owner="p2")

        # 물리 업데이트
        for char_state in [p1, p2]:
            char_state["vy"] += gravity
            char_state["x"] += char_state["vx"]
            char_state["y"] += char_state["vy"]

            # 지면 충돌 처리
            if char_state["y"] >= GROUND_Y:
                char_state["y"] = GROUND_Y
                char_state["vy"] = 0
                char_state["on_ground"] = True
                # 게이지 자동 회복 (점프/낙하 중이 아닐 때)
                char_state["ultimate_gauge"] = min(100, char_state["ultimate_gauge"] + 0.05)

            # 화면 경계 처리
            if char_state["x"] < 0:
                char_state["x"] = 0
            if char_state["x"] > screen.get_width() - CHAR_SIZE:
                char_state["x"] = screen.get_width() - CHAR_SIZE

        # 캐릭터 업데이트 (애니메이션, 타이머)
        p1_char.update(dt)
        p2_char.update(dt)

        # 발사체 업데이트
        new_projectiles = []
        for proj in projectiles:
            # skills.py의 Projectile.update/MeleeHitbox.update가 호출됨
            proj.update(world) 
            if proj.active:
                new_projectiles.append(proj)
        projectiles[:] = new_projectiles
        world["projectiles"] = projectiles # 갱신된 리스트 반영

        # 충돌 처리
        p1_rect = pygame.Rect(p1["x"], p1["y"], CHAR_SIZE, CHAR_SIZE)
        p2_rect = pygame.Rect(p2["x"], p2["y"], CHAR_SIZE, CHAR_SIZE)

        for proj in projectiles:
            # Projectile의 size를 사용하여 충돌 사각형 생성
            proj_rect = pygame.Rect(proj.x, proj.y, proj.size, proj.size) 
            
            # [수정] 이펙트는 사라지지 않도록 damage가 0보다 클 경우에만 비활성화합니다.
            is_damage_dealer = proj.damage > 0

            if proj.owner == "p1" and proj_rect.colliderect(p2_rect):
                deal_damage(p1, p2, proj.damage)
                if is_damage_dealer:
                    proj.active = False
            elif proj.owner == "p2" and proj_rect.colliderect(p1_rect):
                deal_damage(p2, p1, proj.damage)
                if is_damage_dealer:
                    proj.active = False
        
        # 무승부 판정 (충돌 처리)
        if p1_rect.colliderect(p2_rect) and p1_char.is_attacking and p2_char.is_attacking:
            # 서로 공격 중일 때 데미지 1씩 교환 (무승부 방지)
            deal_damage(p1, p2, 1) 
            deal_damage(p2, p1, 1)

        # 승리/패배 판정
        if p1["hp"] <= 0:
            return "p2_win" # P2 승리
        if p2["hp"] <= 0:
            return "p1_win" # P1 승리

        # 그리기
        p1_char.draw(screen)
        p2_char.draw(screen)

        for proj in projectiles:
            proj.draw(screen)
            
        # UI 그리기
        draw_hp_bar(screen, 50, 20, p1["hp"], (0, 255, 0))
        draw_hp_bar(screen, screen.get_width() - 150, 20, p2["hp"], (0, 255, 0))
        
        draw_ultimate_gauge(screen, 50, 40, p1["ultimate_gauge"], (0, 0, 255))
        draw_ultimate_gauge(screen, screen.get_width() - 150, 40, p2["ultimate_gauge"], (0, 0, 255))
        
        # 각성 상태 타이머 표시
        draw_awakening_status(screen, 50, 60, p1, font)
        draw_awakening_status(screen, screen.get_width() - 150, 60, p2, font)

        # FPS 표시 (디버깅용)
        # fps_text = font.render(f"FPS: {clock.get_fps():.1f}", True, (255, 255, 255))
        # screen.blit(fps_text, (10, screen.get_height() - 30))

        pygame.display.flip()

    return None
