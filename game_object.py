import math
import arcade
import pymunk
from game_logic import ImpulseVector


BIRD_COLLISION_TYPE = 1
PIG_COLLISION_TYPE = 2
BLOCK_COLLISION_TYPE = 3
GROUND_COLLISION_TYPE = 4

import os

carpeta = os.path.join(os.path.dirname(__file__), "assets", "img")
nombres = ["background3.png", "beam.png", "blue.png", "chuck.png",
           "column.png", "pig_failed.png", "red-bird3.png", "sling-3.png", "yellow.png"]

imagenes = {nombre: arcade.load_texture(os.path.join(carpeta, nombre)) for nombre in nombres}

class Bird(arcade.Sprite):
    """
    Bird class. This represents an angry bird. All the physics is handled by Pymunk,
    the init method only set some initial properties
    """
    def __init__(
        self,
        path_or_texture,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 25,
        max_impulse: float = 300,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = BIRD_COLLISION_TYPE,
    ):
        super().__init__(path_or_texture, 1)

        
        self.space = space
        self.launched = True
        ##       
        self.scale = 2

        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        impulse_pymunk = impulse * pymunk.Vec2d(1, 0)
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))

        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        shape.filter = pymunk.ShapeFilter(group=1)

        space.add(body, shape)

        self.body = body
        self.shape = shape

    def is_active(self) -> bool:
        return self.body is not None and self.body.velocity.length > 10

    def update(self, delta_time):
        """
        Update the position of the bird sprite based on the physics body position
        """
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = PIG_COLLISION_TYPE,
        static: bool = False,
    ):
        super().__init__(imagenes["pig_failed.png"], 0.1)
        if static:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (x, y)
        else:
            moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
            body = pymunk.Body(mass, moment)
            body.position = (x, y)
        
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape
        self.static = static
        self.center_x = body.position.x
        self.center_y = body.position.y
        self.scale = 0.3

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class PassiveObject(arcade.Sprite):
    """
    Passive object that can interact with other objects.
    """
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.1,
        friction: float = 1.0,
        collision_layer: int = BLOCK_COLLISION_TYPE,
        static: bool = False,
    ):
        super().__init__(image_path, 1)

        if static:
            # Crear como cuerpo estático
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (x, y)
        else:
            # Crear como cuerpo dinámico normal
            moment = pymunk.moment_for_box(mass, (self.width, self.height))
            body = pymunk.Body(mass, moment)
            body.position = (x, y)

      
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape
        self.static = static 
        self.center_x = body.position.x
        self.center_y = body.position.y

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
   def __init__(self, x, y, space, static=False):
        super().__init__(imagenes["column.png"], x, y, space, static=static)


class Beam(PassiveObject):
    def __init__(self, x, y, space, static=False):
        super().__init__(imagenes["beam.png"], x, y, space, static=static)


class YellowBird(Bird):
    """
    Variante del Bird que, mientras esta en vuelo, puede recibir un "boost".

    Comportamiento esperado:
    - Si el usuario hace clic izquierdo mientras este pajaro esta en vuelo,
      su impulso se multiplica por `power_multiplier` (default 2) aplicado
      en la direccion ACTUAL de movimiento.
    - El boost solo deberia aplicarse una vez (no acumular en cada clic).
    - Recomendacion: usar "assets/img/chuck.png" como sprite.

    Pista: para aplicar el boost, usar
        self.body.apply_impulse_at_local_point(...)
    con un vector en la direccion actual de la velocidad del cuerpo
    (self.body.velocity).
    """

    def __init__(
        self,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 9,
        max_impulse: float = 300,
        power_multiplier: float = 50,
        boost_multiplier: float = 2.0,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = BIRD_COLLISION_TYPE,
    ):
        super().__init__(
            imagenes["chuck.png"],
            impulse_vector,
            x,
            y,
            space,
            mass=mass,
            radius=radius,
            max_impulse=max_impulse,
            power_multiplier=power_multiplier,
            elasticity=elasticity,
            friction=friction,
            collision_layer=collision_layer,
        )
        self.scale = 0.3
        self.boost_multiplier = boost_multiplier
        self.boost_used = False

    def boost(self) -> bool:
        if self.boost_used:
            return False

        velocity = self.body.velocity
        speed = velocity.length
        if speed < 1:
            return False

        direction = velocity.normalized()
        extra_impulse = direction * (self.body.mass * speed * (self.boost_multiplier - 1.0))
        self.body.apply_impulse_at_local_point(extra_impulse)
        self.boost_used = True
        return True


class BlueBird(Bird):
    """
    Variante del Bird que se divide en 3 al hacer clic en vuelo.

    Comportamiento esperado:
    - Si el usuario hace clic izquierdo mientras este pajaro esta en vuelo,
      instantaneamente se reemplaza por 3 BlueBirds con direcciones de
      vuelo separadas por +30, 0 y -30 grados respecto a la direccion
      actual. La magnitud de la velocidad se preserva.
    - La division solo deberia ocurrir una vez por pajaro.
    - Recomendacion: usar "assets/img/blue.png" como sprite.

    Pista: para crear los 2 nuevos pajaros se necesita acceso al
    pymunk.Space y a las SpriteLists del juego. El metodo puede devolver
    los nuevos pajaros para que main.py los agregue, o recibir las listas
    como argumento. Esa decision de diseno es parte del ejercicio.
    """

    def __init__(
        self,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 8,
        max_impulse: float = 300,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = BIRD_COLLISION_TYPE,
    ):
        super().__init__(
            imagenes["blue.png"],
            impulse_vector,
            x,
            y,
            space,
            mass=mass,
            radius=radius,
            max_impulse=max_impulse,
            power_multiplier=power_multiplier,
            elasticity=elasticity,
            friction=friction,
            collision_layer=collision_layer,
        )
        self.scale = 0.3
        self.split_used = False

    def split(self):
        if self.split_used:
            return []

        speed = self.body.velocity.length
        if speed < 1:
            return []

        base_angle = math.atan2(self.body.velocity.y, self.body.velocity.x)
        offsets = [0, math.radians(30), math.radians(-30)]
        birds = []

        for offset in offsets:
            impulse_vector = ImpulseVector(0, 0)
            bird = BlueBird(
                impulse_vector,
                self.body.position.x,
                self.body.position.y,
                self.space,
                mass=self.body.mass,
                radius=12,
                max_impulse=0,
                power_multiplier=0,
            )
            bird.body.position = self.body.position
            bird.body.velocity = pymunk.Vec2d(speed, 0).rotated(base_angle + offset)
            bird.body.angle = self.body.angle
            bird.body.angular_velocity = self.body.angular_velocity
            bird.split_used = True
            birds.append(bird)

        self.split_used = True
        return birds
