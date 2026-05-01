# ============================================================
# МИНИ-ИГРЫ ДЛЯ ГОВОРЯЩЕГО ГЛАГОЛА 3D
# ============================================================
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from kivy.core.audio import SoundLoader
import random
import math
import os
import sys

# ============================================================
# ЗАГЛУШКА SOUNDMANAGER (если не импортируется из main)
# ============================================================
class SoundManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.sounds = {}
        return cls._instance
    
    def play(self, name, volume=1.0):
        path = f"sounds/{name}.wav"
        if os.path.exists(path) and name not in self.sounds:
            self.sounds[name] = SoundLoader.load(path)
        
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].volume = volume
            self.sounds[name].play()

# ============================================================
# ХРАНИЛИЩЕ ОЧКОВ
# ============================================================
class GameStorage:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.store = JsonStore('glagol_save.json')
        return cls._instance
    
    def load(self, key, default=None):
        if self._instance.store.exists('game_data'):
            return self._instance.store.get('game_data').get(key, default)
        return default
    
    def save(self, key, value):
        data = {}
        if self._instance.store.exists('game_data'):
            data = dict(self._instance.store.get('game_data'))
        data[key] = value
        self._instance.store.put('game_data', **data)

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
        self.obstacles = []
        self._temp = None
        
        # Фон
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(1000, 1000))
        self.bind(size=self._update_bg)
        
        # Глагол-игрок
        self.player = Widget(size=(50, 50), pos=(50, 300))
        with self.player.canvas:
            Color(0.3, 0.75, 0.3)
            self.player_rect = Rectangle(pos=self.player.pos, size=self.player.size)
            # Глаза
            Color(1, 1, 1)
            self.eye1 = Ellipse(pos=(self.player.x + 8, self.player.y + 28), size=(14, 14))
            self.eye2 = Ellipse(pos=(self.player.x + 28, self.player.y + 28), size=(14, 14))
            Color(0, 0, 0)
            self.pupil1 = Ellipse(pos=(self.player.x + 11, self.player.y + 31), size=(8, 8))
            self.pupil2 = Ellipse(pos=(self.player.x + 31, self.player.y + 31), size=(8, 8))
        self.player.bind(pos=self._update_player_gfx)
        self.add_widget(self.player)
        
        # Счёт
        self.score_label = Label(
            text='Счёт: 0',
            font_size=22,
            bold=True,
            color=(1, 1, 0, 1),
            size_hint=(None, None),
            size=(250, 50),
            pos_hint={'x': 0.02, 'y': 0.92}
        )
        self.add_widget(self.score_label)
        
        # Кнопка назад
        back_btn = Button(
            text='← ВЫХОД',
            font_size=16,
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'right': 0.98, 'y': 0.93},
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.exit_game)
        self.add_widget(back_btn)
        
        # Запуск
        self.bind(on_touch_down=self.jump)
        Clock.schedule_interval(self.update, 1/60.)
        Clock.schedule_interval(self.spawn_obstacle, 1.2)
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = value
    
    def _update_player_gfx(self, instance, value):
        x, y = instance.pos
        self.player_rect.pos = (x, y)
        self.eye1.pos = (x + 8, y + 28)
        self.eye2.pos = (x + 28, y + 28)
        self.pupil1.pos = (x + 11, y + 31)
        self.pupil2.pos = (x + 31, y + 31)
    
    def jump(self, instance, touch):
        if self.game_over:
            self.restart()
            return True
        
        if touch.y < self.height * 0.7:
            target_y = min(self.height - 60, self.player.y + 180)
            anim = Animation(y=target_y, duration=0.15, t='out_cubic')
            anim += Animation(y=max(50, target_y - 180), duration=0.35, t='in_cubic')
            anim.start(self.player)
            SoundManager().play('boing', 0.3)
            return True
        return False
    
    def spawn_obstacle(self, dt=None):
        if self.game_over:
            return
        
        h = random.randint(30, 90)
        w = random.randint(20, 35)
        y_pos = random.randint(0, int(self.height - h))
        
        obstacle = Widget(size=(w, h), pos=(self.width + 20, y_pos))
        with obstacle.canvas:
            Color(1, 0.25, 0.25)
            Rectangle(pos=obstacle.pos, size=obstacle.size)
        obstacle.bind(pos=self._update_obs_gfx)
        
        self.add_widget(obstacle)
        self.obstacles.append(obstacle)
    
    def _update_obs_gfx(self, instance, value):
        pass
    
    def update(self, dt):
        if self.game_over:
            return
        
        for obs in self.obstacles[:]:
            obs.x -= 4.5 + (self.score * 0.02)
            
            # Коллизия
            if self._check_collision(self.player, obs):
                self.end_game()
                return
            
            if obs.x < -50:
                self.remove_widget(obs)
                self.obstacles.remove(obs)
                self.score += 5
                self.score_label.text = f'Счёт: {self.score}'
    
    def _check_collision(self, a, b):
        ax, ay = a.pos
        aw, ah = a.size
        bx, by = b.pos
        bw, bh = b.size
        return (ax < bx + bw and ax + aw > bx and
                ay < by + bh and ay + ah > by)
    
    def end_game(self):
        self.game_over = True
        SoundManager().play('fail', 0.5)
        
        # Рекорд
        high = GameStorage().load('highscore_runner', 0)
        if self.score > high:
            GameStorage().save('highscore_runner', self.score)
        
        # Монеты
        coins_earned = self.score // 3
        current_coins = GameStorage().load('coins', 0)
        GameStorage().save('coins', current_coins + coins_earned)
        
        self.score_label.text = f'💀 GAME OVER! Счёт: {self.score} (+{coins_earned}🪙)'
        self.score_label.color = (1, 0.3, 0.3, 1)
    
    def restart(self):
        self.game_over = False
        self.score = 0
        self.score_label.text = 'Счёт: 0'
        self.score_label.color = (1, 1, 0, 1)
        self.player.pos = (50, self.height / 2)
        
        for obs in self.obstacles:
            self.remove_widget(obs)
        self.obstacles.clear()
    
    def exit_game(self, instance):
        if self.popup:
            self.popup.dismiss()

