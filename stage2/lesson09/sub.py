import paho.mqtt.client as mqtt
import math

BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "stand/#"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Брокер отказал: {reason_code}")
        return
    print("Подключено к брокеру")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        text = msg.payload.decode("utf-8")
    except UnicodeDecodeError:
        print(f"{msg.topic}: не UTF-8, байты {msg.payload!r}")
        return

    if text == "":
        print(f"{msg.topic}: пусто (значение снято)")
        return

    try:
        value = float(text)
    except ValueError:
        print(f"{msg.topic}: не число: {text!r}")
        return
    
    if not math.isfinite(value):
        print(f"{msg.topic}: не конечное число: {text!r}")
        return
    
    print(f"{msg.topic} = {value}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()
