import time
import paho.mqtt.client as mqtt
from gpiozero import LED

BROKER = "127.0.0.1"
PORT = 1883
CLIENT_ID = "pi3-device"
DEVICE = "stand_pi3"
BASE = f"/devices/{DEVICE}"
STATUS_TOPIC = "stand/pi3/status"
PERIOD = 30
LED_PIN = 17

CONTROLS = {
    "cpu_temp": {"type": "temperature", "readonly": "1", "order": "1"},
    "uptime": {"type": "value", "units": "s", "readonly": "1", "order": "2"},
    "led": {"type": "switch", "readonly": "0", "order": "3"},
}

led = LED(LED_PIN, initial_value=False)


def read_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read()) / 1000


def read_uptime():
    with open("/proc/uptime") as f:
        return float(f.read().split()[0])


def publish_meta(client):
    client.publish(f"{BASE}/meta/name", "Стенд: малинка pi3", qos=1, retain=True)
    for control, meta in CONTROLS.items():
        for key, value in meta.items():
            client.publish(f"{BASE}/controls/{control}/meta/{key}", value, qos=1, retain=True)


def publish_value(client, control, value):
    client.publish(f"{BASE}/controls/{control}", value, retain=True)


def publish_led_state(client):
    publish_value(client, "led", str(int(led.is_lit)))


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Брокер отказал: {reason_code}")
        return
    print("Подключено к брокеру")
    client.publish(STATUS_TOPIC, "online", qos=1, retain=True)
    publish_meta(client)
    publish_led_state(client)
    client.subscribe(f"{BASE}/controls/led/on")


def on_message(client, userdata, msg):
    command = msg.payload.decode("utf-8", errors="replace").strip()
    if command == "1":
        led.on()
    elif command == "0":
        led.off()
    else:
        print(f"Неизвестная команда для led: {command!r}")
    publish_led_state(client)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message
client.will_set(STATUS_TOPIC, "offline", qos=1, retain=True)

client.connect(BROKER, PORT, 30)
client.loop_start()

while True:
    publish_value(client, "cpu_temp", f"{read_cpu_temp():.1f}")
    publish_value(client, "uptime", f"{read_uptime():.0f}")
    publish_led_state(client)
    time.sleep(PERIOD)