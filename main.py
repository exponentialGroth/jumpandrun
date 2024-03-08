import pygame
from pygame import mixer
import random
import time
import math
from pathlib import Path
from enum import Enum
from itertools import chain

mixer.init()
pygame.init()

WIDTH, HEIGHT = 1925, 1020

WIN=pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Jump and Run")

BLACK=(0,0,0)
WHITE=(255,255,255)
PINK=(235,0,255)
BLUE = pygame.Color('lightskyblue3')
BLUE2 = (0, 99, 117)
ANAKIWA = (128, 243, 255)
RED = (255, 98, 0)
BROWN = (163, 85, 13)
MENU_COLOR = BROWN

FPS = 50
PLAYER_SIZE = 50
BULLET_COUNT = 3
new_distance = 0
camera_speed = 2


ObstacleTypes = Enum('ObstacleTypes', ['BLACK_STAR'])

BULLET_WIDTH, BULLET_HEIGHT = 17, 12

DISTANCE_POS = (100, 50)
distance_font = pygame.font.Font(None, 50)

play_button_font = pygame.font.Font(None, 150)
play_button_text = play_button_font.render("PLAY", True, BLACK)
play_button_rect = pygame.Rect(WIDTH/2 - play_button_text.get_width()/2, HEIGHT/2 - play_button_text.get_height()/2, play_button_text.get_width(), play_button_text.get_height())
highscore_font = pygame.font.Font(None, 80)

cwd = Path.cwd()
if cwd.name != "jumpandrun":
    print("Select .../jumpandrun as the working directory.")
    exit()
sounds_path = cwd / "sounds"
images_path = cwd / "pictures"
highscore_path = cwd / "highscore.txt"

dying_enemy_sound = mixer.Sound(sounds_path / "dying_enemy_sound.mp3")
dying_player_sound = mixer.Sound(sounds_path / "dying_player_song.mp3")
shooting_sound = mixer.Sound(sounds_path / "shot.wav")
background_sound = mixer.Sound(sounds_path / "background_song.mp3")
background_sound_2 = mixer.Sound(sounds_path / "background_song_2.mp3")
shooting_sound.set_volume(0.2)
dying_enemy_sound.set_volume(0.2)

controls_img = pygame.transform.scale(pygame.image.load(images_path / "controls.png"), (311, 300))
black_star_img = pygame.image.load(images_path / "black_star.png")
yellow_button_img = pygame.image.load(images_path / "yellow_button.png")
yellow_button_activated_img = pygame.image.load(images_path / "yellow_button_activated.png")
bullet_img = pygame.image.load(images_path / "bullet.png")
bullet_img_reversed = pygame.image.load(images_path / "bullet_reversed.png")
flying_enemy_img = pygame.image.load(images_path / "enemy1.png")



class Background:
    def __init__(self, height, color) -> None:
        self.height = height
        self.color = color
        self.rect = pygame.Rect(0, 0, WIDTH, self.height)

    def draw(self):
        pygame.draw.rect(WIN, self.color, self.rect)



