import pygame
import random
import time
import math

pygame.init()

class SpaceDodgerAndroid:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_info = pygame.display.Info()
        self.screen_width = self.screen_info.current_w
        self.screen_height = self.screen_info.current_h
        pygame.display.set_caption("Space Dodger")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, int(self.screen_height * 0.04))
        
        # Player properties
        self.player_pos = [self.screen_width // 2, self.screen_height * 0.8]
        self.player_size = int(self.screen_height * 0.07)
        self.dragging = False
        self.player_shape = 'triangle'
        self.player_color = (0, 255, 0)
        self.shield_active = False
        self.shield_time = 0
        self.player_speed = 1
        self.credits = 0
        
        # Weapon system
        self.projectiles = []
        self.shoot_cooldown = 0
        self.current_gun = 'laser'
        
        # Skills
        self.dash_cooldown = 0
        self.emp_cooldown = 0
        self.overcharge_cooldown = 0
        self.overcharge_active = False
        self.overcharge_time = 0
        
        # Game objects
        self.asteroids = []
        self.stars = []
        self.power_ups = []
        self.particles = []
        self.black_holes = []
        self.background_stars = [(random.randint(0, self.screen_width), random.randint(0, self.screen_height), random.uniform(1, 3)) for _ in range(50)]
        self.planets = [(random.randint(0, self.screen_width), -50, random.randint(30, 80), random.choice([(100, 100, 255), (200, 100, 50)])) for _ in range(3)]
        self.score = 0
        self.lives = 3
        self.game_time = time.time()
        self.high_score = self.load_high_score()
        self.leaderboard = self.load_leaderboard()
        
        # Achievements & Missions
        self.achievements = {'survive_5min': False, 'destroy_10': False, 'beat_boss': False}
        self.missions = {'destroy_20_plasma': False, 'survive_2min_no_shield': False}
        self.asteroids_destroyed = 0
        self.score_multiplier = 1
        self.time_without_shield = 0
        
        # Colors
        self.bg_color = (0, 0, 20)
        self.asteroid_color = (150, 150, 150)
        self.star_color = (255, 255, 0)
        self.shield_color = (0, 255, 255)
        
        # Game settings
        self.asteroid_spawn_rate = 60
        self.star_spawn_rate = 120
        self.power_up_spawn_rate = 300
        self.black_hole_spawn_rate = 600
        self.frame_count = 0
        self.boss_active = False
        self.boss = None
        self.paused = False
        self.show_customization = True
        self.endless_mode = False
        self.screen_shake = 0
        
        # Upgrades
        self.upgrades = {'projectile_speed': 1.0, 'shield_duration': 5, 'skill_cooldown': 1.0}
        
        # New Power-Up States
        self.invincibility = False
        self.time_slow = False
        self.clone_active = False
        
        # Optimization flags
        self.max_particles = 200  # Limit particle count for performance

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))

    def load_leaderboard(self):
        try:
            with open("leaderboard.txt", "r") as f:
                return sorted([int(line.strip()) for line in f.readlines()], reverse=True)[:5]
        except:
            return [0, 0, 0, 0, 0]

    def save_leaderboard(self):
        self.leaderboard.append(self.score)
        self.leaderboard = sorted(self.leaderboard, reverse=True)[:5]
        with open("leaderboard.txt", "w") as f:
            for score in self.leaderboard:
                f.write(f"{score}\n")

    def spawn_asteroid(self):
        size = random.randint(int(self.screen_height * 0.03), int(self.screen_height * 0.08))
        x = random.randint(0, self.screen_width - size)
        self.asteroids.append({
            'pos': [x, -size], 
            'size': size, 
            'speed': random.uniform(2, 4), 
            'disabled': False,
            'trail': []  # For fire trail effect
        })

    def spawn_star(self):
        size = int(self.screen_height * 0.02)
        x = random.randint(0, self.screen_width - size)
        self.stars.append({'pos': [x, -size], 'size': size, 'speed': 3})

    def spawn_power_up(self):
        size = int(self.screen_height * 0.03)
        x = random.randint(0, self.screen_width - size)
        types = ['shield', 'speed', 'multiplier', 'time_slow', 'invincibility', 'clone']
        self.power_ups.append({'pos': [x, -size], 'size': size, 'speed': 2, 'type': random.choice(types)})

    def spawn_black_hole(self):
        size = random.randint(30, 50)
        x = random.randint(size, self.screen_width - size)
        self.black_holes.append({'pos': [x, -size], 'size': size, 'duration': 300})

    def spawn_boss(self):
        self.boss = {'pos': [self.screen_width // 2, -100], 'size': 100, 'speed': 1, 'health': 10, 'phase': 1}
        self.boss_active = True

    def spawn_projectile(self):
        if self.shoot_cooldown <= 0:
            speed_boost = self.upgrades['projectile_speed']
            proj_pos = [self.player_pos[0], self.player_pos[1] - self.player_size]
            if self.current_gun == 'laser':
                damage = 2 if self.overcharge_active else 1
                self.projectiles.append({'pos': proj_pos.copy(), 'speed': 5 * speed_boost, 'size': 5, 'damage': damage, 'color': (255, 255, 255)})
                self.shoot_cooldown = 10 if self.overcharge_active else 20
            elif self.current_gun == 'plasma':
                damage = 4 if self.overcharge_active else 2
                self.projectiles.append({'pos': proj_pos.copy(), 'speed': 8 * speed_boost, 'size': 10, 'damage': damage, 'color': (255, 0, 255)})
                self.shoot_cooldown = 15 if self.overcharge_active else 30
            elif self.current_gun == 'homing':
                damage = 3 if self.overcharge_active else 1
                target = min(self.asteroids, key=lambda a: ((a['pos'][0] - proj_pos[0])**2 + (a['pos'][1] - proj_pos[1])**2)**0.5) if self.asteroids else None
                self.projectiles.append({'pos': proj_pos.copy(), 'speed': 6 * speed_boost, 'size': 7, 'damage': damage, 'color': (0, 255, 0), 'target': target})
                self.shoot_cooldown = 25
            elif self.current_gun == 'spread':
                damage = 1 if self.overcharge_active else 0.5
                for angle in [-20, 0, 20]:
                    self.projectiles.append({'pos': proj_pos.copy(), 'speed': 5 * speed_boost, 'size': 5, 'damage': damage, 'color': (255, 255, 0), 'angle': angle})
                self.shoot_cooldown = 20
            elif self.current_gun == 'gravity':
                self.projectiles.append({'pos': proj_pos.copy(), 'speed': 4 * speed_boost, 'size': 15, 'damage': 0, 'color': (150, 0, 255), 'effect': 'push'})
                self.shoot_cooldown = 40

    def update_projectiles(self):
        for proj in self.projectiles[:]:
            if proj.get('angle'):
                proj['pos'][0] += proj['speed'] * (proj['angle'] / 20)
                proj['pos'][1] -= proj['speed']
            elif proj.get('target'):
                if proj['target'] in self.asteroids:
                    dx = proj['target']['pos'][0] - proj['pos'][0]
                    dy = proj['target']['pos'][1] - proj['pos'][1]
                    dist = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
                    proj['pos'][0] += proj['speed'] * dx / dist
                    proj['pos'][1] += proj['speed'] * dy / dist
                else:
                    proj['pos'][1] -= proj['speed']
            else:
                proj['pos'][1] -= proj['speed']

            if proj['pos'][1] < 0:
                self.projectiles.remove(proj)
                continue

            if proj.get('effect') == 'push':
                for asteroid in self.asteroids:
                    dist = ((proj['pos'][0] - asteroid['pos'][0])**2 + (proj['pos'][1] - asteroid['pos'][1])**2)**0.5
                    if dist < 100:
                        asteroid['pos'][1] += 5
                self.projectiles.remove(proj)
                continue

            for asteroid in self.asteroids[:]:
                if ((proj['pos'][0] - asteroid['pos'][0])**2 + (proj['pos'][1] - asteroid['pos'][1])**2)**0.5 < asteroid['size'] and not asteroid['disabled']:
                    self.projectiles.remove(proj)
                    # Enhanced explosion with fire effect
                    self.particles.extend([
                        {'pos': asteroid['pos'].copy(), 'size': random.randint(3, 8), 'color': (255, random.randint(50, 150), 0), 'speed': [random.uniform(-2, 2), random.uniform(-2, 2)]}
                        for _ in range(10)
                    ])
                    self.screen_shake = 5
                    self.asteroids.remove(asteroid)
                    self.score += (5 if proj['damage'] <= 1 else 10) * self.score_multiplier
                    self.asteroids_destroyed += 1
                    if self.current_gun == 'plasma' and self.asteroids_destroyed >= 20:
                        self.missions['destroy_20_plasma'] = True
                    if self.asteroids_destroyed >= 10:
                        self.achievements['destroy_10'] = True
                    break
            else:  # Only check boss if no asteroid hit
                if self.boss_active and ((proj['pos'][0] - self.boss['pos'][0])**2 + (proj['pos'][1] - self.boss['pos'][1])**2)**0.5 < self.boss['size']:
                    self.projectiles.remove(proj)
                    self.particles.extend([
                        {'pos': self.boss['pos'].copy(), 'size': random.randint(5, 10), 'color': (255, random.randint(50, 150), 0), 'speed': [random.uniform(-3, 3), random.uniform(-3, 3)]}
                        for _ in range(15)
                    ])
                    self.screen_shake = 10
                    self.boss['health'] -= proj['damage']
                    if self.boss['health'] <= 7 and self.boss['phase'] == 1:
                        self.boss['phase'] = 2
                        self.boss['speed'] = 2
                    elif self.boss['health'] <= 3 and self.boss['phase'] == 2:
                        self.boss['phase'] = 3
                    if self.boss['health'] <= 0:
                        self.score += 50 * self.score_multiplier
                        self.boss_active = False
                        self.achievements['beat_boss'] = True

    def update_boss(self):
        if self.boss_active:
            if self.boss['phase'] == 3 and self.frame_count % 20 == 0:
                self.projectiles.append({'pos': self.boss['pos'].copy(), 'speed': 5, 'size': 5, 'damage': 1, 'color': (255, 0, 0)})

    def draw_projectiles(self):
        for proj in self.projectiles:
            pygame.draw.rect(self.screen, proj['color'], (proj['pos'][0] - proj['size']//2, proj['pos'][1], proj['size'], proj['size'] * 2))
            # Add glow effect
            pygame.draw.circle(self.screen, (255, 255, 255, 50), (int(proj['pos'][0]), int(proj['pos'][1])), proj['size'] + 2, 1)

    def draw_player(self):
        if self.player_shape == 'triangle':
            points = [
                (self.player_pos[0], self.player_pos[1] - self.player_size//2),
                (self.player_pos[0] - self.player_size//2, self.player_pos[1] + self.player_size//2),
                (self.player_pos[0] + self.player_size//2, self.player_pos[1] + self.player_size//2)
            ]
            pygame.draw.polygon(self.screen, self.player_color, points)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(self.player_pos[0]), int(self.player_pos[1] - self.player_size//4)), 5)
        elif self.player_shape == 'circle':
            pygame.draw.circle(self.screen, self.player_color, (int(self.player_pos[0]), int(self.player_pos[1])), self.player_size//2)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(self.player_pos[0]), int(self.player_pos[1] - self.player_size//4)), 5)
        if self.shield_active:
            pygame.draw.circle(self.screen, self.shield_color, (int(self.player_pos[0]), int(self.player_pos[1])), self.player_size//2 + 5, 2)
        self.particles.append({'pos': [self.player_pos[0], self.player_pos[1] + self.player_size//2], 'size': 3, 'color': (255, 100, 0), 'speed': [0, 2]})

    def draw_asteroid(self, asteroid):
        # Add trail effect
        asteroid['trail'].append(asteroid['pos'].copy())
        if len(asteroid['trail']) > 5:
            asteroid['trail'].pop(0)
        for i, pos in enumerate(asteroid['trail']):
            alpha = (i + 1) * 20
            pygame.draw.circle(self.screen, (255, 100, 0, alpha), (int(pos[0]), int(pos[1])), int(asteroid['size'] * (0.5 - i * 0.1)))
        
        color = (100, 100, 100) if asteroid['disabled'] else self.asteroid_color
        pygame.draw.circle(self.screen, color, (int(asteroid['pos'][0]), int(asteroid['pos'][1])), asteroid['size'])
        # Add glow effect
        pygame.draw.circle(self.screen, (255, 150, 0, 50), (int(asteroid['pos'][0]), int(asteroid['pos'][1])), asteroid['size'] + 2, 1)

    def draw_star(self, star):
        pygame.draw.circle(self.screen, self.star_color, (int(star['pos'][0]), int(star['pos'][1])), star['size'])

    def draw_power_up(self, power_up):
        colors = {'shield': self.shield_color, 'speed': (255, 165, 0), 'multiplier': (255, 0, 255), 'time_slow': (0, 0, 255), 'invincibility': (255, 255, 255), 'clone': (150, 150, 150)}
        pygame.draw.circle(self.screen, colors[power_up['type']], (int(power_up['pos'][0]), int(power_up['pos'][1])), power_up['size'])

    def draw_black_hole(self, black_hole):
        pygame.draw.circle(self.screen, (0, 0, 0), (int(black_hole['pos'][0]), int(black_hole['pos'][1])), black_hole['size'])
        pygame.draw.circle(self.screen, (100, 0, 100), (int(black_hole['pos'][0]), int(black_hole['pos'][1])), black_hole['size'], 2)

    def draw_boss(self):
        pygame.draw.circle(self.screen, (255, 0, 0), (int(self.boss['pos'][0]), int(self.boss['pos'][1])), self.boss['size'])
        health_text = self.font.render(f"HP: {self.boss['health']}", True, (255, 255, 255))
        self.screen.blit(health_text, (self.boss['pos'][0] - 20, self.boss['pos'][1] - self.boss['size'] - 20))

    def draw_particles(self):
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]  # Limit particles
        for particle in self.particles[:]:
            particle['pos'][0] += particle['speed'][0]
            particle['pos'][1] += particle['speed'][1]
            particle['size'] -= 0.2
            if particle['size'] <= 0:
                self.particles.remove(particle)
                continue
            pygame.draw.circle(self.screen, particle['color'], (int(particle['pos'][0]), int(particle['pos'][1])), int(particle['size']))

    def draw_background(self):
        for i, (x, y, speed) in enumerate(self.background_stars):
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), 2)
            self.background_stars[i] = (x, y + speed, speed)
            if y > self.screen_height:
                self.background_stars[i] = (x, -2, speed)
        for i, (x, y, size, color) in enumerate(self.planets):
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)
            self.planets[i] = (x, y + 0.5, size, color)
            if y > self.screen_height + size:
                self.planets[i] = (random.randint(0, self.screen_width), -size, size, color)

    def check_collision(self, obj, is_star=False, is_power_up=False):
        obj_x, obj_y = obj['pos']
        obj_size = obj['size']
        px, py = self.player_pos
        distance = ((px - obj_x) ** 2 + (py - obj_y) ** 2) ** 0.5
        if distance < (self.player_size/2 + obj_size):
            if is_star:
                self.score += 10 * self.score_multiplier
                self.particles.extend([{'pos': [px, py], 'size': 5, 'color': self.star_color, 'speed': [random.uniform(-1, 1), random.uniform(-1, 1)]} for _ in range(5)])
                return True
            elif is_power_up:
                if obj['type'] == 'shield':
                    self.shield_active = True
                    self.shield_time = time.time()
                elif obj['type'] == 'speed':
                    self.player_speed = 2
                    self.speed_time = time.time()
                elif obj['type'] == 'multiplier':
                    self.score_multiplier = 2
                    self.multiplier_time = time.time()
                elif obj['type'] == 'time_slow':
                    self.time_slow = True
                    self.time_slow_time = time.time()
                elif obj['type'] == 'invincibility':
                    self.invincibility = True
                    self.invincibility_time = time.time()
                elif obj['type'] == 'clone':
                    self.clone_active = True
                    self.clone_time = time.time()
                return True
            elif not self.shield_active and not self.invincibility and not obj.get('disabled', False):
                self.lives -= 1
                self.particles.extend([{'pos': [px, py], 'size': 5, 'color': (255, 0, 0), 'speed': [random.uniform(-2, 2), random.uniform(-2, 2)]} for _ in range(5)])
                return True
        return False

    def apply_black_hole_effect(self):
        for bh in self.black_holes[:]:
            bh['pos'][1] += 1
            bh['duration'] -= 1
            if bh['duration'] <= 0:
                self.black_holes.remove(bh)
                continue
            for obj in self.asteroids + ([self.boss] if self.boss_active else []):
                if obj:
                    dx = bh['pos'][0] - obj['pos'][0]
                    dy = bh['pos'][1] - obj['pos'][1]
                    dist = max(1, (dx**2 + dy**2)**0.5)
                    strength = 3 / dist
                    obj['pos'][0] += dx * strength
                    obj['pos'][1] += dy * strength
            dx = bh['pos'][0] - self.player_pos[0]
            dy = bh['pos'][1] - self.player_pos[1]
            dist = max(1, (dx**2 + dy**2)**0.5)
            strength = 2 / dist
            self.player_pos[0] += dx * strength
            self.player_pos[1] += dy * strength

    def is_touching_player(self, touch_pos):
        px, py = self.player_pos
        tx, ty = touch_pos
        return ((px - tx) ** 2 + (py - ty) ** 2) ** 0.5 < self.player_size

    def draw_customization(self):
        self.screen.fill(self.bg_color)
        title = self.font.render("Customize Your Ship", True, (255, 255, 255))
        self.screen.blit(title, (self.screen_width//4, self.screen_height * 0.1))
        colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]
        shapes = ['triangle', 'circle']
        for i, color in enumerate(colors):
            pygame.draw.rect(self.screen, color, (self.screen_width * 0.2 * (i + 1), self.screen_height * 0.3, 50, 50))
        for i, shape in enumerate(shapes):
            if shape == 'triangle':
                pygame.draw.polygon(self.screen, self.player_color, 
                                  [(self.screen_width * 0.2 * (i + 1), self.screen_height * 0.5 - 25),
                                   (self.screen_width * 0.2 * (i + 1) - 25, self.screen_height * 0.5 + 25),
                                   (self.screen_width * 0.2 * (i + 1) + 25, self.screen_height * 0.5 + 25)])
            else:
                pygame.draw.circle(self.screen, self.player_color, 
                                 (int(self.screen_width * 0.2 * (i + 1)), int(self.screen_height * 0.5)), 25)
        start_text = self.font.render("Tap to Start", True, (255, 255, 255))
        self.screen.blit(start_text, (self.screen_width//3, self.screen_height * 0.7))
        endless_text = self.font.render("Endless Mode", True, (255, 255, 255))
        self.screen.blit(endless_text, (self.screen_width//3, self.screen_height * 0.8))

    def draw_upgrades(self):
        self.screen.fill(self.bg_color)
        title = self.font.render(f"Upgrades (Credits: {self.credits})", True, (255, 255, 255))
        self.screen.blit(title, (self.screen_width//4, self.screen_height * 0.1))
        upgrades = [
            ("Projectile Speed +0.2 (100)", 'projectile_speed', 0.2, 100),
            ("Shield Duration +2s (150)", 'shield_duration', 2, 150),
            ("Skill Cooldown -10% (200)", 'skill_cooldown', -0.1, 200)
        ]
        for i, (text, key, value, cost) in enumerate(upgrades):
            upgrade_text = self.font.render(text, True, (255, 255, 255) if self.credits >= cost else (100, 100, 100))
            self.screen.blit(upgrade_text, (self.screen_width//4, self.screen_height * 0.2 + i * 50))
        back_text = self.font.render("Tap to Continue", True, (255, 255, 255))
        self.screen.blit(back_text, (self.screen_width//3, self.screen_height * 0.8))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if self.show_customization:
                        if y > self.screen_height * 0.7 and y < self.screen_height * 0.75:
                            self.show_customization = False
                            self.endless_mode = False
                        elif y > self.screen_height * 0.75:
                            self.show_customization = False
                            self.endless_mode = True
                        elif y > self.screen_height * 0.4 and y < self.screen_height * 0.6:
                            if x < self.screen_width * 0.2:
                                self.player_shape = 'triangle'
                            elif x < self.screen_width * 0.4:
                                self.player_shape = 'circle'
                        elif y > self.screen_height * 0.2 and y < self.screen_height * 0.4:
                            if x < self.screen_width * 0.2:
                                self.player_color = (0, 255, 0)
                            elif x < self.screen_width * 0.4:
                                self.player_color = (255, 0, 0)
                            elif x < self.screen_width * 0.6:
                                self.player_color = (0, 0, 255)
                    elif self.lives <= 0:
                        if y > self.screen_height * 0.8:
                            self.save_leaderboard()
                            self.__init__()
                        elif y > self.screen_height * 0.2 and y < self.screen_height * 0.5:
                            upgrades = [
                                ('projectile_speed', 0.2, 100),
                                ('shield_duration', 2, 150),
                                ('skill_cooldown', -0.1, 200)
                            ]
                            i = (y - int(self.screen_height * 0.2)) // 50
                            if i < len(upgrades):
                                key, value, cost = upgrades[i]
                                if self.credits >= cost:
                                    self.upgrades[key] += value
                                    self.credits -= cost
                    elif self.paused:
                        if x > self.screen_width * 0.75 and y < self.screen_height * 0.1:
                            self.paused = False
                    elif x > self.screen_width * 0.75 and y < self.screen_height * 0.1:
                        self.paused = True
                    elif not self.paused and self.lives > 0:
                        if y < self.screen_height * 0.1:
                            if x < self.screen_width // 3 and self.dash_cooldown <= 0:
                                self.player_pos[0] += 100 * (-1 if self.player_pos[0] > self.screen_width//2 else 1)
                                self.dash_cooldown = int(600 * self.upgrades['skill_cooldown'])
                            elif self.screen_width // 3 <= x < 2 * self.screen_width // 3 and self.emp_cooldown <= 0:
                                for asteroid in self.asteroids:
                                    if ((asteroid['pos'][0] - self.player_pos[0]) ** 2 + (asteroid['pos'][1] - self.player_pos[1]) ** 2) ** 0.5 < 200:
                                        asteroid['disabled'] = True
                                self.emp_cooldown = int(900 * self.upgrades['skill_cooldown'])
                            elif x >= 2 * self.screen_width // 3 and self.overcharge_cooldown <= 0:
                                self.overcharge_active = True
                                self.overcharge_time = time.time()
                                self.overcharge_cooldown = int(1200 * self.upgrades['skill_cooldown'])
                        elif y < self.screen_height * 0.2:
                            guns = ['laser', 'plasma', 'homing', 'spread', 'gravity']
                            self.current_gun = guns[(guns.index(self.current_gun) + 1) % len(guns)]
                        elif y < self.player_pos[1]:
                            self.spawn_projectile()
                        elif self.is_touching_player(event.pos):
                            self.dragging = True
                if event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                if event.type == pygame.MOUSEMOTION and self.dragging and self.lives > 0 and not self.paused:
                    new_pos = list(event.pos)
                    self.player_pos[0] += (new_pos[0] - self.player_pos[0]) * self.player_speed * 0.1
                    self.player_pos[1] += (new_pos[1] - self.player_pos[1]) * self.player_speed * 0.1

            if self.show_customization:
                self.draw_customization()
                pygame.display.flip()
                continue

            if self.lives <= 0:
                self.draw_upgrades()
                pygame.display.flip()
                continue

            if not self.paused:
                speed_factor = 0.5 if self.time_slow else 1.0
                if self.frame_count % (1800 // (2 if self.endless_mode else 1)) == 0:
                    self.asteroid_spawn_rate = max(20, self.asteroid_spawn_rate - (5 if self.endless_mode else 2))

                # Smooth boundary checking
                self.player_pos[0] = max(-self.player_size//2, min(self.screen_width + self.player_size//2, self.player_pos[0]))
                self.player_pos[1] = max(self.player_size//2, min(self.screen_height - self.player_size//2, self.player_pos[1]))

                self.frame_count += 1
                if self.frame_count % int(self.asteroid_spawn_rate * speed_factor) == 0:
                    self.spawn_asteroid()
                if self.frame_count % int(self.star_spawn_rate * speed_factor) == 0:
                    self.spawn_star()
                if self.frame_count % int(self.power_up_spawn_rate * speed_factor) == 0:
                    self.spawn_power_up()
                if self.frame_count % int(self.black_hole_spawn_rate * speed_factor) == 0:
                    self.spawn_black_hole()
                if self.frame_count % (3600 if not self.endless_mode else 1800) == 0 and not self.boss_active:
                    self.spawn_boss()

                # Timer updates
                current_time = time.time()
                if self.shield_active and current_time - self.shield_time > self.upgrades['shield_duration']:
                    self.shield_active = False
                if hasattr(self, 'speed_time') and current_time - self.speed_time > 5:
                    self.player_speed = 1
                if hasattr(self, 'multiplier_time') and current_time - self.multiplier_time > 10:
                    self.score_multiplier = 1
                if hasattr(self, 'time_slow_time') and current_time - self.time_slow_time > 5:
                    self.time_slow = False
                if hasattr(self, 'invincibility_time') and current_time - self.invincibility_time > 3:
                    self.invincibility = False
                if hasattr(self, 'clone_time') and current_time - self.clone_time > 5:
                    self.clone_active = False
                if self.overcharge_active and current_time - self.overcharge_time > 5:
                    self.overcharge_active = False
                self.dash_cooldown = max(0, self.dash_cooldown - 1)
                self.emp_cooldown = max(0, self.emp_cooldown - 1)
                self.overcharge_cooldown = max(0, self.overcharge_cooldown - 1)

                # Update game objects
                for asteroid in self.asteroids[:]:
                    if not asteroid['disabled']:
                        asteroid['pos'][1] += asteroid['speed'] * speed_factor
                    if asteroid['pos'][1] > self.screen_height + asteroid['size']:
                        self.asteroids.remove(asteroid)
                    elif self.check_collision(asteroid):
                        self.asteroids.remove(asteroid)

                for star in self.stars[:]:
                    star['pos'][1] += star['speed'] * speed_factor
                    if star['pos'][1] > self.screen_height + star['size']:
                        self.stars.remove(star)
                    elif self.check_collision(star, is_star=True):
                        self.stars.remove(star)

                for power_up in self.power_ups[:]:
                    power_up['pos'][1] += power_up['speed'] * speed_factor
                    if power_up['pos'][1] > self.screen_height + power_up['size']:
                        self.power_ups.remove(power_up)
                    elif self.check_collision(power_up, is_power_up=True):
                        self.power_ups.remove(power_up)

                if self.boss_active:
                    self.boss['pos'][1] += self.boss['speed'] * speed_factor
                    if self.boss['pos'][1] > self.screen_height + self.boss['size']:
                        self.boss_active = False
                    elif self.check_collision(self.boss):
                        self.boss['health'] -= 1
                        if self.boss['health'] <= 0:
                            self.score += 50 * self.score_multiplier
                            self.boss_active = False
                            self.achievements['beat_boss'] = True

                self.apply_black_hole_effect()
                self.shoot_cooldown = max(0, self.shoot_cooldown - 1)
                self.update_projectiles()
                self.update_boss()

                elapsed = int(current_time - self.game_time)
                if elapsed >= 300 and not self.achievements['survive_5min']:
                    self.achievements['survive_5min'] = True
                if not self.shield_active:
                    self.time_without_shield += 1
                    if self.time_without_shield >= 120 * 60 and not self.missions['survive_2min_no_shield']:
                        self.missions['survive_2min_no_shield'] = True
                self.credits += self.score // 100

            # Rendering
            self.screen.fill(self.bg_color)
            shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            self.screen_shake = max(0, self.screen_shake - 1)
            
            self.draw_background()
            self.draw_player()
            if self.clone_active:
                temp_pos = self.player_pos.copy()
                self.player_pos[0] += 50
                self.draw_player()
                self.spawn_projectile()
                self.player_pos = temp_pos
            self.draw_particles()
            for asteroid in self.asteroids:
                self.draw_asteroid(asteroid)
            for star in self.stars:
                self.draw_star(star)
            for power_up in self.power_ups:
                self.draw_power_up(power_up)
            for bh in self.black_holes:
                self.draw_black_hole(bh)
            if self.boss_active:
                self.draw_boss()
            self.draw_projectiles()

            # UI
            elapsed = int(time.time() - self.game_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
            lives_text = self.font.render(f"Lives: {self.lives}", True, (255, 255, 255))
            time_text = self.font.render(f"Time: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
            gun_text = self.font.render(f"Gun: {self.current_gun.capitalize()}", True, (255, 255, 255))
            skills_text = self.font.render(f"Dash: {self.dash_cooldown//60} | EMP: {self.emp_cooldown//60} | Over: {self.overcharge_cooldown//60}", True, (255, 255, 255))
            high_score_text = self.font.render(f"High: {self.high_score}", True, (255, 255, 255))
            mode_text = self.font.render("Endless Mode" if self.endless_mode else "Normal Mode", True, (255, 255, 255))
            self.screen.blit(score_text, (10 + shake_x, 10 + shake_y))
            self.screen.blit(lives_text, (10 + shake_x, int(self.screen_height * 0.08) + shake_y))
            self.screen.blit(time_text, (10 + shake_x, int(self.screen_height * 0.16) + shake_y))
            self.screen.blit(gun_text, (10 + shake_x, int(self.screen_height * 0.24) + shake_y))
            self.screen.blit(skills_text, (10 + shake_x, int(self.screen_height * 0.32) + shake_y))
            self.screen.blit(high_score_text, (10 + shake_x, int(self.screen_height * 0.40) + shake_y))
            self.screen.blit(mode_text, (10 + shake_x, int(self.screen_height * 0.48) + shake_y))

            if self.paused:
                pause_text = self.font.render("PAUSED - Tap Here to Resume", True, (255, 255, 255))
                self.screen.blit(pause_text, (self.screen_width//4 + shake_x, self.screen_height//2 + shake_y))
            else:
                pause_button = self.font.render("Pause", True, (255, 255, 255))
                self.screen.blit(pause_button, (self.screen_width * 0.85 + shake_x, 10 + shake_y))

            if self.lives <= 0:
                game_over_text = self.font.render("GAME OVER - Select Upgrades", True, (255, 0, 0))
                self.screen.blit(game_over_text, (self.screen_width//4 + shake_x, self.screen_height//2 + shake_y))
                ach_text = self.font.render("Achievements & Missions:", True, (255, 255, 255))
                self.screen.blit(ach_text, (self.screen_width//4 + shake_x, self.screen_height * 0.6 + shake_y))
                y_offset = 0
                for name, unlocked in {**self.achievements, **self.missions}.items():
                    text = self.font.render(f"{name}: {'Yes' if unlocked else 'No'}", True, (255, 255, 255))
                    self.screen.blit(text, (self.screen_width//4 + shake_x, self.screen_height * 0.65 + y_offset + shake_y))
                    y_offset += 30

            pygame.display.flip()
            self.clock.tick(60)  # Consistent 60 FPS

        pygame.quit()

if __name__ == "__main__":
    game = SpaceDodgerAndroid()
    game.run()