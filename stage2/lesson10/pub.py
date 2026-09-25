import time
import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"
PORT = 1883
CLIENT_ID = "pi3-telemetry"
STATUS_TOPIC = "stand/pi3/status"
TEMP_TOPIC = "stand/pi3/cpu_temp"
PERIOD = 30
SENSOR = "/sys/class/thermal/thermal_zone0/temp"


def read_cpu_temp():
    with open(SENSOR) as f:
        return int(f.read()) / 1000


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Брокер отказал: {reason_code}")
        return
    print("Подключено к брокеру")
    client.publish(STATUS_TOPIC, "online", qos=1, retain=True)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.will_set(STATUS_TOPIC, "offline", qos=1, retain=True)

client.connect(BROKER, PORT, 30)
client.loop_start()

while True:
    temp = read_cpu_temp()
    client.publish(TEMP_TOPIC, f"{temp:.1f}", retain=True)
    time.sleep(PERIOD)