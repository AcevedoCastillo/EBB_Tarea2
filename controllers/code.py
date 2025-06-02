from controller import Robot
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

# Cámara (solo habilitar, sin procesamiento)
camera = robot.getDevice("camera")
camera.enable(TIME_STEP)

# Motores
left_motor = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

# LEDs (opcional, para mostrar estados)
leds = []
for i in range(10):
    try:
        led = robot.getDevice(f'led{i}')
        leds.append(led)
    except:
        pass

def set_led_state(state: str):
    """Controla el color del LED según el estado."""
    colors = {
        'go': (1, 0, 0),       # Verde (r=1)
        'turning': (0, 0, 1),  # Azul (b=1)
        'obstacle': (0, 1, 0), # Rojo (g=1)
        'goal': (1, 1, 0),     # Amarillo (r=1, g=1)
        'stuck': (1, 0, 1),    # Violeta (r=1, b=1)
    }
    r, g, b = colors.get(state, (0, 0, 0))
    for led in leds:
        led.set(r + g * 2 + b * 4)  # Esto es la suma para el valor del led (según Webots)

def read_proximity(index):
    return prox_sensors[index].getValue()

# ===== MÉTRICAS =====
start_time = robot.getTime()
distance = 0.0
collisions = 0
goal_reached = False
stuck_counter = 0  # Para detectar si está atascado

# ===== NAVEGACIÓN PRINCIPAL =====
def navigate():
    global collisions, goal_reached, stuck_counter

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
        stuck_counter += 1
        for _ in range(5):
            robot.step(TIME_STEP)
        return

    # Lógica de movimiento
    if obstacle_ahead:
        set_led_state('turning')
        left_motor.setVelocity(0.4 * MAX_SPEED)
        right_motor.setVelocity(-0.4 * MAX_SPEED)
        stuck_counter += 1
    elif right_clear:
        set_led_state('turning')
        left_motor.setVelocity(0.6 * MAX_SPEED)
        right_motor.setVelocity(0.2 * MAX_SPEED)
        stuck_counter = 0
    else:
        set_led_state('go')
        left_motor.setVelocity(0.5 * MAX_SPEED)
        right_motor.setVelocity(0.5 * MAX_SPEED)
        stuck_counter = 0

# ===== BUCLE PRINCIPAL =====
print("Controlador iniciado correctamente.")
max_stuck = 50  # Máximos ciclos permitidos sin progreso

while robot.step(TIME_STEP) != -1 and not goal_reached and stuck_counter < max_stuck:
    navigate()

    # Estimar distancia recorrida
    v_left = left_motor.getVelocity()
    v_right = right_motor.getVelocity()
    v_avg = (v_left + v_right) / 2
    distance += abs(v_avg * (TIME_STEP / 1000))

# Detener motores
left_motor.setVelocity(0)
right_motor.setVelocity(0)

# Estado final si se quedó atascado
if stuck_counter >= max_stuck and not goal_reached:
    set_led_state('stuck')
    print("⚠️ Robot atascado. Detenido por seguridad.")

# ===== RESULTADOS =====
end_time = robot.getTime()
total_time = end_time - start_time

print("\n===== RESULTADOS DE NAVEGACIÓN =====")
print(f"Tiempo total     : {total_time:.2f} s")
print(f"Distancia aprox. : {distance:.2f} unidades")
print(f"Colisiones       : {collisions}")
print(f"Meta alcanzada   : {'Sí' if goal_reached else 'No'}")
print(f"Estado final     : {'Atascado' if stuck_counter >= max_stuck else 'Finalizado correctamente'}")

# Guardar en archivo
fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
try:
    with open(f"resultados_navegacion_{fecha}.txt", "w") as file:
        file.write("===== RESULTADOS DE NAVEGACIÓN =====\n")
        file.write(f"Tiempo total     : {total_time:.2f} s\n")
        file.write(f"Distancia aprox. : {distance:.2f} unidades\n")
        file.write(f"Colisiones       : {collisions}\n")
        file.write(f"Meta alcanzada   : {'Sí' if goal_reached else 'No'}\n")
        file.write(f"Estado final     : {'Atascado' if stuck_counter >= max_stuck else 'Finalizado correctamente'}\n")
except:
    print("⚠️ No se pudo guardar el archivo de resultados.")