# ============================================================
# МИНИ-ИГРА 2: МЕТАНИЕ ЯБЛОК
# ============================================================
class AppleThrowGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Метание яблок"
        self.popup = None
        self.score = 0
        self.apples_on_screen = []
        
        # Фон
        with self.canvas.before:
            Color(0.3, 0.5, 0.75, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(1000, 1000))
        self.bind(size=self._update_bg)
        
        # Мишень
        self.target = Widget(size=(55, 55), pos=(self.width/2, self.height*0.75))
        with self.target.canvas:
            Color(1, 0.15, 0.15)
            self.target_circle = Ellipse(pos=self.target.pos, size=self.target.size)
            Color(1, 1, 1)
            self.target_inner = Ellipse(
                pos=(self.target.x+12, self.target.y+12),
                size=(31, 31)
            )
            Color(1, 0.15, 0.15)
            self.target_bull = Ellipse(
                pos=(self.target.x+22, self.target.y+22),
                size=(11, 11)
            )
        self.target.bind(pos=self._update_target_gfx)
        self.add_widget(self.target)
        
        # Счёт
        self.score_label = Label(
            text='🍎 Попаданий: 0',
            font_size=22,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(300, 50),
            pos_hint={'x': 0.02, 'y': 0.92}
        )
        self.add_widget(self.score_label)
        
        # Кнопка назад
        back_btn = Button(
            text='← ВЫХОД',
            font_size=16,
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'right': 0.98, 'y': 0.93},
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.exit_game)
        self.add_widget(back_btn)
        
        # Свайп для броска
        self._touch_start = None
        self.bind(on_touch_down=self._start_throw)
        self.bind(on_touch_up=self._end_throw)
        
        # Движение мишени
        Clock.schedule_interval(self.move_target, 2.0)
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = value
    
    def _update_target_gfx(self, instance, value):
        self.target_circle.pos = value
        self.target_inner.pos = (value[0]+12, value[1]+12)
        self.target_bull.pos = (value[0]+22, value[1]+22)
    
    def move_target(self, dt):
        new_x = random.randint(20, self.width - 75)
        new_y = random.randint(int(self.height*0.4), self.height - 75)
        anim = Animation(x=new_x, y=new_y, duration=1.0, t='in_out_cubic')
        anim.start(self.target)
    
    def _start_throw(self, instance, touch):
        if touch.y < self.height * 0.3:
            self._touch_start = (touch.x, touch.y)
            return True
        return False
    
    def _end_throw(self, instance, touch):
        if self._touch_start:
            dx = touch.x - self._touch_start[0]
            dy = touch.y - self._touch_start[1]
            
            if abs(dx) < 5 and abs(dy) < 5:
                self._touch_start = None
                return
            
            apple = Widget(size=(22, 22), pos=(touch.x - 11, touch.y - 11))
            with apple.canvas:
                Color(1, 0.25, 0.25)
                Ellipse(pos=apple.pos, size=apple.size)
                Color(0, 0.6, 0)
                Rectangle(pos=(apple.x+9, apple.y+20), size=(4, 8))
            
            self.add_widget(apple)
            self.apples_on_screen.append(apple)
            
            target_x = touch.x + dx * 1.5
            target_y = touch.y + dy * 1.5
            
            anim = Animation(
                x=target_x - 11,
                y=target_y - 11,
                duration=0.7,
                t='out_cubic'
            )
            anim.bind(on_complete=lambda *x: self.check_hit(apple))
            anim.start(apple)
            
            SoundManager().play('boing', 0.2)
            self._touch_start = None
    
    def check_hit(self, apple):
        ax, ay = apple.pos
        tx, ty = self.target.pos
        ts = self.target.size[0]
        
        distance = math.sqrt((ax - tx - ts/2)**2 + (ay - ty - ts/2)**2)
        
        if distance < ts * 0.7:
            self.score += 1
            self.score_label.text = f'🍎 Попаданий: {self.score}'
            SoundManager().play('coin', 0.8)
            
            coins = GameStorage().load('coins', 0)
            GameStorage().save('coins', coins + 2)
        
        self.remove_widget(apple)
        if apple in self.apples_on_screen:
            self.apples_on_screen.remove(apple)
    
    def exit_game(self, instance):
        if self.popup:
            self.popup.dismiss()

