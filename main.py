# ============================================================
# ГОВОРЯЩИЙ ГЛАГОЛ 3D - ГЛАВНЫЙ ФАЙЛ
# ============================================================
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore
from kivy.animation import Animation
from kivy.properties import (NumericProperty, BooleanProperty, 
                              StringProperty, ListProperty, ObjectProperty)
from kivy.core.image import Image as CoreImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.utils import platform
import os
import zipfile
import random
import math
import json
from datetime import datetime

# Импорт модулей
from objloader import ObjLoader
from minigames import MinigameManager

# ============================================================
# КОНФИГУРАЦИЯ ОКНА
# ============================================================
Window.size = (480, 800)
Window.clearcolor = (0.05, 0.55, 0.85, 1)  # Небесный градиент фон

# ============================================================
# АВТОМАТИЧЕСКАЯ РАСПАКОВКА ZIP
# ============================================================
class ModelExtractor:
    def __init__(self):
        self.model_dir = "model"
        self.files = {
            'obj': None,
            'mtl': None,
            'jpg': [],
            'txt': None
        }
        
    def extract(self):
        """Распаковывает ZIP и находит все файлы"""
        # Проверяем, есть ли уже распакованная модель
        if os.path.exists(os.path.join(self.model_dir, "model_ready.txt")):
            print("Модель уже распакована!")
            return self.find_files()
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        
        # Ищем ZIP
        zip_files = [f for f in os.listdir('.') if f.endswith('.zip') and f != 'buildozer.zip']
        
        if not zip_files:
            print("ZIP с моделью не найден!")
            return False
        
        zip_path = zip_files[0]
        print(f"Распаковываю: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Смотрим содержимое
            print("Содержимое ZIP:")
            for f in zf.namelist():
                print(f"  - {f}")
            zf.extractall(self.model_dir)
        
        # Создаём маркер что модель готова
        with open(os.path.join(self.model_dir, "model_ready.txt"), 'w') as f:
            f.write("OK")
        
        print("Распаковка завершена!")
        return self.find_files()
    
    def find_files(self):
        """Находит все файлы модели"""
        for root, dirs, files in os.walk(self.model_dir):
            for f in files:
                path = os.path.join(root, f)
                if f.endswith('.obj'):
                    self.files['obj'] = path
                elif f.endswith('.mtl'):
                    self.files['mtl'] = path
                elif f.endswith(('.jpg', '.jpeg')):
                    self.files['jpg'].append(path)
                elif f.endswith('.txt'):
                    self.files['txt'] = path
        
        # Сортируем JPG чтобы было предсказуемо
        self.files['jpg'].sort()
        
        print(f"OBJ: {self.files['obj']}")
        print(f"MTL: {self.files['mtl']}")
        print(f"JPG: {self.files['jpg']}")
        print(f"TXT: {self.files['txt']}")
        
        return self.files['obj'] is not None

# ============================================================
# МЕНЕДЖЕР ЗВУКОВ
# ============================================================
class SoundManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.sounds = {}
            cls._instance.loaded = False
        return cls._instance
    
    def load(self):
        if self.loaded:
            return
        
        sound_names = ['hryuk', 'chavk', 'xrap', 'dance', 'bounce', 'coin', 
                       'victory', 'fail', 'pop', 'boing']
        
        for name in sound_names:
            path = f"sounds/{name}.wav"
            if os.path.exists(path):
                self.sounds[name] = SoundLoader.load(path)
                print(f"Звук загружен: {name}")
        
        self.loaded = True
    
    def play(self, name, volume=1.0):
        if name in self.sounds and self.sounds[name]:
            sound = self.sounds[name]
            sound.volume = volume
            sound.play()
            return True
        return False

# ============================================================
# ХРАНИЛИЩЕ ИГРЫ
# ============================================================
class GameStorage:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.store = JsonStore('glagol_save.json')
        return cls._instance
    
    def save(self, key, value):
        data = {}
        if self.store.exists('game_data'):
            data = dict(self.store.get('game_data'))
        data[key] = value
        data['last_save'] = str(datetime.now())
        self.store.put('game_data', **data)
    
    def load(self, key, default=None):
        if self.store.exists('game_data'):
            return self.store.get('game_data').get(key, default)
        return default
    
    def get_all(self):
        if self.store.exists('game_data'):
            return dict(self.store.get('game_data'))
        return {}

# ============================================================
# 3D РЕНДЕРЕР ГЛАГОЛА
# ============================================================
class Glagol3DRenderer(Widget):
    """Продвинутый 3D рендерер с анимациями"""
    
    happiness = NumericProperty(100)
    is_sleeping = BooleanProperty(False)
    current_animation = StringProperty('idle')
    
    def __init__(self, obj_path, texture_paths, **kwargs):
        self.canvas_obj = RenderContext(compute_normal_mat=True)
        
        # Продвинутый шейдер
        self.canvas_obj.shader.source = '''
            ---VERTEX SHADER---
            #ifdef GL_ES
            precision highp float;
            #endif
            
            uniform mat4 modelview_mat;
            uniform mat4 projection_mat;
            uniform mat4 normal_mat;
            
            attribute vec3 v_pos;
            attribute vec3 v_normal;
            attribute vec2 v_tc0;
            
            varying vec2 tex_coords;
            varying vec3 frag_pos;
            varying vec3 normal_vec;
            varying vec3 view_dir;
            
            void main() {
                vec4 world_pos = modelview_mat * vec4(v_pos, 1.0);
                frag_pos = world_pos.xyz;
                normal_vec = normalize(mat3(normal_mat) * v_normal);
                tex_coords = v_tc0;
                view_dir = normalize(-world_pos.xyz);
                gl_Position = projection_mat * world_pos;
            }
            
            ---FRAGMENT SHADER---
            #ifdef GL_ES
            precision highp float;
            #endif
            
            uniform sampler2D texture0;
            uniform vec3 light_pos;
            uniform vec3 ambient_light;
            uniform vec3 diffuse_light;
            uniform vec3 specular_light;
            uniform float shininess;
            uniform vec3 camera_pos;
            uniform float time;
            uniform float has_texture;
            
            varying vec2 tex_coords;
            varying vec3 frag_pos;
            varying vec3 normal_vec;
            varying vec3 view_dir;
            
            void main() {
                // Освещение
                vec3 normal = normalize(normal_vec);
                vec3 light_dir = normalize(light_pos - frag_pos);
                vec3 view = normalize(view_dir);
                vec3 halfway = normalize(light_dir + view);
                
                // Ambient
                vec3 ambient = ambient_light;
                
                // Diffuse
                float diff = max(dot(normal, light_dir), 0.0);
                vec3 diffuse = diffuse_light * diff;
                
                // Specular (Blinn-Phong)
                float spec = pow(max(dot(normal, halfway), 0.0), shininess);
                vec3 specular = specular_light * spec;
                
                // Итоговый цвет
                vec4 color;
                if (has_texture > 0.5) {
                    color = texture2D(texture0, tex_coords);
                } else {
                    color = vec4(0.2, 0.7, 0.3, 1.0);
                }
                
                vec3 result = (ambient + diffuse + specular) * color.rgb;
                
                // Лёгкое свечение на короне (по краям)
                float fresnel = pow(1.0 - abs(dot(normal, view)), 3.0);
                result += vec3(0.4, 0.3, 0.1) * fresnel * 0.5;
                
                gl_FragColor = vec4(result, color.a);
            }
        '''
        
        super(Glagol3DRenderer, self).__init__(**kwargs)
        
        self.obj_path = obj_path
        self.texture_paths = texture_paths
        
        # Состояния анимации
        self._angle_y = 0.0
        self._angle_x = -15.0
        self._target_y = 0.0
        self._target_x = -15.0
        self._bounce_offset = 0.0
        self._scale_current = 1.0
        self._scale_target = 1.0
        self._blink_timer = 0.0
        self._eye_offset = (0.0, 0.0)
        self._mouth_open = 0.0
        self._ear_wiggle = 0.0
        
        # Загружаем модель
        self.load_model()
        
        # Запускаем рендеринг
        with self.canvas_obj:
            self.cb_setup = Callback(self.setup_gl)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb_reset = Callback(self.reset_gl)
        
        # Анимации
        Clock.schedule_interval(self.update_animation, 1/60.)
        Clock.schedule_interval(self.random_action, random.uniform(3, 7))
        
        # Инициализация
        self.bind(size=self.update_projection)
    
    def load_model(self):
        """Загружает OBJ модель"""
        if not os.path.exists(self.obj_path):
            print(f"Модель не найдена: {self.obj_path}")
            return
        
        self.scene = ObjLoader(self.obj_path)
        print(f"Загружено объектов: {len(self.scene.objects)}")
        
        # Назначаем текстуры
        if self.texture_paths and len(self.texture_paths) > 0:
            self.main_texture = self.texture_paths[0]
            print(f"Основная текстура: {self.main_texture}")
        else:
            self.main_texture = None
    
    def setup_gl(self, *args):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
    
    def reset_gl(self, *args):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
    
    def setup_scene(self):
        Color(1, 1, 1, 1)
        PushMatrix()
        
        # Трансформации
        self.trans = Translate(0, -0.5, -5)
        
        # Вращения
        self.rot_y = Rotate(0, 0, 1, 0)    # Горизонтальное вращение
        self.rot_x = Rotate(-15, 1, 0, 0)  # Вертикальный наклон
        self.rot_z = Rotate(0, 0, 0, 1)    # Наклон головы
        
        # Масштаб
        self.scale = Scale(1.0, 1.0, 1.0)
        
        UpdateNormalMatrix()
        
        # Создаём меш
        if hasattr(self, 'scene') and self.scene.objects:
            first_obj = list(self.scene.objects.values())[0]
            self.mesh = Mesh(
                vertices=first_obj.vertices,
                indices=first_obj.indices,
                fmt=first_obj.vertex_format,
                mode='triangles'
            )
            
            if self.main_texture and os.path.exists(self.main_texture):
                self.canvas_obj['has_texture'] = 1.0
                self.mesh.texture = self.main_texture
            else:
                self.canvas_obj['has_texture'] = 0.0
        
        PopMatrix()
    
    def update_projection(self, *args):
        if self.width > 0 and self.height > 0:
            asp = self.width / self.height
            proj = Matrix().view_clip(-asp, asp, -1, 1, 1, 100, 1)
            self.canvas_obj['projection_mat'] = proj
    
    def update_animation(self, dt):
        """Главный цикл анимации"""
        # Плавное вращение
        diff_y = self._target_y - self._angle_y
        self._angle_y += diff_y * 5 * dt
        
        diff_x = self._target_x - self._angle_x
        self._angle_x += diff_x * 5 * dt
        
        # Плавный скейл
        diff_scale = self._scale_target - self._scale_current
        self._scale_current += diff_scale * 8 * dt
        
        # Анимация дыхания
        breath = math.sin(self._bounce_offset) * 0.05
        self._bounce_offset += dt * 1.5
        
        # Моргание
        self._blink_timer += dt
        if self._blink_timer > 4.0:
            self._blink_timer = 0
            self.blink()
        
        # Шевеление ушами
        self._ear_wiggle += dt * random.uniform(0.5, 2.0)
        
        # Применяем трансформации
        if hasattr(self, 'rot_y'):
            self.rot_y.angle = self._angle_y
            self.rot_x.angle = self._angle_x
            self.rot_z.angle = math.sin(self._ear_wiggle) * 3
            
            bounce = breath + math.sin(self._bounce_offset * 2) * 0.02
            self.trans.y = -0.5 + bounce
            self.scale.xyz = (self._scale_current,) * 3
        
        # Обновляем шейдер
        self.update_projection()
        self.canvas_obj['light_pos'] = (3.0, 4.0, 3.0)
        self.canvas_obj['ambient_light'] = (0.25, 0.25, 0.3)
        self.canvas_obj['diffuse_light'] = (0.7, 0.7, 0.7)
        self.canvas_obj['specular_light'] = (0.8, 0.7, 0.4)
        self.canvas_obj['shininess'] = 32.0
        self.canvas_obj['time'] = self._bounce_offset
        self.canvas_obj['camera_pos'] = (0, 0, 5)
    
    def random_action(self, dt):
        """Случайные действия Глагола"""
        r = random.random()
        
        if self.is_sleeping:
            return
        
        if r < 0.3:
            self.action_look_around()
        elif r < 0.5:
            self.action_bounce()
        elif r < 0.7:
            self.action_tilt_head()
        else:
            self.action_wiggle()
        
        Clock.schedule_once(self.random_action, random.uniform(4, 10))
    
    def action_bounce(self):
        """Подпрыгивание"""
        self._scale_target = 1.15
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 0.9), 0.15)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.0), 0.3)
        SoundManager().play('boing', 0.3)
    
    def action_look_around(self):
        """Оглядывается"""
        self._target_y = random.uniform(-30, 30)
        Clock.schedule_once(lambda dt: setattr(self, '_target_y', 0), 1.5)
    
    def action_tilt_head(self):
        """Наклоняет голову"""
        self._target_x = random.uniform(-25, -5)
        Clock.schedule_once(lambda dt: setattr(self, '_target_x', -15), 2.0)
    
    def action_wiggle(self):
        """Вибрирует"""
        self._scale_target = 1.05
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 0.95), 0.1)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.05), 0.2)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.0), 0.3)
    
    def blink(self):
        """Моргание"""
        pass  # Реализуется через морфинг или скейл век
    
    def on_touch_down(self, touch):
        """Реакция на прикосновение"""
        if self.collide_point(*touch.pos):
            # Определяем куда нажали
            rel_x = (touch.x / self.width) - 0.5
            rel_y = (touch.y / self.height) - 0.5
            
            # Поворот к пальцу
            self._target_y = rel_x * 40
            
            # Подпрыгивание
            self.action_bounce()
            
            # Звук
            SoundManager().play('hryuk')
            
            # Уменьшаем счастье при частых тыках
            self.happiness = max(0, self.happiness - 0.5)
            
            return True
        return super().on_touch_down(touch)
    
    def pet_belly(self):
        """Поглаживание пузика"""
        self._target_x = -25
        self._scale_target = 1.1
        self.is_sleeping = True
        SoundManager().play('xrap')
        
        Clock.schedule_once(lambda dt: setattr(self, '_target_x', -15), 1.0)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.0), 1.0)
        Clock.schedule_once(lambda dt: setattr(self, 'is_sleeping', False), 3.0)
    
    def feed(self):
        """Кормление"""
        self._scale_target = 1.3
        SoundManager().play('chavk')
        self.happiness = min(100, self.happiness + 20)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.0), 0.5)
    
    def give_crown(self):
        """Надевание короны"""
        self._target_x = -5
        self._scale_target = 1.2
        self._target_y = 360  # Полный оборот!
        SoundManager().play('dance')
        self.happiness = min(100, self.happiness + 30)
        Clock.schedule_once(lambda dt: setattr(self, '_target_y', 0), 2.0)
        Clock.schedule_once(lambda dt: setattr(self, '_target_x', -15), 2.0)
        Clock.schedule_once(lambda dt: setattr(self, '_scale_target', 1.0), 2.0)

