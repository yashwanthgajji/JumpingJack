import pygame
from pygame import mixer
import pickle
from os import path
from pygame.locals import *

mixer.pre_init(44100,-16,2,512)
mixer.init()
pygame.init()

clock=pygame.time.Clock()

#pygame constants
screen_width=800
screen_height=800
font_score=pygame.font.SysFont('Bauhaus 93',30)
font=pygame.font.SysFont('Bauhaus 93',70)
white=(255,255,255)
blue=(0,0,255)

#game variables
tile_size=40
fps=60
game_over=0
main_menu=True
level=1
max_levels=7
score=0

#starting window
screen=pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Platformer")

#load images
bg_img=pygame.image.load('img/sky.png')
sun_img=pygame.image.load('img/sun.png')
restart_img=pygame.image.load('img/restart_btn.png')
start_img=pygame.image.load('img/start_btn.png')
exit_img=pygame.image.load('img/exit_btn.png')

#load sound effects
pygame.mixer.music.load('img/music.wav')
pygame.mixer.music.play(-1,0.0,5000)
coin_fx=pygame.mixer.Sound('img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx=pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx=pygame.mixer.Sound('img/game_over.wav')
game_over_fx.set_volume(0.5)

#draw text function
def draw_text(text,font,text_col,x,y):
    img=font.render(text,True,text_col)
    screen.blit(img,(x,y))

#function to reset level
def reset_level(level):
    world_data=[]
    player.reset(100,(screen_height-tile_size-80))
    blob_group.empty()
    platform_group.empty()
    lava_group.empty()
    coin_group.empty()
    exit_group.empty()
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world=World(world_data)
    return world



class Button():
    def __init__(self,x,y,img):
        self.img=img
        self.rect=self.img.get_rect()
        self.rect.x=x
        self.rect.y=y
        self.clicked=False
    def draw(self):
        action=False
        #mouse position
        pos=pygame.mouse.get_pos()

        #check mouse over and check click
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0]==1 and self.clicked==False:
                action=True
                self.clicked=True
        if pygame.mouse.get_pressed()[0]==0:
            self.clicked=False
        #draw button
        screen.blit(self.img,self.rect)
        return action

