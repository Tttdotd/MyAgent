# flybird game main program
import pygame
import sys
import random

# 初始化Pygame
pygame.init()

# 设置屏幕尺寸
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flybird Game")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
GREEN = (0, 128, 0)

# 游戏时钟
clock = pygame.time.Clock()
FPS = 60

# 小鸟类
class Bird:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.jump_power = -8
        self.width = 40
        self.height = 30

    def update(self):
        # 应用重力
        self.velocity += self.gravity
        self.y += self.velocity

        # 确保小鸟不会飞出屏幕（修正：增加边界限制）
        if self.y < 0:
            self.y = 0
            self.velocity = 0
        elif self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height
            self.velocity = 0

    def jump(self):
        self.velocity = self.jump_power

    def draw(self):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))

# 管道类
class Pipe:
    def __init__(self):
        self.gap = 150
        self.x = SCREEN_WIDTH
        self.top_height = random.randint(100, SCREEN_HEIGHT - 100 - self.gap)
        self.bottom_y = self.top_height + self.gap
        self.width = 60
        self.speed = 5

    def update(self):
        self.x -= self.speed

    def draw(self):
        # 画上管道
        pygame.draw.rect(screen, GREEN, (self.x, 0, self.width, self.top_height))
        # 画下管道
        pygame.draw.rect(screen, GREEN, (self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y))

    def collide(self, bird):
        # 检测碰撞：上下边界或管道内部（修正：确保碰撞检测准确）
        if bird.y < self.top_height or bird.y + bird.height > self.bottom_y:
            if self.x < bird.x + bird.width and bird.x < self.x + self.width:
                return True
        return False

# 创建游戏对象
bird = Bird()
pipes = []
pipe_timer = 0
pipe_frequency = 120  # 每120帧生成一个新管道

# 游戏主循环
game_over = False
score = 0
while True:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                bird.jump()
            if event.key == pygame.K_r and game_over:
                # 重新开始游戏
                bird = Bird()
                pipes = []
                pipe_timer = 0
                score = 0
                game_over = False

    if not game_over:
        # 更新小鸟位置
        bird.update()

        # 生成新管道
        pipe_timer += 1
        if pipe_timer >= pipe_frequency:
            pipes.append(Pipe())
            pipe_timer = 0

        # 更新所有管道的位置
        for pipe in pipes[:]:
            pipe.update()
            if pipe.collide(bird):
                game_over = True
            if pipe.x + pipe.width < 0:
                pipes.remove(pipe)
                score += 1

        # 检查是否触底或撞顶（修正：确保边界判断正确）
        if bird.y + bird.height >= SCREEN_HEIGHT or bird.y <= 0:
            game_over = True

    # 绘制画面
    screen.fill(BLUE)

    # 绘制小鸟
    bird.draw()

    # 绘制管道
    for pipe in pipes:
        pipe.draw()

    # 显示分数（简单文本）
    font = pygame.font.SysFont('Arial', 36)
    score_text = font.render(f'Score: {score}', True, WHITE)
    screen.blit(score_text, (10, 10))

    # 如果游戏结束，显示提示
    if game_over:
        game_over_text = font.render('Game Over! Press R to Restart', True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))

    # 更新屏幕
    pygame.display.flip()
    clock.tick(FPS)