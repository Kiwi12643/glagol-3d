# ============================================================
# МИНИ-ИГРЫ
# ============================================================
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
import random
import math

class GameStorage:
    def __init__(self):
        self.store = JsonStore('glagol_save.json')
    
    def save(self, key, value):
        data = {}
        if self.store.exists('game_data'):
            data = dict(self.store.get('game_data'))
        data[key] = value
        self.store.put('game_data', **data)
    
    def load(self, key, default=None):
        if self.store.exists('game_data'):
            return self.store.get('game_data').get(key, default)
        return default

# ============================================================
# МИНИ-ИГРА 1: РАННЕР ГЛАГОЛА
# ============================================================
class RunnerGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Раннер Глагола"
        self.popup = None
        self.score = 0
        self.game_over = False
        
        # Игровое поле
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_bg)
        
        # Глагол (квадратик)
        self.player = Widget()
        self.player.size = (50, 50)
        self.player.pos = (50, self.height / 2)
        with self.player.canvas:
            Color(0.3, 0.7, 0.3)  # Зелёный Глагол
            self.player_rect = Rectangle(pos=self.player.pos, size=self.player.size)
        self.player.bind(pos=self._update_player_rect)
        self.add_widget(self.player)
        
        # Счёт
        self.score_label = Label(
            text='Счёт: 0',
            font_size=24,
            color=(1, 1, 1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.score_label.size = (200, 50)
        self.add_widget(self.score_label)
        
        # Препятствия
        self.obstacles = []
        
        # Управление
        self.bind(on_touch_down=self.jump)
        
        # Игровой цикл
        Clock.schedule_interval(self.update, 1/60.)
    
    def _update_bg(self, instance, value):
        self.bg.size = instance.size
        self.player.pos = (50, self.height / 2)
    
    def _update_player_rect(self, instance, value):
        self.player_rect.pos = instance.pos
    
    def jump(self, instance, touch):
        if self.game_over:
            self.restart()
            return
        
        # Прыжок вверх
        target_y = min(self.height - 50, self.player.pos[1] + 150)
        anim = Animation(pos=(50, target_y), duration=0.1)
        anim += Animation(pos=(50, max(0, target_y - 150)), duration=0.3)
        anim.start(self.player)
    
    def spawn_obstacle(self):
        if self.game_over:
            return
        
        obstacle = Widget()
        obstacle.size = (30, random.randint(30, 100))
        obstacle.pos = (self.width, random.randint(0, self.height - obstacle.height))
        
        with obstacle.canvas:
            Color(1, 0.3, 0.3)
            self.obstacle_rect = Rectangle(pos=obstacle.pos, size=obstacle.size)
        obstacle.bind(pos=lambda inst, val: setattr(self, '_temp', val))
        
        self.add_widget(obstacle)
        self.obstacles.append(obstacle)
    
    def update(self, dt):
        if self.game_over:
            return
        
        # Двигаем препятствия
        for obs in self.obstacles[:]:
            x, y = obs.pos
            obs.pos = (x - 5, y)
            
            # Проверка столкновения
            if self._check_collision(self.player, obs):
                self.end_game()
                return
            
            # Удаляем ушедшие
            if obs.pos[0] < -50:
                self.remove_widget(obs)
                self.obstacles.remove(obs)
                self.score += 10
                self.score_label.text = f'Счёт: {self.score}'
        
        # Спавн препятствий
        if random.random() < 0.02:
            self.spawn_obstacle()
    
    def _check_collision(self, w1, w2):
        x1, y1 = w1.pos
        w1_w, w1_h = w1.size
        x2, y2 = w2.pos
        w2_w, w2_h = w2.size
        
        return (x1 < x2 + w2_w and x1 + w1_w > x2 and
                y1 < y2 + w2_h and y1 + w1_h > y2)
    
    def end_game(self):
        self.game_over = True
        
        # Сохраняем рекорд
        highscore = GameStorage().load('highscore_runner', 0)
        if self.score > highscore:
            GameStorage().save('highscore_runner', self.score)
        
        # Награда
        coins = self.score // 2
        current = GameStorage().load('coins', 0)
        GameStorage().save('coins', current + coins)
        
        self.score_label.text = f'КОНЕЦ! Счёт: {self.score} | +{coins}🪙'
    
    def restart(self):
        self.game_over = False
        self.score = 0
        self.score_label.text = 'Счёт: 0'
        
        for obs in self.obstacles:
            self.remove_widget(obs)
        self.obstacles.clear()

# ============================================================
# МИНИ-ИГРА 2: МЕТАНИЕ ЯБЛОК
# ============================================================
class AppleThrowGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Метание яблок"
        self.popup = None
        self.score = 0
        self.apples = []
        
        with self.canvas.before:
            Color(0.3, 0.5, 0.8, 1)
            self.bg = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_bg)
        
        # Мишень
        self.target = Widget()
        self.target.size = (60, 60)
        self.target.pos = (self.width / 2 - 30, self.height * 0.7)
        with self.target.canvas:
            Color(1, 0, 0)
            self.target_rect = Rectangle(pos=self.target.pos, size=self.target.size)
        self.target.bind(pos=self._update_target)
        self.add_widget(self.target)
        
        self.score_label = Label(
            text='Попаданий: 0',
            font_size=22,
            color=(1, 1, 1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.score_label.size = (250, 50)
        self.add_widget(self.score_label)
        
        self.bind(on_touch_down=self.throw_apple)
        Clock.schedule_interval(self.move_target, 1.5)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def _update_target(self, instance, value):
        self.target_rect.pos = value
    
    def move_target(self, dt):
        self.target.pos = (
            random.randint(0, self.width - 60),
            random.randint(self.height * 0.4, self.height - 60)
        )
    
    def throw_apple(self, instance, touch):
        if touch.y > self.height * 0.3:
            return
        
        launch_x = touch.x
        launch_y = 0
        
        apple = Widget()
        apple.size = (20, 20)
        apple.pos = (launch_x, launch_y)
        
        with apple.canvas:
            Color(1, 0.3, 0.3)
            self._apple_rect = Rectangle(pos=apple.pos, size=apple.size)
        
        self.add_widget(apple)
        
        target_x, target_y = self.target.pos
        anim = Animation(pos=(target_x + 20, target_y + 20), duration=0.8)
        anim.bind(on_complete=lambda *x: self.check_hit(apple))
        anim.start(apple)
    
    def check_hit(self, apple):
        ax, ay = apple.pos
        tx, ty = self.target.pos
        
        if (abs(ax - tx) < 40 and abs(ay - ty) < 40):
            self.score += 1
            self.score_label.text = f'Попаданий: {self.score}'
            SoundManager().play('coin')
        
        self.remove_widget(apple)

# ============================================================
# МИНИ-ИГРА 3: ЛОПНИ ШАРЫ
# ============================================================
class BalloonPopGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Лопни шары"
        self.popup = None
        self.score = 0
        self.balloons = []
        
        with self.canvas.before:
            Color(0.6, 0.8, 1, 1)
            self.bg = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_bg)
        
        self.score_label = Label(
            text='Лопнуто: 0',
            font_size=22,
            color=(0, 0, 0, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.score_label)
        
        self.bind(on_touch_down=self.pop_balloon)
        Clock.schedule_interval(self.spawn_balloon, 0.8)
        Clock.schedule_interval(self.update_balloons, 1/30.)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def spawn_balloon(self, dt):
        if len(self.balloons) > 10:
            return
        
        balloon = Widget()
        balloon.size = (random.randint(40, 80), random.randint(50, 90))
        balloon.pos = (
            random.randint(0, self.width - balloon.width),
            0 - balloon.height
        )
        
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1)]
        color = random.choice(colors)
        
        with balloon.canvas:
            Color(*color)
            self._balloon_rect = Rectangle(pos=balloon.pos, size=balloon.size)
        
        self.add_widget(balloon)
        self.balloons.append(balloon)
    
    def update_balloons(self, dt):
        for balloon in self.balloons[:]:
            x, y = balloon.pos
            balloon.pos = (x, y + 2)
            
            if y > self.height:
                self.remove_widget(balloon)
                self.balloons.remove(balloon)
    
    def pop_balloon(self, instance, touch):
        for balloon in self.balloons[:]:
            bx, by = balloon.pos
            bw, bh = balloon.size
            
            if (bx <= touch.x <= bx + bw and 
                by <= touch.y <= by + bh):
                self.remove_widget(balloon)
                self.balloons.remove(balloon)
                self.score += 1
                self.score_label.text = f'Лопнуто: {self.score}'
                return

# ============================================================
# МИНИ-ИГРА 4: ПАЗЛ
# ============================================================
class PuzzleGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Пазл Глагола"
        self.popup = None
        self.tiles = []
        
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.bg = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_bg)
        
        self.create_puzzle()
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def create_puzzle(self):
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)]
        positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
        random.shuffle(positions)
        
        for i, (color, (px, py)) in enumerate(zip(colors, positions)):
            tile = Button(
                text=f'{i+1}',
                font_size=30,
                background_color=color,
                size_hint=(None, None),
                size=(self.width / 2 - 10, self.height / 2 - 10),
                pos=(px * self.width / 2, py * self.height / 2)
            )
            tile.bind(on_press=self.tile_pressed)
            self.tiles.append({'btn': tile, 'pos': (px, py)})
            self.add_widget(tile)
    
    def tile_pressed(self, instance):
        # Простая механика: меняем цвет на правильный
        if instance.background_color == [1, 0, 1, 1]:
            instance.background_color = (0, 1, 0, 1)
            GameStorage().save('coins', GameStorage().load('coins', 0) + 5)