# ============================================================
# МИНИ-ИГРА 3: ЛОПНИ ШАРЫ
# ============================================================
class BalloonPopGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Лопни шары"
        self.popup = None
        self.score = 0
        self.missed = 0
        self.max_missed = 10
        self.balloons = []
        
        # Фон
        with self.canvas.before:
            Color(0.5, 0.7, 0.95, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(1000, 1000))
        self.bind(size=self._update_bg)
        
        # Счёт
        self.score_label = Label(
            text='🎈 Лопнуто: 0',
            font_size=22,
            bold=True,
            color=(0.1, 0.1, 0.3, 1),
            size_hint=(None, None),
            size=(300, 50),
            pos_hint={'x': 0.02, 'y': 0.92}
        )
        self.add_widget(self.score_label)
        
        # Пропуски
        self.missed_label = Label(
            text=f'❌ Пропущено: 0/{self.max_missed}',
            font_size=18,
            color=(0.7, 0.2, 0.2, 1),
            size_hint=(None, None),
            size=(250, 40),
            pos_hint={'right': 0.98, 'y': 0.85}
        )
        self.add_widget(self.missed_label)
        
        # Кнопка назад
        back_btn = Button(
            text='← ВЫХОД',
            font_size=16,
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'right': 0.98, 'y': 0.93},
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.exit_game)
        self.add_widget(back_btn)
        
        self.bind(on_touch_down=self.pop_balloon)
        Clock.schedule_interval(self.spawn_balloon, 0.9)
        Clock.schedule_interval(self.update_balloons, 1/40.)
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = value
    
    def spawn_balloon(self, dt):
        if self.missed >= self.max_missed:
            return
        
        size = random.randint(45, 75)
        balloon = Widget(
            size=(size, int(size * 1.2)),
            pos=(random.randint(0, self.width - size), -size)
        )
        
        colors = [
            (1, 0.2, 0.2), (1, 0.5, 0.2), (1, 0.9, 0.2),
            (0.2, 0.9, 0.3), (0.2, 0.6, 1), (0.6, 0.2, 1)
        ]
        color = random.choice(colors)
        
        with balloon.canvas:
            Color(*color)
            Ellipse(pos=balloon.pos, size=balloon.size)
            Color(0.3, 0.3, 0.3)
            Rectangle(
                pos=(balloon.x + size/2 - 2, balloon.y - 8),
                size=(4, 12)
            )
        
        self.add_widget(balloon)
        self.balloons.append(balloon)
    
    def update_balloons(self, dt):
        for balloon in self.balloons[:]:
            balloon.y += 2.5
            
            if balloon.y > self.height + 20:
                self.remove_widget(balloon)
                self.balloons.remove(balloon)
                self.missed += 1
                self.missed_label.text = f'❌ Пропущено: {self.missed}/{self.max_missed}'
                self.missed_label.color = (1, 0.2, 0.2, 1)
                
                if self.missed >= self.max_missed:
                    self.score_label.text = f'💀 КОНЕЦ! Лопнуто: {self.score}'
                    self.score_label.color = (1, 0.2, 0.2, 1)
                    coins = self.score * 3
                    GameStorage().save('coins', GameStorage().load('coins', 0) + coins)
    
    def pop_balloon(self, instance, touch):
        for balloon in self.balloons[:]:
            bx, by = balloon.pos
            bw, bh = balloon.size
            
            if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
                self.remove_widget(balloon)
                self.balloons.remove(balloon)
                self.score += 1
                self.score_label.text = f'🎈 Лопнуто: {self.score}'
                SoundManager().play('pop', 0.6)
                return True
        return False
    
    def exit_game(self, instance):
        if self.popup:
            self.popup.dismiss()

