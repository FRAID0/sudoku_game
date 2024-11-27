import paho.mqtt.client as mqtt
import json

# Configuration du broker
BROKER = "localhost"  # Remplacez par l'adresse de votre broker
PORT = 1883
TOPIC = "sudoku/game_sync"

# Fonction qui sera appelée lorsque le client reçoit un message
def on_message(client, userdata, msg):
    # Décoder le message JSON
    data = json.loads(msg.payload.decode())
    print(f"Received message: {data}")

# Fonction pour configurer le client MQTT
def setup_mqtt():
    client = mqtt.Client()
    client.on_message = on_message  # Définir la fonction de rappel pour les messages
    client.connect(BROKER, PORT, 60)  # Connexion au broker
    client.subscribe(TOPIC)  # S'abonner au topic
    client.loop_forever()  # Boucle infinie pour traiter les messages

if __name__ == "__main__":
    setup_mqtt()  # Lancer la configuration du client MQTT