# ============================================================
# МИНИ-ИГРА 5: КОЛЕСО УДАЧИ
# ============================================================
class WheelGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Колесо удачи"
        self.popup = None
        
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)
            self.bg = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_bg)
        
        self.spin_btn = Button(
            text='🎰 КРУТИТЬ',
            font_size=24,
            size_hint=(0.5, 0.15),
            pos_hint={'x': 0.25, 'y': 0.4},
            background_color=(0.8, 0.6, 0, 1)
        )
        self.spin_btn.bind(on_press=self.spin)
        self.add_widget(self.spin_btn)
        
        self.result_label = Label(
            text='Нажми КРУТИТЬ!',
            font_size=20,
            color=(1, 1, 1, 1),
            pos_hint={'x': 0, 'y': 0.6}
        )
        self.add_widget(self.result_label)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def spin(self, instance):
        prizes = [
            ('🪙 50', 50),
            ('🪙 100', 100),
            ('🪙 25', 25),
            ('🪙 200', 200),
            ('🪙 10', 10),
        ]
        prize_text, prize_amount = random.choice(prizes)
        
        coins = GameStorage().load('coins', 0)
        GameStorage().save('coins', coins + prize_amount)
        
        self.result_label.text = f'Выигрыш: {prize_text}!'

# ============================================================
# МЕНЕДЖЕР МИНИ-ИГР
# ============================================================
class MinigameManager:
    def start(self, game_type):
        games = {
            'runner': RunnerGame,
            'apple_throw': AppleThrowGame,
            'balloon_pop': BalloonPopGame,
            'puzzle': PuzzleGame,
            'wheel': WheelGame,
        }
        
        if game_type in games:
            return games[game_type]()
        return None
