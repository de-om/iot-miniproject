import utime
from utime import sleep_ms

from ubinascii import hexlify

from machine import Pin, reset, unique_id

from hcsr04 import HCSR04
from dht import DHT11
from umqtt.simple import MQTTClient

# La conexion a wifi la hacemos en boot.py

# INPUTS / OUTPUTS
led = Pin(2, Pin.OUT)  # LED de alerta de proximidad
hcsr_sensor = HCSR04(12,13)  # Sensor de proximidad
sensorDHT = DHT11(Pin(15,Pin.IN))  # Sensor de temperatura y humedad

# CONSTANTES
INTERVAL = 5000  # ms
MQTT_SERVER = "broker.hivemq.com"  # broker publico con el que podemos hacer pruebas tiene un cliente web en http://www.hivemq.com/demos/websocket-client/
MQTT_TOPIC = "eoi/iot"
ID_CLIENT = hexlify('eoi-DanielEOM')  # El nombre con el que nos registremos en el broker tiene que ser unico

# CALLBACK cuando se reciben mensajes (Cuando hacemos check_msg() y hay mensajes en los topics suscritos entra aqui)
def mqtt_callback(topic, msg):
    msg = msg.decode()  # son array de bytes, lo pasamos a string
    topic = topic.decode()
    print(f"Me llego por '{topic}' esto: '{msg}'.")
    if topic == MQTT_TOPIC:
        try:
            dist = float(msg.lstrip("Dist: "))
            if dist < 10:
                led.on()
                sensorDHT.measure()
                temp = sensorDHT.temperature()
                hum = sensorDHT.humidity()
                print(f"T={temp:02d} ºC, {hum:02d} %")
                print("Algo está a menos de 10cm!")
                utime.sleep_ms(INTERVAL)
                led.off()
        except:
            pass

# PUBLICAR MENSAJES
def publish_mqtt_message(topic, message):
    try:
        client = MQTTClient(ID_CLIENT + "-esp32", MQTT_SERVER)
        client.connect()
        client.publish(topic, message)
        client.disconnect()
    except Exception as e:
        print(message)
        print("Error al publicar mensaje MQTT:", e)

client = MQTTClient(ID_CLIENT, MQTT_SERVER)  # si no decimos nada usa el puerto por defecto 1883
client.set_callback(mqtt_callback)  # cuando entren mensajes por los topics a los que estamos suscritos, dispara el callback
client.connect()

client.subscribe(MQTT_TOPIC)  # nos suscribimos al topic

proximo_envio = utime.ticks_ms() + INTERVAL  # utilizamos este sistema para enviar mensajes cada 5 segundos

while True:
    try:
        client.check_msg()  # comprueba mensajes, llamar frecuentemente pero no de continuo que nos da error
            
        # Periodicamente manda mensajes, pero sin bloquear
        if utime.ticks_ms() > proximo_envio:
            
            # Mensaje de conexión:
#             default_message = "Hola mundo, me envía Dani cada 5 segundos."
#             publish_mqtt_message(MQTT_TOPIC, default_message)
            
            # Mensaje de distancia
            distance_cm = hcsr_sensor.distance_cm()
            dist_message = f'Dist: {distance_cm}'
            publish_mqtt_message(MQTT_TOPIC, dist_message)
            
            # Mensaje de temperatura y humedad
            sensorDHT.measure()
            temp = sensorDHT.temperature()
            hum = sensorDHT.humidity()
            dht_message = f"T={temp:02d} ºC, {hum:02d} %"
            publish_mqtt_message(MQTT_TOPIC, dht_message)
            
            proximo_envio = utime.ticks_ms() + INTERVAL
    
    except OSError as e:
        print("Error de conexión MQTT:", e)
        
    utime.sleep_ms(INTERVAL)
