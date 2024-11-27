import paho.mqtt.client as mqtt
import json
import random

BROKER_HOST = "test.mosquitto.org"
BROKER_PORT = 1883

# Topics
START_GAME_TOPIC = "game/start"
GRID_UPDATE_TOPIC = "game/grid/update"

# Fonction pour vérifier si un nombre peut être placé dans une cellule
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

# Fonction pour générer une grille de Sudoku
def generate_filled_sudoku():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    
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

# Fonction pour retirer des valeurs en fonction de la difficulté
def remove_cells(grid, difficulty):
    num_to_remove = {"easy": 20, "medium": 40, "hard": 55}
    cells_to_remove = num_to_remove.get(difficulty, 20)
    for _ in range(cells_to_remove):
        row, col = random.randint(0, 8), random.randint(0, 8)
        while grid[row][col] == 0:  # Éviter de supprimer une cellule déjà vide
            row, col = random.randint(0, 8), random.randint(0, 8)
        grid[row][col] = 0
    return grid

def on_connect(client, userdata, flags, rc):
    print("Connected to broker.")
    client.subscribe(START_GAME_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        difficulty = data.get("difficulty", "easy")
        print(f"Generating grid for difficulty: {difficulty}")
        
        # Générer une grille complète et retirer des cellules selon la difficulté
        full_grid = generate_filled_sudoku()
        playable_grid = remove_cells(full_grid, difficulty)
        
        # Publier la grille sur le topic GRID_UPDATE_TOPIC
        message = json.dumps({"grid": playable_grid})
        client.publish(GRID_UPDATE_TOPIC, message)
    except Exception as e:
        print(f"Error processing message: {e}")

# Configurer le client MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_forever()
