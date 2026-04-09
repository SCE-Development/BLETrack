import paho.mqtt.client as mqtt
import json
from dotenv import load_dotenv
import os

load_dotenv() 

# --- Configuration --

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "espresense/devices/+/sce")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        # Clean print for the terminal
        print(f"User: {msg.topic.split(':')[1].split('/')[0]} | Distance: {data['distance']}m")
    except Exception as e:
        print(f"Raw Message: {msg.payload.decode()}")

client = mqtt.Client()
client.on_message = on_message



    

print(f"Connecting to {MQTT_BROKER}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

# This starts the infinite loop to keep the script running
client.loop_forever()