class Ground:
    def __init__(self, elements: list[tuple[pygame.Rect], tuple[int, int, int]]) -> None:
        self.elements = elements


    def draw(self):
        for rect, color in self.elements:
            pygame.draw.rect(WIN, color, rect)


    def handle_contact(self, player_x, player_y, player_vel_x, player_vel_y):
        """Returns coordinates for the player such that he is not in the ground or None if the player dies"""
        final_x, final_y = player_x, player_y
        final_color = None
        collisions = []
        for rect, color in self.elements:
            if player_x + PLAYER_SIZE - player_vel_x <= rect.x and player_x + PLAYER_SIZE > rect.x and player_y + PLAYER_SIZE > rect.y and player_y < rect.y + rect.h:  # only right of player
                collisions.append((rect.x - PLAYER_SIZE, player_y))
            if player_x - player_vel_x >= rect.x + rect.w and player_x < rect.x + rect.w and player_y + PLAYER_SIZE > rect.y and player_y < rect.y + rect.h:  # left
                collisions.append((rect.x + rect.w, player_y))
            if player_y + PLAYER_SIZE - player_vel_y <= rect.y and player_y + PLAYER_SIZE > rect.y and player_x + PLAYER_SIZE > rect.x and player_x < rect.x + rect.w:  # bottom
                collisions.append((player_x, rect.y - PLAYER_SIZE))
            if player_y - player_vel_y >= rect.y + rect.h and player_y < rect.y + rect.h and player_x + PLAYER_SIZE > rect.x and player_x < rect.x + rect.w:  # top
                collisions.append((player_x, rect.y + rect.h))

            if len(collisions) == 1:
                collision = collisions[0]
                if player_vel_x > 0 and collision[0] < final_x or player_vel_x < 0 and collision[0] > final_x:
                    final_x = collision[0]
                    final_color = color
                if player_vel_y > 0 and collision[1] < final_y or player_vel_y < 0 and collision[1] > final_y:
                    final_y = collision[1] 
                    final_color = color
            elif len(collisions) == 2:
                x_collision, y_collision = collisions[0], collisions[1]
                final_color = color
                if abs((player_x - x_collision[0]) / player_vel_x) < abs((player_y - y_collision[1]) / player_vel_y):  # contact was on the side
                    final_x = x_collision[0]
                    final_y = player_y - (player_x - final_x) / player_vel_x * player_vel_y
                else:
                    final_y = y_collision[1]
                    final_x = player_x - (player_y - final_y) / player_vel_y * player_vel_x
                break  # player should not be fast enough to go diagonally through multiple ground rects during one frame 
            collisions.clear()

        if final_color == RED: return None
        return final_x, final_y, player_vel_x + final_x - player_x, player_vel_y + final_y - player_y


    def update(self):
        for r, _ in self.elements:
            r.move_ip(-camera_speed, 0)



class Obstacle:
    def __init__(self, pos, size, type) -> None:
        self.pos = pos
        self.size = size
        base_img = black_star_img if type == ObstacleTypes.BLACK_STAR else None
        self.img = pygame.transform.scale(base_img, size)


    def draw(self):
        WIN.blit(self.img, self.pos)


    def update(self):
        self.pos = self.pos[0] - camera_speed, self.pos[1]

    
    def collides(self, player_x, player_y, player_vel_x, player_vel_y):
        if player_x + PLAYER_SIZE - player_vel_x <= self.pos[0] and player_x + PLAYER_SIZE > self.pos[0] and player_y + PLAYER_SIZE > self.pos[1] and player_y < self.pos[1] + self.size[1]:  # only right of player
            return True
        if player_x - player_vel_x >= self.pos[0] + self.size[0] and player_x < self.pos[0] + self.size[0] and player_y + PLAYER_SIZE > self.pos[1] and player_y < self.pos[1] + self.size[1]:  # left
            return True
        if player_y + PLAYER_SIZE - player_vel_y <= self.pos[1] and player_y + PLAYER_SIZE > self.pos[1] and player_x + PLAYER_SIZE > self.pos[0] and player_x < self.pos[0] + self.size[0]:  # bottom
            return True
        if player_y - player_vel_y >= self.pos[1] + self.size[1] and player_y < self.pos[1] + self.size[1] and player_x + PLAYER_SIZE > self.pos[0] and player_x < self.pos[0] + self.size[0]:  # top
            return True
        return False



class Button:
    def __init__(self, pos, width, height, reversed = False) -> None:
        self.xpos = pos[0]
        self.ypos = pos[1]
        self.active = False
        self.size = (width, height)
        self.reversed = reversed
        self.picture = pygame.transform.scale(yellow_button_img, self.size)
        self.picture_activated = pygame.transform.scale(yellow_button_activated_img, (self.size[0], round(self.size[0] * 84/269)))
        

    def draw_button(self):
        if not self.active:
            WIN.blit(self.picture, (self.xpos, self.ypos))
        else:
            WIN.blit(self.picture_activated, (self.xpos, self.ypos - self.size[1] * 84/269 + self.size[1]))


    def check_for_player(self, other):
        self.rect = pygame.Rect(self.xpos, self.ypos, self.size[0], self.size[1])
        if not self.reversed:
            if other.rect.colliderect(self.rect):  # TODO: activate only if player falls on the button from above
                self.active = True


    def update(self):
        self.xpos -= camera_speed



