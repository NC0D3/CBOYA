from gpiozero import Button
from signal import pause

# Define el botón físico en el pin GPIO 17
button = Button(17)

# Función que se ejecuta cuando el botón es pulsado
def button_pressed():
    print("Botón pulsado")

# Función que se ejecuta cuando el botón es despulsado
def button_released():
    print("Botón despulsado")

# Conectar las funciones a los eventos del botón
button.when_pressed = button_pressed
button.when_released = button_released

# Mantener el programa ejecutándose
print("Programa iniciado. Presiona el botón para ver los mensajes.")
pause()
