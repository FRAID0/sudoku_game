import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties

class MQTTClient:
    def __init__(self, username, password):
        # Create an instance of MQTT client
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        
        # Assign callback functions
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Set username and password
        self.client.username_pw_set(username, password)
        
        # Connect to the MQTT broker
        self.host = "localhost"
        self.port = 4005
        self.keepalive = 60
        self.client_id = ""  # Leave empty for auto-generated ID
        self.client.connect(self.host, self.port, self.keepalive)
        
        # Subscribe to a specific topic
        self.topic = "game/grid"

        try:    
            self.client.subscribe(self.topic)
            print(f"Subscribed to topic '{self.topic}'")
        except Exception as e:
            print(f"Failed to subscribe to topic '{self.topic}': {e}")
        
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
    
    def on_message(self, client, userdata, message):
        """Callback function when a message is received"""
        print(f"Received message on topic '{message.topic}': {str(message.payload.decode())}")
        
    
    @property
    def callback_api_version(self) -> mqtt.CallbackAPIVersion:
        """
        Return the callback API version used for user-callback. See docstring for
        each user-callback (`on_connect`, `on_publish`, ...) for details.

        This property is read-only.
        """
        return self.client.callback_api_version
    
    def disconnect(self):
        """Clean disconnection"""
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    username = "pass"
    password = "passmqtt"
    
    mqtt_client = MQTTClient(username, password)
    try:
        # Keep the script running to receive messages
        while True:
            pass
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, disconnecting...")
        mqtt_client.disconnect()