class Elevator:
    def __init__(self, x, y, width, height, color, vel_list, active = False) -> None:
        self.x = x
        self.y = y
        self.active = active
        self.width = width
        self.height = height
        self.color = color
        self.vel_list = vel_list
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.absolute_position = 0
    

    def handle_contact(self, player_x, player_y, player_vel_y):
        """Returns coordinates for the player to prevent falling through the elevator and takes the player with it
            Returns x, y, x_additional_speed, real_vel_y
        """
        if player_y + PLAYER_SIZE - player_vel_y <= self.y - self.vel_list[self.absolute_position][1] and player_y + PLAYER_SIZE > self.y and player_x + PLAYER_SIZE > self.x and player_x < self.x + self.width:  # only bottom
            return player_x, self.y - PLAYER_SIZE, self.vel_list[self.absolute_position][0] if self.active else 0, player_vel_y + self.y - player_y

        return player_x, player_y, 0, player_vel_y


    def draw(self):
        pygame.draw.rect(WIN, self.color, self.rect)


    def update(self, distance):
        self.x -= camera_speed

        if self.active:
            self.x += self.vel_list[self.absolute_position][0]
            self.y += self.vel_list[self.absolute_position][1]
            self.absolute_position += camera_speed

        self.rect.move_ip(self.x - self.rect.x, self.y - self.rect.y)


def handle_elevator_contact(elevators: list[Elevator], player_x, player_y, player_vel_y):
    for el in elevators:
        new_coords = el.handle_contact(player_x, player_y, player_vel_y)
        if player_y != new_coords[1]:
            return new_coords
    return player_x, player_y, 0, player_vel_y
    


class Bullet:
    def __init__(self, pos, speed = 7) -> None:
        self.x = pos[0]
        self.y = pos[1]
        self.speed = speed


    def update(self):
        self.x += self.speed - camera_speed


    def draw(self):
        if self.speed > 0:
            WIN.blit(bullet_img, (self.x, self.y))
        else:
            WIN.blit(bullet_img_reversed, (self.x, self.y))


    def collision(self, other_hitbox):  # does not use speed of the target because it is small compared to the bullet speed
        return (self.speed < 0 and other_hitbox[0] + other_hitbox[2] <= self.x - self.speed and other_hitbox[0] + other_hitbox[2] > self.x or \
            self.speed > 0 and other_hitbox[0] >= self.x + BULLET_WIDTH - self.speed and other_hitbox[0] < self.x + BULLET_WIDTH or \
            other_hitbox[0] < self.x + BULLET_WIDTH and other_hitbox[0] + other_hitbox[2] > self.x) and \
            other_hitbox[1] < self.y + BULLET_HEIGHT/2 and other_hitbox[1] + other_hitbox[3] > self.y + BULLET_HEIGHT/2




class FlyingEnemy:
    def __init__(self, pos, shooting_interval, bullet_speed, flying_interval, vel_y, size, lives=1) -> None:
        self.x = pos[0]
        self.y = pos[1]
        self.max_y = pos[1] + flying_interval
        self.min_y = pos[1] - flying_interval
        self.vel_y = vel_y
        self.shooting_interval = shooting_interval
        self.bullet_speed = bullet_speed
        self.image = pygame.transform.scale(flying_enemy_img, size)
        self.last_shot = time.time()
        self.size = size
        self.lives = lives

    def draw(self):
        WIN.blit(self.image, (self.x, self.y))


    def update(self):
        self.x -= camera_speed
        self.y += self.vel_y
        if self.y < self.min_y or self.y > self.max_y:
            self.vel_y *= -1


    def shoot(self, other_player_pos):
        if not (-100 - self.size[0] < self.x < WIDTH + 100): return None
        current_time = time.time()
        if self.last_shot + 0.75 > current_time: return None
        if 1 != random.randint(1, self.shooting_interval): return None
        
        self.last_shot = current_time
        return Bullet(
            (self.x + self.image.get_width(), self.y + self.image.get_height()/2 - BULLET_HEIGHT / 2),
            self.bullet_speed
        ) if other_player_pos[0] > self.x else Bullet(
            (self.x, self.y + self.image.get_height()/2 - BULLET_HEIGHT / 2),
            -self.bullet_speed
        )


    def collision(self, other_player_pos):
        return other_player_pos[0] + PLAYER_SIZE > self.x and other_player_pos[0] < self.x + self.size[0] \
            and other_player_pos[1] + PLAYER_SIZE > self.y and other_player_pos[1] < self.y + self.size[1]



