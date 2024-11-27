import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
import json
import random

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
        self.topic = "game/start"

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

        if(message.topic == "game/start"):
            print("Grid:", self.set_difficulty("easy"))
            self.publish("game/grid", {"grid": self.set_difficulty("easy")})

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

    def generate_filled_sudoku(self):
        grid = [[0 for _ in range(9)] for _ in range(9)]
        
        def is_valid_move(grid, row, col, num):
            # Vérifier la ligne
            if num in grid[row]:
                return False
            # Vérifier la colonne
            if num in [grid[i][col] for i in range(9)]:
                return False
            # Vérifier le sous-grille 3x3
            box_row, box_col = row // 3 * 3, col // 3 * 3
            for i in range(box_row, box_row + 3):
                for j in range(box_col, box_col + 3):
                    if grid[i][j] == num:
                        return False
            return True

        def fill_grid():
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        random_nums = random.sample(range(1, 10), 9)  # Mélange des nombres 1-9
                        for num in random_nums:
                            if is_valid_move(grid, row, col, num):
                                grid[row][col] = num
                                if fill_grid():
                                    return True
                                grid[row][col] = 0  # Annuler si non valide
                        return False  # Revenir en arrière
            return True
        fill_grid()
        return grid
    def generate_sudoku_with_holes(self,filled_grid, holes):
        grid = [row[:] for row in filled_grid]  # Copy the filled grid
        count = holes
        while count > 0:
            row = random.randint(0, 8)
            col = random.randint(0, 8)
            if grid[row][col] != 0:  # Only remove if the cell is not empty
                grid[row][col] = 0
                count -= 1
        return grid

    def set_difficulty(self,level):
        global shared_grid, time_limit, difficulty_chosen, difficulty, base_points
        difficulty = level
        difficulty_chosen = True

        # Générer la grille solution complète du Sudoku
        filled_grid = self.generate_filled_sudoku()
        print("Solution of the Sudoku:")
        for row in filled_grid:
            print(row)

        # Ajuster les paramètres en fonction du niveau de difficulté choisi
        if level == 'easy':
            holes = 40
            time_limit = 30 * 1000  # 30 secondes
            base_points = 1
        elif level == 'medium':
            holes = 30
            time_limit = 20 * 1000  # 20 secondes
            base_points = 1.5
        else:  # 'hard'
            holes = 20
            time_limit = 10 * 1000  # 10 secondes
            base_points = 2

        # Désactiver les boutons de difficulté après la sélection
        # easy_button.config(state="disabled")
        # medium_button.config(state="disabled")
        # hard_button.config(state="disabled")


        # Générer la grille avec les trous correspondant au niveau de difficulté
        shared_grid = self.generate_sudoku_with_holes(filled_grid, holes)

        return shared_grid
        
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
