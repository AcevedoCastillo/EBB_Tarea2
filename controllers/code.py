from controller import Robot
import math
import datetime

# ===== CONFIGURACIÓN GENERAL =====
TIME_STEP = 64
MAX_SPEED = 6.28

# ===== INICIALIZACIÓN DE ROBOT =====
robot = Robot()

# Sensores de proximidad
prox_sensors = []
for i in range(8):
    sensor = robot.getDevice(f'ps{i}')
    sensor.enable(TIME_STEP)
    prox_sensors.append(sensor)

# Sensores adicionales (usa try-except por si no existen)
try:
    light_sensor = robot.getDevice("ls0")
    light_sensor.enable(TIME_STEP)
except:
    light_sensor = None

try:
    gyro = robot.getDevice("gyro")
    gyro.enable(TIME_STEP)
except:
    gyro = None

try:
    acc = robot.getDevice("accelerometer")
    acc.enable(TIME_STEP)
except:
    acc = None

try:
    camera = robot.getDevice("camera")
    camera.enable(TIME_STEP)
except:
    camera = None

# Motores
left_motor = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

# LEDs
leds = []
for i in range(10):
    try:
        led = robot.getDevice(f'led{i}')
        leds.append(led)
    except:
        pass  # Si algún LED no existe, lo ignora

def set_led_state(state: str):
    """Controla el color del LED según el estado."""
    colors = {
        'go': (1, 0, 0),       # Verde
        'turning': (0, 0, 1),  # Azul
        'obstacle': (0, 1, 0), # Rojo
        'goal': (1, 1, 0),     # Amarillo
        'stuck': (1, 0, 1),    # Violeta
    }
    r, g, b = colors.get(state, (0, 0, 0))
    for led in leds:
        led.set(r + g * 2 + b * 4)

def read_proximity(index):
    return prox_sensors[index].getValue()

# ===== MÉTRICAS =====
start_time = robot.getTime()
distance = 0.0
collisions = 0
goal_reached = False

# ===== NAVEGACIÓN PRINCIPAL =====
def navigate():
    global collisions, goal_reached

    # Sensores clave
    front_left = read_proximity(0)
    front_right = read_proximity(7)
    side_right = read_proximity(2)

    # Lógica de navegación basada en "seguir pared derecha"
    obstacle_ahead = front_left > 80 or front_right > 80
    right_clear = side_right < 60

    # Detectar colisiones
    if front_left > 100 and front_right > 100:
        collisions += 1
        set_led_state('obstacle')
        left_motor.setVelocity(-0.5 * MAX_SPEED)
        right_motor.setVelocity(-0.5 * MAX_SPEED)
        # Espera mientras retrocede
        for _ in range(5):
            robot.step(TIME_STEP)
        return

    if obstacle_ahead:
        set_led_state('turning')
        left_motor.setVelocity(0.4 * MAX_SPEED)
        right_motor.setVelocity(-0.4 * MAX_SPEED)
    elif right_clear:
        set_led_state('turning')
        left_motor.setVelocity(0.6 * MAX_SPEED)
        right_motor.setVelocity(0.2 * MAX_SPEED)
    else:
        set_led_state('go')
        left_motor.setVelocity(0.5 * MAX_SPEED)
        right_motor.setVelocity(0.5 * MAX_SPEED)

    # Detectar fuente de luz como meta alcanzada
    if light_sensor and light_sensor.getValue() > 600:
        set_led_state('goal')
        goal_reached = True

# ===== BUCLE PRINCIPAL =====
print("Controlador iniciado correctamente.")
while robot.step(TIME_STEP) != -1 and not goal_reached:
    print("Ciclo activo.")
    navigate()

    # Estimar distancia recorrida
    v_left = left_motor.getVelocity()
    v_right = right_motor.getVelocity()
    v_avg = (v_left + v_right) / 2
    distance += abs(v_avg * (TIME_STEP / 1000))

# ===== RESULTADOS =====
end_time = robot.getTime()
total_time = end_time - start_time

# Mostrar en consola
print("\n===== RESULTADOS DE NAVEGACIÓN =====")
print(f"Tiempo total     : {total_time:.2f} s")
print(f"Distancia aprox. : {distance:.2f} unidades")
print(f"Colisiones       : {collisions}")
print(f"Meta alcanzada   : {'Sí' if goal_reached else 'No'}")

# Guardar en archivo
fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
try:
    with open(f"resultados_navegacion_{fecha}.txt", "w") as file:
        file.write("===== RESULTADOS DE NAVEGACIÓN =====\n")
        file.write(f"Tiempo total     : {total_time:.2f} s\n")
        file.write(f"Distancia aprox. : {distance:.2f} unidades\n")
        file.write(f"Colisiones       : {collisions}\n")
        file.write(f"Meta alcanzada   : {'Sí' if goal_reached else 'No'}\n")
except:
    print("⚠️ No se pudo guardar el archivo de resultados.")