class Player:
    gravitation = 1
    max_vel = 20

    sprinting = 0
    walking_left = 0
    walking_right = 0
    boosting = 0  # increases the height of a jump
    x_additional_speed = 0

    can_jump = False

    def __init__(self, xpos, ypos, size, color, distance = 0) -> None:
        self.x = xpos
        self.y = ypos
        self.y_vel = 0
        self.color = color
        self.rect = pygame.Rect(self.x, self.y, size, size)
        self.distance = distance
        

    def __add__(self, o):
        self.distance += o


    def draw_player(self):
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        pygame.draw.rect(WIN, self.color, self.rect)


    def shoot(self):
        shooting_sound.play()
        return Bullet((self.x + PLAYER_SIZE, self.y + PLAYER_SIZE/2 - BULLET_HEIGHT / 2))


    def fall(self):
        if self.y_vel < 0: self.y_vel -= self.boosting * 0.5
        self.y_vel = min(self.max_vel, self.y_vel + self.gravitation)


    def jump(self):
        self.y -= 1
        self.y_vel -= 15
        self.boosting = 1


    def move(self, ground: Ground, elevators, obstacles):
        self.fall()
        total_x_vel = self.walking_left * -2 + self.walking_right * (3 + self.sprinting * 3) + self.x_additional_speed
        self.x += total_x_vel - camera_speed
        self.y += self.y_vel
        self.distance += total_x_vel / 100

        ground_adjusted_coords = ground.handle_contact(self.x, self.y, total_x_vel, self.y_vel)
        if ground_adjusted_coords is None:
            player.die()
            return
        on_ground = ground_adjusted_coords[1] < self.y
        if ground_adjusted_coords[0] != self.x or ground_adjusted_coords[1] != self.y:
            self.x_additional_speed = 0
        self.x, self.y, total_x_vel, self.y_vel = ground_adjusted_coords

        elevator_adjusted_coords = handle_elevator_contact(elevators, self.x, self.y, self.y_vel)
        self.can_jump = on_ground or elevator_adjusted_coords[1] < self.y
        if elevator_adjusted_coords[1] != self.y:
            self.x_additional_speed = elevator_adjusted_coords[2]
        self.x, self.y, _, self.y_vel = elevator_adjusted_coords
        if self.can_jump: self.y_vel = 0
        
        for o in obstacles:
            if o.collides(self.x, self.y, total_x_vel, self.y_vel):
                self.die()
                return
        
        if self.x + PLAYER_SIZE < 0:
            self.die()


    def show_distance(self):
        text = distance_font.render(f"Distance: {self.distance:.1f} ", 1, BLACK)
        WIN.blit(text, DISTANCE_POS)


    def die(self):
        global new_distance
        new_distance = self.distance
        
        draw_window()

        background_sound.fadeout(1000)
        dying_player_sound.play(loops = -1, fade_ms=2000)

        circle_center = (round(self.x + PLAYER_SIZE / 2), self.y)
        circle_radius = 1500

        shrinking_steps = 20

        clock = pygame.time.Clock()

        while circle_radius > PLAYER_SIZE / 2:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()

            rects_around_circle = []

            for i in range(circle_center[0] - circle_radius, circle_center[0] + 1, 1):
                rects_around_circle.append(pygame.Rect(0, 0, i, circle_center[1] - math.sqrt(circle_radius ** 2 - (circle_center[0] - i) ** 2)))  # top left of player
                rects_around_circle.append(pygame.Rect(i + circle_radius, 0, WIDTH - i - circle_radius,  circle_center[1] - math.sqrt(circle_radius ** 2 - (i - circle_center[0] + circle_radius) ** 2)))  # top right
                rects_around_circle.append(pygame.Rect(0, circle_center[1] + math.sqrt(circle_radius ** 2 - (circle_center[0] - i) ** 2), i, HEIGHT - circle_center[1] + math.sqrt(circle_radius ** 2 - (circle_center[0] - i) ** 2)))  # bottom left
                rects_around_circle.append(pygame.Rect(i + circle_radius, circle_center[1] + math.sqrt(circle_radius ** 2 - (i - circle_center[0] + circle_radius) ** 2), WIDTH - i - PLAYER_SIZE/2, HEIGHT - circle_center[1] + math.sqrt(circle_radius ** 2 - (i - circle_center[0] + circle_radius) ** 2)))  # bottom right

            for e in rects_around_circle:
                pygame.draw.rect(WIN, BROWN, e)
                
            pygame.display.update()
            circle_radius -= shrinking_steps

        main()