class Player():
    def __init__(self,x,y):
        self.reset(x,y)
    def reset(self,x,y):
        self.player_width = 32
        self.player_height = 76
        self.right_images = []
        self.left_images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (self.player_width, self.player_height))
            img_left = pygame.transform.flip(img_right, True, False)
            self.right_images.append(img_right)
            self.left_images.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.right_images[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air=True
    def update(self,game_over):
        dx=0
        dy=0
        walk_cooldown=5
        col_threshold=16

        if game_over==0:
            #get keypresses
            key=pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped==False and self.in_air==False:
                jump_fx.play()
                self.vel_y=-15
                self.jumped=True
            if key[pygame.K_SPACE]==False:
                self.jumped=False
            if key[pygame.K_LEFT]:
                dx-=5
                self.direction=-1
                self.counter+=1
            if key[pygame.K_RIGHT]:
                dx+=5
                self.direction=1
                self.counter+=1
            if key[pygame.K_LEFT]==False and key[pygame.K_RIGHT]==False:
                self.counter=0
                self.index=0
                if self.direction == -1:
                    self.image = self.left_images[self.index]
                elif self.direction == 1:
                    self.image = self.right_images[self.index]
            #handle animation
            if self.counter>=walk_cooldown:
                self.counter=0
                self.index=(self.index+1)%len(self.right_images)
                if self.direction==-1:
                    self.image=self.left_images[self.index]
                elif self.direction==1:
                    self.image=self.right_images[self.index]

            #add gravity
            self.vel_y+=1
            if self.vel_y>10:
                self.vel_y=10
            dy+=self.vel_y

            #check for collision
            self.in_air=True
            for tile in world.tile_list:
                #collsiion in y direction
                if tile[1].colliderect(self.rect.x+dx,self.rect.y,self.rect.width,self.rect.height):
                    dx=0
                #collsiion in y direction
                if tile[1].colliderect(self.rect.x,self.rect.y+dy,self.rect.width,self.rect.height):
                    #head hiting to above block
                    if self.vel_y<0:
                        dy=tile[1].bottom-self.rect.top
                        self.vel_y=0
                    #foot hitting to below block
                    elif self.vel_y>=0:
                        dy=tile[1].top-self.rect.bottom
                        self.in_air=False

            #check for collision with enemies
            if pygame.sprite.spritecollide(self,blob_group,False):
                game_over=-1
            # check for collision with lava
            if pygame.sprite.spritecollide(self,lava_group,False):
                game_over=-1
            # check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over=1
            #check for collision with platforms
            for platform in platform_group:
                # collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                    dx = 0
                # collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                    # check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_threshold:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_threshold:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # move sideways with the platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction



            #update player position
            self.rect.x+=dx
            self.rect.y+=dy
        elif game_over==-1:
            self.image=self.dead_image
            if self.rect.y>tile_size:
                self.rect.y-=5
        #draw player
        screen.blit(self.image,self.rect)
        # pygame.draw.rect(screen,(255,255,255),self.rect,2)
        return game_over

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image=pygame.image.load('img/blob.png')
        self.rect=self.image.get_rect()
        self.rect.x=x
        self.rect.y=y
        self.move_direction=1
        self.move_counter=0
    def update(self):
        self.rect.x+=self.move_direction
        self.move_counter+=1
        if abs(self.move_counter)>tile_size:
            self.move_counter*=-1
            self.move_direction*=-1

class Platform(pygame.sprite.Sprite):
    def __init__(self,x,y,move_x,move_y):
        pygame.sprite.Sprite.__init__(self)
        platform_image=pygame.image.load('img/platform.png')
        self.image=pygame.transform.scale(platform_image,(tile_size,(tile_size//2)))
        self.rect=self.image.get_rect()
        self.rect.x=x
        self.rect.y=y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x=move_x
        self.move_y=move_y
    def update(self):
        self.rect.x += self.move_direction*self.move_x
        self.rect.y+=self.move_direction*self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > tile_size:
            self.move_counter *= -1
            self.move_direction *= -1

class Lava(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img=pygame.image.load('img/lava.png')
        self.image=pygame.transform.scale(img,(tile_size,tile_size//2))
        self.rect=self.image.get_rect()
        self.rect.x=x
        self.rect.y=y

class Coin(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img=pygame.image.load('img/coin.png')
        self.image=pygame.transform.scale(img,(tile_size//2,tile_size//2))
        self.rect=self.image.get_rect()
        self.rect.center=(x,y)

class Exit(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img=pygame.image.load('img/exit.png')
        self.image=pygame.transform.scale(img,(tile_size,int(tile_size*1.5)))
        self.rect=self.image.get_rect()
        self.rect.x=x
        self.rect.y=y

class World():
    def __init__(self,data):
        self.tile_list=[]
        #load images
        dirt_img=pygame.image.load('img/dirt.png')
        grass_img=pygame.image.load('img/grass.png')

        row_count=0
        for row in data:
            col_count=0
            for col in row:
                if col==1:
                    img=pygame.transform.scale(dirt_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile=(img,img_rect)
                    self.tile_list.append(tile)
                if col==2:
                    img=pygame.transform.scale(grass_img,(tile_size,tile_size))
                    img_rect=img.get_rect()
                    img_rect.x=col_count*tile_size
                    img_rect.y=row_count*tile_size
                    tile=(img,img_rect)
                    self.tile_list.append(tile)
                if col==3:
                    blob=Enemy(col_count*tile_size,row_count*tile_size+15)
                    blob_group.add(blob)
                if col == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size,1,0)
                    platform_group.add(platform)
                if col == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size,0,1)
                    platform_group.add(platform)
                if col==6:
                    lava=Lava(col_count*tile_size,row_count*tile_size+tile_size//2)
                    lava_group.add(lava)
                if col==7:
                    coin=Coin(col_count*tile_size+tile_size//2,row_count*tile_size+tile_size//2)
                    coin_group.add(coin)
                if col==8:
                    exit=Exit(col_count*tile_size,row_count*tile_size-tile_size//2)
                    exit_group.add(exit)
                col_count+=1
            row_count+=1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0],tile[1])
            # pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)


blob_group=pygame.sprite.Group()
platform_group=pygame.sprite.Group()
lava_group=pygame.sprite.Group()
coin_group=pygame.sprite.Group()
exit_group=pygame.sprite.Group()

#create a dummy coin to show score
score_coin=Coin(tile_size//2,tile_size//2)
coin_group.add(score_coin)

player=Player(80,(screen_height-tile_size-40))
world=reset_level(level)

#create buttons
restart_button=Button(screen_width//2-50,screen_height//2+100,restart_img)
start_button=Button(screen_width//2-350,screen_height//2,start_img)
exit_button=Button(screen_width//2+150,screen_height//2,exit_img)

run=True
while run:
    clock.tick(fps)

    screen.blit(bg_img,(0,0))
    screen.blit(sun_img,(100,100))

    if main_menu:
        if start_button.draw():
            main_menu=False
        if exit_button.draw():
            run=False
    else:
        world.draw()
        draw_text(": "+str(score),font_score,white,tile_size,10)
        game_over=player.update(game_over)
        if game_over==0:
            blob_group.update()
            platform_group.update()
            #update score
            #check coin collided
            if pygame.sprite.spritecollide(player,coin_group,True):
                coin_fx.play()
                score+=1

        elif game_over==-1:
            game_over_fx.play()
            draw_text("GAME OVER!!!",font,blue,screen_width//2-200,screen_height//2-100)
            if restart_button.draw():
                world = reset_level(level)
                game_over=0
                score=0

        elif game_over==1:
            level+=1
            if level<=max_levels:
                world=reset_level(level)
                game_over=0
            else:
                draw_text("YOU WIN!!!", font, blue, (screen_width // 2 - 200), screen_height // 2)
                if restart_button.draw():
                    level=0
                    world = reset_level(level)
                    game_over = 0
                    score=0

        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            run=False

    pygame.display.update()

pygame.quit()