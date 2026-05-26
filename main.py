import math
import logging
import arcade
import pymunk

from game_object import Bird, Column, Pig, Beam, YellowBird, BlueBird
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900

SLING_X = 150
SLING_Y = 70
MAX_STRETCH = 125

BIRD_START_X = SLING_X
BIRD_START_Y = SLING_Y

DESTROY_IMPULSE = 450

import os

carpeta = os.path.join(os.path.dirname(__file__), "assets", "img")
nombres = ["background3.png", "beam.png", "blue.png", "chuck.png",
           "column.png", "pig_failed.png", "red-bird3.png", "sling-3.png", "yellow.png"]

imagenes = {nombre: arcade.load_texture(os.path.join(carpeta, nombre)) for nombre in nombres}


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = imagenes["background3.png"]
        self.sling_texture = imagenes["sling-3.png"]

        self.startup_frames = 0
        self.startup_delay = 120

        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10.0
        floor_shape.elasticity = 0.1
        floor_shape.collision_type = 4
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()

        self.pending_removals = []
        self.start_point = Point2D(BIRD_START_X, BIRD_START_Y)
        self.end_point = Point2D(BIRD_START_X, BIRD_START_Y)
        self.draw_line = False
        self.aiming = False

        self.current_bird_kind = "red"
        self.active_bird = None
        self.can_launch = True  # Nuevo: controla si se puede lanzar
        self.launch_timer = 0   # Nuevo: temporizador para el siguiente lanzamiento
        self.wait_time = 3.0

        self.add_columns()
        self.add_pigs()

        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

    def add_object(self, obj):
        self.sprites.append(obj)
        self.world.append(obj)

    def remove_object(self, obj):
        if obj is None:
            return
        if obj in self.sprites:
            obj.remove_from_sprite_lists()
        if obj in self.world:
            obj.remove_from_sprite_lists()
        if obj in self.birds:
            obj.remove_from_sprite_lists()
        try:
            self.space.remove(obj.shape, obj.body)
        except Exception:
            pass
        if obj is self.active_bird:
            self.active_bird = None

    def add_columns(self):
        # Separación más pequeña entre letras (120px en lugar de 180px)
        
        # 'O' - x=200-300
        self.add_object(Column(600, 60, self.space, static=True))
        self.add_object(Column(600, 140, self.space, static=True))
        self.add_object(Column(700, 60, self.space, static=True))
        self.add_object(Column(700, 140, self.space, static=True))
        self.add_object(Beam(650, 30, self.space, static=True))
        self.add_object(Beam(650, 190, self.space, static=True))
        
        # 'S' - x=350-450
        self.add_object(Column(850, 60, self.space, static=True))
        self.add_object(Beam(800, 30, self.space, static=True))
        self.add_object(Column(750, 140, self.space, static=True))
        self.add_object(Beam(800, 190, self.space, static=True))
        self.add_object(Beam(800, 110, self.space, static=True))
        
        # 'C' - x=500-600
        self.add_object(Column(900, 60, self.space, static=True))
        self.add_object(Column(900, 140, self.space, static=True))
        self.add_object(Beam(950, 30, self.space, static=True))
        self.add_object(Beam(950, 190, self.space, static=True))
        
        # 'A' - x=650-750
        self.add_object(Column(1050, 60, self.space, static=True))
        self.add_object(Column(1050, 140, self.space, static=True))
        self.add_object(Column(1150, 60, self.space, static=True))
        self.add_object(Column(1150, 140, self.space, static=True))
        self.add_object(Beam(1100, 110, self.space, static=True))
        self.add_object(Beam(1100, 190, self.space, static=True))
       
        # 'R' - x=800-900
        self.add_object(Column(1250, 60, self.space, static=True))
        self.add_object(Column(1250, 140, self.space, static=True))
        self.add_object(Column(1300, 60, self.space, static=True))
        self.add_object(Column(1350, 140, self.space, static=True))
       
        self.add_object(Beam(1300, 110, self.space, static=True))
        self.add_object(Beam(1300, 190, self.space, static=True))
        

    def add_pigs(self):
        # Posiciones ajustadas para la versión compacta
        pig_positions = [
            # O
            (650, 70), 
            
            # S
            (800, 70), (800, 150),
            # C
            (950, 70),
            # A
            (1100, 50), (1100, 150),
            # R
            (1300, 150), 
        ]
        
        for x, y in pig_positions:
            self.add_object(Pig(x, y, self.space, static=True))
        
        
    
  
    def collision_handler(self, arbiter, space, data):
        if self.startup_frames < self.startup_delay:
            return True
    
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < DESTROY_IMPULSE:
            return True

        shapes = arbiter.shapes
        for obj in list(self.world):
            if obj.shape in shapes:
                if isinstance(obj, Pig) or isinstance(obj, Column) or isinstance(obj, Beam):
                    if obj not in self.pending_removals:
                        self.pending_removals.append(obj)

        return True

    def process_pending_removals(self):
        while self.pending_removals:
            obj = self.pending_removals.pop(0)
            self.remove_object(obj)

    def bird_is_flying(self, bird):
        if bird is None:
            return False
        if bird.body not in self.space.bodies:
            return False
        return bird.body.velocity.length > 12

    def get_launch_vector(self):
        return get_impulse_vector(self.start_point, self.end_point)

    def clamp_to_sling(self, x, y):
        dx = x - self.start_point.x
        dy = y - self.start_point.y
        dist = math.hypot(dx, dy)
        if dist <= MAX_STRETCH or dist == 0:
            return x, y
        scale = MAX_STRETCH / dist
        return self.start_point.x + dx * scale, self.start_point.y + dy * scale

    def create_bird(self, impulse_vector, x, y):
        if self.current_bird_kind == "yellow":
            return YellowBird(impulse_vector, x, y, self.space)
        if self.current_bird_kind == "blue":
            return BlueBird(impulse_vector, x, y, self.space)
        return Bird(imagenes["red-bird3.png"], impulse_vector, x, y, self.space)

    def launch_bird(self):
        if not self.can_launch:  # Verificar si se puede lanzar
            logger.debug("Espera para lanzar otro pájaro")
            return
    
        impulse_vector = self.get_launch_vector()
        if impulse_vector.impulse < 5:
            self.draw_line = False
            self.aiming = False
            return

        bird = self.create_bird(impulse_vector, BIRD_START_X, BIRD_START_Y)
        self.sprites.append(bird)
        self.birds.append(bird)
        self.active_bird = bird
        self.draw_line = False
        self.aiming = False
        
        # Deshabilitar lanzamiento hasta que pase el tiempo
        self.can_launch = False
        self.launch_timer = 0

    def use_active_bird_power(self):
        bird = self.active_bird
        if bird is None or not self.bird_is_flying(bird):
            return

        if isinstance(bird, YellowBird):
            if bird.boost():
                logger.debug("Yellow bird boost activated")
        elif isinstance(bird, BlueBird):
            new_birds = bird.split()
            if new_birds:
                logger.debug("Blue bird split activated")
                self.remove_object(bird)
                for new_bird in new_birds:
                    self.sprites.append(new_bird)
                    self.birds.append(new_bird)
                self.active_bird = new_birds[0]

    def cleanup_birds(self):
        for bird in list(self.birds):
            if bird.body not in self.space.bodies:
                self.remove_object(bird)
                continue

            if bird.body.velocity.length < 8 and bird.body.position.y <= 120:
                if bird is self.active_bird:
                    self.active_bird = None

            if bird.body.position.y < -150 or bird.body.position.x < -250 or bird.body.position.x > WIDTH + 250:
                self.remove_object(bird)

    def on_update(self, delta_time: float):
        if self.startup_frames < self.startup_delay:
            self.startup_frames += 1

        self.space.step(1 / 60.0)
        self.sprites.update(delta_time)
        self.process_pending_removals()
        self.cleanup_birds()
        # Manejar el temporizador para lanzar nuevo pájaro
        if not self.can_launch:
            self.launch_timer += delta_time
            if self.launch_timer >= self.wait_time:
                self.can_launch = True
                self.launch_timer = 0
                logger.debug("Puedes lanzar otro pájaro")

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.bird_is_flying(self.active_bird):
            self.use_active_bird_power()
            return

        if get_distance(Point2D(x, y), self.start_point) <= 120:
            self.aiming = True
            self.draw_line = True
            clamped_x, clamped_y = self.clamp_to_sling(x, y)
            self.end_point = Point2D(clamped_x, clamped_y)
        else:
            self.aiming = False
            self.draw_line = False

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT and self.aiming:
            clamped_x, clamped_y = self.clamp_to_sling(x, y)
            self.end_point = Point2D(clamped_x, clamped_y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.aiming:
            clamped_x, clamped_y = self.clamp_to_sling(x, y)
            self.end_point = Point2D(clamped_x, clamped_y)
            self.launch_bird()
        self.aiming = False
        self.draw_line = False

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.current_bird_kind = "red"
        elif key == arcade.key.Y:
            self.current_bird_kind = "yellow"
        elif key == arcade.key.B:
            self.current_bird_kind = "blue"

    def draw_trajectory(self):
        launch = self.get_launch_vector()
        if launch.impulse < 5:
            return

        impulse = min(300, launch.impulse) * 50
        mass = 5
        speed = impulse / mass
        vx = math.cos(launch.angle) * speed
        vy = math.sin(launch.angle) * speed

        points = []
        steps = 24
        dt = 0.08

        for i in range(steps):
            t = i * dt
            x = BIRD_START_X + vx * t
            y = BIRD_START_Y + vy * t + 0.5 * GRAVITY * t * t
            points.append((x, y))

        for i in range(len(points) - 1):
            arcade.draw_line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], arcade.color.WHITE, 2)

    def on_draw(self):
        self.clear()

        # Fondo
        arcade.draw_texture_rect(
            self.background,
            arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT)
        )

        # Sprites
        self.sprites.draw()

        # Resortera
        arcade.draw_texture_rect(
            self.sling_texture,
            arcade.XYWH(
                190, 50,
                self.sling_texture.width * 0.8,
                self.sling_texture.height * 0.8,
            )
        )
        
        # Pájaro listo
        if not self.bird_is_flying(self.active_bird) and not self.aiming:
            if self.current_bird_kind == "yellow":
                ready_texture = imagenes["chuck.png"]
                ancho, alto = 0.3, 0.3
            elif self.current_bird_kind == "blue":
                ready_texture = imagenes["blue.png"]
                ancho, alto = 0.3, 0.3
            else:
                ready_texture = imagenes["red-bird3.png"]
                ancho, alto = 2, 2

            arcade.draw_texture_rect(
                ready_texture,
                arcade.XYWH(BIRD_START_X, BIRD_START_Y,
                             ready_texture.width * ancho,
                             ready_texture.height * alto)
            )

        # Línea de trayectoria
        if self.draw_line:
            arcade.draw_line(
                self.start_point.x, self.start_point.y,
                self.end_point.x, self.end_point.y,
                arcade.color.BLACK, 3
            )
            self.draw_trajectory()

        # Textos
        arcade.draw_text(
            f"Ave actual: {self.current_bird_kind.upper()}   |   Teclas: R rojo, Y amarillo, B azul",
            20, HEIGHT - 30, arcade.color.WHITE, 16
        )
        arcade.draw_text(
            "Click y arrastra sobre la resortera. Si el pájaro está en vuelo, un click activa su poder.",
            20, HEIGHT - 55, arcade.color.WHITE, 14
        )



def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