def set_up():
    global ground, background, player, obstacles, button_for_elevator, bullets, enemies, enemy_bullets, elevators

    # ground
    ground_elements = [
        (pygame.Rect(0, 0.3*HEIGHT, 870, 0.7*HEIGHT), BLACK), 
        (pygame.Rect(870, 0.99*HEIGHT, 130, 0.01*HEIGHT), RED), 
        (pygame.Rect(1000, 0.85*HEIGHT, 970, 0.15*HEIGHT), BLACK), 
        (pygame.Rect(1970, HEIGHT - 5, 130, 5), RED)
    ]
    for i in range(1, 7):
        ground_elements.append((pygame.Rect(1800 + i*300, HEIGHT - 200 - i*85, 150, 200 + i*85), BLACK))
        ground_elements.append((pygame.Rect(1950 + i*300, HEIGHT - 5, 150, 5), RED))
    ground_elements[-1][0].width = 4500 - 1950 - 6*300

    ground_elements.append((pygame.Rect(4250, 520, 150, 50), BROWN))
    for i in range(3):
        ground_elements.append((pygame.Rect(6600 + i*210, 380 - (i+1)*70, (i+1)*210, (i+1)*70), BROWN))
    ground_elements.append((pygame.Rect(8220, 700, 500, 100), BROWN))

    for i in range(100):
        ground_elements.append((pygame.Rect(4500 + i*50, HEIGHT - i*2, 50, i*2), RED))
    ground_elements[-1][0].width = 14000


    # obstacles
    obstacles = []
    obstacles.append(Obstacle((400, 400), (35, 35), ObstacleTypes.BLACK_STAR))
    for i in range(16):
        obstacles.append(Obstacle((1000 + i * 60, 580), (50, 50), ObstacleTypes.BLACK_STAR))

    obstacles.append(Obstacle((4800, 360), (50, 50), ObstacleTypes.BLACK_STAR))
    obstacles.append(Obstacle((4800, 300), (50, 50), ObstacleTypes.BLACK_STAR))
    obstacles.append(Obstacle((5050, 380), (50, 50), ObstacleTypes.BLACK_STAR))
    obstacles.append(Obstacle((5050, 320), (50, 50), ObstacleTypes.BLACK_STAR))
    obstacles.append(Obstacle((5050, 260), (50, 50), ObstacleTypes.BLACK_STAR))

    for i in chain(range(3, 12), range(14, 25)):
        obstacles.append(Obstacle((7500 + i*60, 400), (50, 50), ObstacleTypes.BLACK_STAR))
    for i in range(13, 25):
        obstacles.append(Obstacle((7530 + i*60, 320), (50, 50), ObstacleTypes.BLACK_STAR))

    for i in range(3):
        obstacles.append(Obstacle((9150 + i*50, 650), (50, 50), ObstacleTypes.BLACK_STAR))
    for i in range(3):
        obstacles.append(Obstacle((9600 + i*55, 470), (50, 50), ObstacleTypes.BLACK_STAR))
    for i in range(3):
        obstacles.append(Obstacle((10250 + i*55, 355), (50, 50), ObstacleTypes.BLACK_STAR))

    possible_star_positions = [600, 550, 500, 450, 400]
    for i in range(400):
        if 1 == random.randint(1, 12):
            obstacles.append(Obstacle((12000 + i*300, random.choice(possible_star_positions)), (50, 50), ObstacleTypes.BLACK_STAR))


    # Enemies
    enemies = []
    enemies.append(FlyingEnemy((2000, 0.64 * HEIGHT), 80, 2, 150, 1, (50, 50)))

    for i in range(2, 7):
        enemies.append(FlyingEnemy((1850 + i * 300, HEIGHT - 260 - i * 85), 128 - 2 * i, 3, 0, 0, (45, 45)))

    enemies.append(FlyingEnemy((5400, 0.3 * HEIGHT), 160, 4, 50, 1, (50, 50)))
    enemies.append(FlyingEnemy((5800, 0.25 * HEIGHT), 160, 2, 100, 2, (75, 75)))
    enemies.append(FlyingEnemy((6200, 0.36 * HEIGHT), 160, 2, 100, 3, (100, 100)))
    enemies.append(FlyingEnemy((7600, 120), 30, 1, 10, 5, (40, 40)))

    for i in range(48):
        if 1 == random.randint(0,1):
            enemy_size = random.randint(15, 500)
            enemies.append(FlyingEnemy((11000 + 250*i, 666 - PLAYER_SIZE/2 - enemy_size/2), random.randint(101 - i, 256 - 2*i), random.randint(int(1+i/10), int(12+i)), random.randint(10, 250), random.randint(int(1+i/8), int(12+i/8)), (enemy_size, enemy_size), int(1 + enemy_size/100)))
            if enemy_size < 30:
                enemies.append(FlyingEnemy((11000 + 250*i + 50, 666 - PLAYER_SIZE/2 - enemy_size/2), random.randint(101 - i, 256 - 2*i), random.randint(int(1+i/10), int(12+i)), random.randint(10, 250), random.randint(int(1+i/8), int(12+i/8)), (enemy_size, enemy_size)))
            if enemy_size < 23:
                enemies.append(FlyingEnemy((11000 + 250*i + 100, 666 - PLAYER_SIZE/2 - enemy_size/2), random.randint(101 - i, 256 - 2*i), random.randint(int(1+i/10), int(12+i)), random.randint(10, 250), random.randint(int(1+i/8), int(12+i/8)), (enemy_size, enemy_size)))

    # Elevators
    vel_list_1 = []
    for i in range(4400):
        vel_list_1.append([camera_speed, 0])
    for i in range(900):
        vel_list_1.append([1, -2])
    for i in range(5000):
        vel_list_1.append([0, 0])

    vel_list_2 = []
    for i in range(800):
        vel_list_2.append([camera_speed - 1, 0])
    for i in range(800):
        vel_list_2.append([camera_speed - 1, 1])
    for i in range(4000):
        vel_list_2.append([0, 0])

    vel_list_3 = []
    for i in range(500):
        vel_list_3.append([camera_speed - 1, 0])
    for i in range(800):
        vel_list_3.append([camera_speed-1, 1])
    for i in range(3000):
        vel_list_3.append([0, 0])

    vel_list_4 = []
    for i in range(850):
        vel_list_4.append([camera_speed - 1, 0])
    for i in range(800):
        vel_list_4.append([camera_speed -1, -1])
    for i in range(3000):
        vel_list_4.append([0, 0])

    vel_list_5 = []
    for i in range(25000):
        vel_list_5.append([camera_speed, 0]) 

    elevator1 = Elevator(4000, 380, 150, 20, BROWN, vel_list_1)
    elevator2 = Elevator(8800, 700, 80, 15, BROWN, vel_list_2)
    elevator3 = Elevator(9250, 520, 120, 15, BROWN, vel_list_3)
    elevator4 = Elevator(9750, 400, 100, 15, BROWN, vel_list_4)
    elevator5 = Elevator(10450, 666, 250, 25, BROWN, vel_list_5)
    elevators = [elevator1, elevator2, elevator3, elevator4, elevator5]

    ground = Ground(ground_elements)
    background = Background(HEIGHT, BLUE2)
    player = Player(200, HEIGHT * 0.2 - PLAYER_SIZE, PLAYER_SIZE, ANAKIWA)
    button_for_elevator = Button((4300, 470), 50, 50)

    bullets = []
    enemy_bullets = []