# ============================================================
# ЭКРАН ИГРЫ
# ============================================================
class GameScreen(Screen):
    def __init__(self, model_files, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        
        self.model_files = model_files
        
        # Основной layout
        self.layout = FloatLayout()
        
        # Фоновый градиент
        with self.layout.canvas.before:
            Color(0.1, 0.5, 0.8, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=self.layout.size)
        self.layout.bind(size=self._update_bg)
        
        # 3D Глагол
        self.glagol_3d = Glagol3DRenderer(
            obj_path=model_files['obj'],
            texture_paths=model_files['jpg'],
            size_hint=(1, 0.65),
            pos_hint={'x': 0, 'y': 0.35}
        )
        self.layout.add_widget(self.glagol_3d)
        
        # Имя и уровень
        self.name_label = Label(
            text='[b]ГЛАГОЛ[/b]\nУровень 5',
            markup=True,
            font_size=24,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'y': 0.9}
        )
        self.layout.add_widget(self.name_label)
        
        # Шкала счастья
        self.happiness_bar = ProgressBar(
            max=100,
            value=100,
            size_hint=(0.8, 0.03),
            pos_hint={'x': 0.1, 'y': 0.87}
        )
        self.layout.add_widget(self.happiness_bar)
        
        # Кнопки действий
        self.create_action_buttons()
        
        # Монеты
        self.coin_label = Label(
            text='🪙 250',
            font_size=20,
            color=(1, 0.8, 0, 1),
            size_hint=(0.3, 0.05),
            pos_hint={'x': 0.35, 'y': 0.28}
        )
        self.layout.add_widget(self.coin_label)
        
        self.add_widget(self.layout)
        
        # Обновление UI
        Clock.schedule_interval(self.update_ui, 1/30.)
    
    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
    
    def create_action_buttons(self):
        """Создаёт кнопки действий"""
        actions = [
            ('🍎', 'Кормить', 0.05, self.feed_glagol),
            ('✋', 'Гладить', 0.28, self.pet_glagol),
            ('👑', 'Корона', 0.51, self.crown_glagol),
            ('🎮', 'Игры', 0.74, self.open_games),
        ]
        
        for emoji, text, x_pos, callback in actions:
            # Кнопка
            btn = Button(
                text=f'{emoji}\n{text}',
                font_size=18,
                size_hint=(0.2, 0.12),
                pos_hint={'x': x_pos, 'y': 0.12},
                background_color=(0.2, 0.6, 0.3, 0.8),
                color=(1, 1, 1, 1),
                halign='center',
                valign='middle'
            )
            btn.bind(on_press=callback)
            self.layout.add_widget(btn)
    
    def feed_glagol(self, instance):
        self.glagol_3d.feed()
        self._add_coins(5)
    
    def pet_glagol(self, instance):
        self.glagol_3d.pet_belly()
        self._add_coins(3)
    
    def crown_glagol(self, instance):
        self.glagol_3d.give_crown()
        self._add_coins(10)
    
    def open_games(self, instance):
        self.manager.current = 'minigames'
    
    def _add_coins(self, amount):
        current = GameStorage().load('coins', 0)
        GameStorage().save('coins', current + amount)
    
    def update_ui(self, dt):
        # Обновляем шкалу счастья
        self.happiness_bar.value = self.glagol_3d.happiness
        
        # Обновляем монеты
        coins = GameStorage().load('coins', 0)
        self.coin_label.text = f'🪙 {coins}'
        
        # Уменьшаем счастье со временем
        if not self.glagol_3d.is_sleeping:
            self.glagol_3d.happiness = max(0, self.glagol_3d.happiness - 0.02)