# ============================================================
# МИНИ-ИГРА 4: ПАЗЛ ГЛАГОЛА
# ============================================================
class PuzzleGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Пазл Глагола"
        self.popup = None
        self.moves = 0
        self.correct_tiles = 0
        self.total_tiles = 9
        
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(1000, 1000))
        self.bind(size=self._update_bg)
        
        self.moves_label = Label(
            text='Ходов: 0',
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(200, 40),
            pos_hint={'x': 0.05, 'y': 0.92}
        )
        self.add_widget(self.moves_label)
        
        back_btn = Button(
            text='← ВЫХОД',
            font_size=16,
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'right': 0.98, 'y': 0.93},
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.exit_game)
        self.add_widget(back_btn)
        
        self.create_grid()
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = value
    
    def create_grid(self):
        self.tiles = []
        colors = [
            (1, 0.3, 0.3), (0.3, 1, 0.3), (0.3, 0.3, 1),
            (1, 1, 0.3), (1, 0.3, 1), (0.3, 1, 1),
            (1, 0.6, 0.3), (0.6, 1, 0.3), (0.3, 0.6, 1)
        ]
        random.shuffle(colors)
        
        tile_size = min(self.width, self.height) * 0.25
        grid_start_x = (self.width - tile_size * 3) / 2
        grid_start_y = (self.height - tile_size * 3) / 2
        
        for row in range(3):
            for col in range(3):
                idx = row * 3 + col
                color = colors[idx]
                
                tile = Button(
                    text=str(idx + 1),
                    font_size=28,
                    bold=True,
                    background_color=color,
                    background_normal='',
                    color=(1, 1, 1, 1),
                    size_hint=(None, None),
                    size=(tile_size - 4, tile_size - 4),
                    pos=(grid_start_x + col * tile_size + 2,
                         grid_start_y + (2 - row) * tile_size + 2)
                )
                tile.original_color = color
                tile.correct_position = (row, col)
                tile.bind(on_press=self.tile_pressed)
                
                self.tiles.append(tile)
                self.add_widget(tile)
    
    def tile_pressed(self, instance):
        self.moves += 1
        self.moves_label.text = f'Ходов: {self.moves}'
        
        if instance.background_color == [0.3, 1, 0.3, 1]:
            instance.background_color = (0.15, 0.15, 0.5, 1)
            self.correct_tiles += 1
            SoundManager().play('coin', 0.6)
            
            if self.correct_tiles >= self.total_tiles:
                coins = 50
                GameStorage().save('coins', GameStorage().load('coins', 0) + coins)
                self.moves_label.text = f'🎉 СОБРАНО! +{coins}🪙'
                self.moves_label.color = (0, 1, 0, 1)
        else:
            instance.background_color = (0.3, 1, 0.3, 1)
            self.correct_tiles += 1
            SoundManager().play('boing', 0.3)
            
            if self.correct_tiles >= self.total_tiles:
                coins = 50
                GameStorage().save('coins', GameStorage().load('coins', 0) + coins)
                self.moves_label.text = f'🎉 СОБРАНО! +{coins}🪙'
                self.moves_label.color = (0, 1, 0, 1)
    
    def exit_game(self, instance):
        if self.popup:
            self.popup.dismiss()