def draw_window():
    background.draw()    
    ground.draw()
    player.draw_player()
    player.show_distance()
    for o in obstacles:
        o.draw()
    button_for_elevator.draw_button()

    for el in elevators:
        el.draw()

    for b in bullets:
        b.draw()

    for e in enemies:
        e.draw()

    for eb in enemy_bullets:
        eb.draw()

    pygame.display.update()


def read_highscore():
    d = open(highscore_path)
    highscore = d.readlines()
    d.close()
    return highscore[0]
    

def write_highscore(distance):
    d = open(highscore_path, "w")
    d.write(str(distance))
    d.close()


def menu():
    start_game = False
    clock = pygame.time.Clock()
    
    old_highscore = read_highscore()
    if new_distance > int(old_highscore):
        highscore_text = highscore_font.render(f"Best Distance: {new_distance:.0f} ", True, BLACK)
        write_highscore(f"{new_distance:.0f}")
    else:
        highscore_text = highscore_font.render("Best Distance: " + str(old_highscore), True, BLACK)

    distance_text = highscore_font.render(f"Distance: {new_distance:.0f} ", True, BLACK)

    while not start_game:
        clock.tick(FPS)
        
        WIN.fill(MENU_COLOR)
        WIN.blit(play_button_text, (play_button_rect.x, play_button_rect.y))
        pygame.draw.rect(WIN, BLACK, play_button_rect, 3)
        WIN.blit(controls_img, (100, 150))
        WIN.blit(highscore_text, (WIDTH - 600, 100))
        if new_distance > 0:
            WIN.blit(distance_text, (WIDTH / 2 - distance_text.get_width()/2, 275))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()  # TODO: end program correctly

            if event.type == pygame.MOUSEBUTTONDOWN and play_button_rect.collidepoint(event.pos) or \
            event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN) :
                dying_player_sound.fadeout(3000)
                start_game = True


