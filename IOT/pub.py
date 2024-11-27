import paho.mqtt.client as mqtt
import threading
import sys

# Informations de connexion
broker = "localhost"
port = 1883
username = "iot"
password = "iot"
topic = "sudoku/game_sync"

# Fonction qui sera appelée à la réception d'un message
def on_message(client, userdata, message):
    print(f"\nMessage reçu : {message.payload.decode()}")

# Fonction pour publier des messages
def publish_messages():
    client = mqtt.Client()
    client.username_pw_set(username, password)  # Authentification
    client.connect(broker, port)  # Connexion au broker
    client.loop_start()  # Démarre la boucle d'attente pour les messages

    while True:
        try:
            message = input("Entrez un message à publier (ou 'exit' pour quitter) : ")
            if message.lower() == "exit":
                break
            client.publish(topic, message)  # Publication du message
            print(f"Message publié : {message}")
        except EOFError:
            break  # Sortie propre en cas d'EOFError

    client.loop_stop()  # Arrête la boucle d'attente
    client.disconnect()  # Déconnexion

# Création du client MQTT pour la réception
client_sub = mqtt.Client()
client_sub.username_pw_set(username, password)  # Authentification
client_sub.on_message = on_message  # Assignation de la fonction de rappel

client_sub.connect(broker, port)  # Connexion au broker
client_sub.subscribe(topic)  # Abonnement au topic
client_sub.loop_start()  # Démarre la boucle d'attente

# Lancer la fonction de publication dans un thread séparé
thread = threading.Thread(target=publish_messages)
thread.start()

# Boucle principale pour recevoir des messages
try:
    while True:
        pass  # Reste dans cette boucle pour continuer à recevoir des messages
except KeyboardInterrupt:
    print("\nArrêt de l'application...")

# Arrêt des boucles et déconnexion
client_sub.loop_stop()  # Arrête la boucle d'attente
client_sub.disconnect()  # Déconnexion
thread.join()  # Attendre que le thread de publication se termine
