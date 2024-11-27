import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self):
        # Create an instance of MQTT client
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        
        # Assign callback functions
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Connect to the MQTT broker
        self.host = "localhost"
        self.port = 4005
        
        self.keepalive = 60
        self.client_id = ""  
        self.client.connect(self.host, self.port, self.keepalive)
        
        # Start the message handling loop
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, rc, properties):
        """Callback function when connected to the broker"""
        if rc == 0:
            print("Connected to the MQTT broker")
        else:
            print(f"Connection failed with result code {rc}")
    
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback function when disconnected from the broker"""
        print("Disconnected from the MQTT broker")
    
    def on_publish(self, client, userdata, mid, reason_code, properties):
        """Callback function when a message is successfully published"""
        print("Message published successfully")
    
    @property
    def callback_api_version(self) -> mqtt.CallbackAPIVersion:
        """
        Return the callback API version used for user-callback. See docstring for
        each user-callback (`on_connect`, `on_publish`, ...) for details.

        This property is read-only.
        """
        return self.client.callback_api_version
    
    def publish(self, topic, payload, qos=0, retain=False):
        """Publish a message"""
        json_payload = json.dumps(payload)  # Convert dict to JSON string
        self.client.publish(topic, json_payload, qos, retain)
        print(f"Published message on topic '{topic}': {json_payload}")
    
    def disconnect(self):
        """Clean disconnection"""
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    mqtt_client = MQTTClient()

    mqtt_client.publish("game/start", "start")
    
    mqtt_client.disconnect()