# ============================================================
# МИНИ-ИГРА 5: КОЛЕСО УДАЧИ
# ============================================================
class WheelGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_name = "Колесо удачи"
        self.popup = None
        self.is_spinning = False
        
        with self.canvas.before:
            Color(0.1, 0.05, 0.15, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=(1000, 1000))
        self.bind(size=self._update_bg)
        
        # Колесо (визуализация)
        self.wheel_widget = Widget(
            size_hint=(None, None),
            size=(220, 220),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        with self.wheel_widget.canvas:
            # Сегменты колеса
            segment_colors = [
                (1, 0.2, 0.2), (1, 0.7, 0.2), (1, 1, 0.2),
                (0.2, 1, 0.2), (0.2, 0.7, 1), (0.5, 0.2, 1)
            ]
            for i, color in enumerate(segment_colors * 2):
                Color(*color)
                angle_start = i * 30
                angle_end = (i + 1) * 30
                Ellipse(
                    pos=(self.wheel_widget.x, self.wheel_widget.y),
                    size=self.wheel_widget.size,
                    angle_start=angle_start,
                    angle_end=angle_end
                )
            Color(0.9, 0.8, 0.3)
            self.wheel_arrow = Ellipse(
                pos=(self.wheel_widget.x + 95, self.wheel_widget.y + 95),
                size=(30, 30)
            )
        
        self.add_widget(self.wheel_widget)
        
        # Кнопка крутить
        self.spin_btn = Button(
            text='🎰 КРУТИТЬ (10🪙)',
            font_size=22,
            bold=True,
            size_hint=(None, None),
            size=(220, 60),
            pos_hint={'center_x': 0.5, 'y': 0.15},
            background_color=(0.9, 0.7, 0.1, 1),
            color=(0, 0, 0, 1)
        )
        self.spin_btn.bind(on_press=self.spin)
        self.add_widget(self.spin_btn)
        
        # Результат
        self.result_label = Label(
            text='🎰 Испытай удачу!',
            font_size=20,
            bold=True,
            color=(1, 0.9, 0.3, 1),
            pos_hint={'center_x': 0.5, 'y': 0.75}
        )
        self.add_widget(self.result_label)
        
        # Монеты
        self.coin_label = Label(
            text=f'🪙 {GameStorage().load("coins", 0)}',
            font_size=18,
            color=(1, 0.8, 0, 1),
            size_hint=(None, None),
            size=(150, 40),
            pos_hint={'x': 0.05, 'y': 0.92}
        )
        self.add_widget(self.coin_label)
        
        back_btn = Button(
            text='← ВЫХОД',
            font_size=16,
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'right': 0.98, 'y': 0.93},
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.exit_game)
        self.add_widget(back_btn)
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = value
    
    def spin(self, instance):
        if self.is_spinning:
            return
        
        coins = GameStorage().load('coins', 0)
        if coins < 10:
            self.result_label.text = '❌ Не хватает монет!'
            self.result_label.color = (1, 0.3, 0.3, 1)
            return
        
        self.is_spinning = True
        GameStorage().save('coins', coins - 10)
        self.coin_label.text = f'🪙 {coins - 10}'
        
        # Анимация вращения
        def animate_wheel(progress, *args):
            if self.wheel_widget:
                self.wheel_widget.canvas.clear()
                # Перерисовка под другим углом
        
        # Имитация вращения
        for i in range(20):
            Clock.schedule_once(lambda dt, n=i: self._spin_step(n), i * 0.05)
        
        Clock.schedule_once(self._finish_spin, 1.2)
    
    def _spin_step(self, step):
        if self.wheel_widget:
            self.wheel_widget.rotation = step * 45
            self.result_label.text = ['🎰', '🔄', '💫'][step % 3]
    
    def _finish_spin(self, dt):
        self.is_spinning = False
        
        if self.wheel_widget:
            self.wheel_widget.rotation = 0
        
        prizes = [
            ('🪙 200', 200, (0, 1, 0)),
            ('🪙 50', 50, (1, 1, 0)),
            ('🪙 25', 25, (1, 0.8, 0)),
            ('🪙 100', 100, (0, 1, 0)),
            ('🪙 500!', 500, (0, 1, 1)),
            ('😢 0', 0, (1, 0.3, 0.3)),
        ]
        
        weights = [0.1, 0.25, 0.3, 0.2, 0.05, 0.1]
        prize_text, prize_amount, color = random.choices(
            prizes, weights=weights, k=1
        )[0]
        
        coins = GameStorage().load('coins', 0)
        GameStorage().save('coins', coins + prize_amount)
        
        self.result_label.text = f'Выигрыш: {prize_text}!'
        self.result_label.color = color
        self.coin_label.text = f'🪙 {coins + prize_amount}'
        
        SoundManager().play('coin', 1.0)
    
    def exit_game(self, instance):
        if self.popup:
            self.popup.dismiss()

# ============================================================
# МЕНЕДЖЕР МИНИ-ИГР
# ============================================================
class MinigameManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def start(self, game_type):
        games = {
            'runner': RunnerGame,
            'apple_throw': AppleThrowGame,
            'balloon_pop': BalloonPopGame,
            'puzzle': PuzzleGame,
            'wheel': WheelGame,
        }
        if game_type in games:
            game = games[game_type]()
            return game
        return None