def main():
    global camera_speed

    menu()
    set_up()
    clock = pygame.time.Clock()
    run = True
    background_sound.play(-1, fade_ms=1000)
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run=False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pass

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    player.walking_left = 1
                elif event.key == pygame.K_d:
                    player.walking_right = 1
                elif event.key == pygame.K_RSHIFT:
                    player.sprinting = 1
                elif event.key == pygame.K_SPACE and player.can_jump:
                    player.jump()
                elif event.key == pygame.K_w and len(bullets) < BULLET_COUNT:
                    bullets.append(player.shoot())
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player.walking_left = 0
                elif event.key == pygame.K_d:
                    player.walking_right = 0
                elif event.key == pygame.K_RSHIFT:
                    player.sprinting = 0
                elif event.key == pygame.K_SPACE:
                    player.boosting = 0


        ground.update()
        for o in obstacles:
            o.update()
        button_for_elevator.update()
        
        if len(elevators) >= 5:
            if button_for_elevator.active:
                elevators[0].active = True
            else:
                elevators[0].active = False

            if player.distance >= 83:
                elevators[1].active = True

            if player.distance > 89.5:
                elevators[2].active = True
            
            if player.distance > 95:
                elevators[3].active = True
            
            if player.distance > 103.5:
                elevators[4].active = True

            if player.distance > 120:
                del elevators[0:4]

        for el in elevators:
            el.update(player.distance)

        for i, b in enumerate(bullets):
            b.update()
            if b.x > WIDTH:
                bullets.pop(i)

        for i, eb in enumerate(enemy_bullets):
            eb.update()
            if eb.speed < 0 and eb.x < -BULLET_WIDTH or eb.speed > 0 and eb.x > WIDTH:
                enemy_bullets.pop(i)

        for enemy in enemies:
            enemy.update()
            new_bullet = enemy.shoot((player.x, player.y))
            if new_bullet:
                enemy_bullets.append(new_bullet)

        player.move(ground, elevators, obstacles)
        button_for_elevator.check_for_player(player)

        for i, b in enumerate(bullets):
            for j, e in enumerate(enemies):
                if b.collision((e.x, e.y, e.size[0], e.size[1])):
                    dying_enemy_sound.play()
                    bullets.pop(i)
                    if e.lives == 1:
                        enemies.pop(j)
                    else:
                        e.lives -= 1

        for eb in enemy_bullets:
            if eb.collision((player.x, player.y, PLAYER_SIZE, PLAYER_SIZE)):
                player.die()
        
        for e in enemies:
            if e.collision((player.x, player.y)):
                player.die()


        if player.distance >= 222:
            player.die()  # TODO: let him win the game instead


        draw_window()

    pygame.quit()


if __name__ == '__main__':
    main()