# ============================================================
# ЭКРАН МИНИ-ИГР
# ============================================================
class MinigamesScreen(Screen):
    def __init__(self, **kwargs):
        super(MinigamesScreen, self).__init__(**kwargs)
        
        layout = FloatLayout()
        
        # Заголовок
        title = Label(
            text='[b]МИНИ-ИГРЫ[/b]',
            markup=True,
            font_size=32,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0.88}
        )
        layout.add_widget(title)
        
        # Кнопки мини-игр
        games = [
            ('🏃', 'Раннер Глагола', self.start_runner),
            ('🎯', 'Метание яблок', self.start_apple_throw),
            ('💥', 'Лопни шары', self.start_balloon_pop),
            ('🧩', 'Пазл Глагола', self.start_puzzle),
            ('🎰', 'Колесо удачи', self.start_wheel),
        ]
        
        for i, (emoji, name, callback) in enumerate(games):
            y_pos = 0.72 - (i * 0.14)
            
            btn = Button(
                text=f'{emoji}  {name}',
                font_size=20,
                size_hint=(0.9, 0.1),
                pos_hint={'x': 0.05, 'y': y_pos},
                background_color=(0.2, 0.5, 0.3, 0.9),
                color=(1, 1, 1, 1),
                halign='left',
                valign='middle'
            )
            btn.bind(on_press=callback)
            layout.add_widget(btn)
        
        # Кнопка назад
        back_btn = Button(
            text='← НАЗАД',
            font_size=22,
            size_hint=(0.4, 0.07),
            pos_hint={'x': 0.3, 'y': 0.02},
            background_color=(0.7, 0.2, 0.2, 0.9),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def start_runner(self, instance):
        game = MinigameManager().start('runner')
        self.show_game_popup(game)
    
    def start_apple_throw(self, instance):
        game = MinigameManager().start('apple_throw')
        self.show_game_popup(game)
    
    def start_balloon_pop(self, instance):
        game = MinigameManager().start('balloon_pop')
        self.show_game_popup(game)
    
    def start_puzzle(self, instance):
        game = MinigameManager().start('puzzle')
        self.show_game_popup(game)
    
    def start_wheel(self, instance):
        game = MinigameManager().start('wheel')
        self.show_game_popup(game)
    
    def show_game_popup(self, game_widget):
        popup = Popup(
            title=f'Мини-игра: {game_widget.game_name}',
            content=game_widget,
            size_hint=(0.95, 0.85),
            auto_dismiss=False
        )
        game_widget.popup = popup
        popup.open()
    
    def go_back(self, instance):
        self.manager.current = 'game'

# ============================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================
class GlagolApp(App):
    def build(self):
        self.title = 'Говорящий Глагол 3D'
        
        # Загружаем звуки
        SoundManager().load()
        
        # Извлекаем модель
        extractor = ModelExtractor()
        if not extractor.extract():
            print("Модель не найдена! Создаём fallback...")
            return Label(text='Ошибка: модель не найдена\nКинь ZIP в папку!')
        
        model_files = extractor.files
        
        # Инициализируем хранилище
        storage = GameStorage()
        if storage.load('coins') is None:
            storage.save('coins', 100)
            storage.save('level', 1)
            storage.save('highscore_runner', 0)
            storage.save('highscore_apple', 0)
            storage.save('highscore_balloon', 0)
        
        # Создаём экраны
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(GameScreen(model_files=model_files, name='game'))
        sm.add_widget(MinigamesScreen(name='minigames'))
        
        return sm

# ============================================================
# ТОЧКА ВХОДА
# ============================================================
if __name__ == '__main__':
    GlagolApp().run()
