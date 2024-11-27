import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import json
import paho.mqtt.client as mqtt
import time  # Importer la bibliothèque pour gérer le temps

# MQTT Setup
BROKER = "localhost"
PORT = 4005
TOPIC_G = "game/grid"
TOPIC_S = "game/start"
client = mqtt.Client()

# Sudoku Grid Size
GRID_SIZE = 9
CELL_SIZE = 50
MARGIN = 20
game_grid = [[None for _ in range(9)] for _ in range(9)]  # Grille vide 9x9
difficulty_chosen = False  # Variable globale pour vérifier si la difficulté a été sélectionnée
difficulty = None  # Initialise à None, sera défini dans la fonction `set_difficulty`
difficulty_chosen = False  # Pour indiquer si un niveau de difficulté a été choisi
base_points = 1 
minus_punkt = 1
player_id = 0

POINTS = {
    'easy': 1,
    'medium': 1.5,
    'hard': 2
}


# Définition des seuils de bonus par niveau
BONUS_THRESHOLDS = {
    'easy': [(10, 1), (20, 0.5)],
    'medium': [(7, 1), (15, 0.5)],
    'hard': [(5, 1), (8, 0.5)]
}

# Initial game settings
player_scores = [0, 0]  # Initial scores for two players
current_player = 0  # Current player
timer = 0  # Initial timer
time_limit = 0  # Time limit in milliseconds
shared_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # Initial empty grid


color_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
timer_running = False  # Timer state

# Callback called when the MQTT client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker with result code {rc}")
    client.subscribe(TOPIC_G)
    print(f"Subscribed to topic: {TOPIC_G}")

def on_message(client, userdata, msg):
    global shared_grid, current_player, player_scores, color_grid, difficulty, difficulty_chosen, time_limit, base_points
    try:
        data = json.loads(msg.payload.decode())

        # Synchroniser la grille, les scores, et les paramètres
        shared_grid = data["grid"]
        print(f"Player {current_player + 1} received grid: {shared_grid}")

        current_player = data["current_player"]
        player_scores = data["player_scores"]
        color_grid = data.get("color_grid", [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)])

        # Synchroniser la difficulté et l'état de la difficulté choisie
        difficulty = data.get("difficulty")
        difficulty_chosen = data.get("difficulty_chosen", False)
        
        # Synchroniser time_limit et base_points si présents dans les données
        time_limit = data.get("time_limit", time_limit)
        base_points = data.get("base_points", base_points)

        print(f"Received message: {data}")
        
        # Mettre à jour l'interface utilisateur
        draw_grid(shared_grid)
        update_score_display()

        # Désactiver les boutons de difficulté si la difficulté a été choisie
        if difficulty_chosen:
            easy_button.config(state="disabled")
            medium_button.config(state="disabled")
            hard_button.config(state="disabled")
        
        # Verrouiller ou déverrouiller la grille en fonction du joueur en cours
        if current_player == player_id:  # Assurez-vous que player_id est défini pour chaque joueur
            lock_grid(False)  # Déverrouille pour le joueur en cours
            start_timer()      # Démarre le minuteur si ce n'est pas déjà en cours
        else:
            lock_grid(True)   # Verrouille pour l'autre joueur
            reset_timer()     # Réinitialise le minuteur sans démarrer le décompte

    except Exception as e:
        print(f"Error in sync: {e}")




# Send the current state of the game via MQTT
def send_sync():
    global shared_grid, current_player, player_scores, color_grid, difficulty, time_limit, base_points, difficulty_chosen
    data = {
        "grid": shared_grid,
        "current_player": current_player,
        "player_scores": player_scores,
        "color_grid": color_grid,
        "difficulty": difficulty,
        "time_limit": time_limit,
        "base_points": base_points,
        "difficulty_chosen": difficulty_chosen  # Envoie également l'état de la difficulté
    }
    print(f"Sending sync: {data}")
    client.publish(TOPIC, json.dumps(data))
    print(f"Data published to topic: {TOPIC}")




# Configure the MQTT client and connect
def setup_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    print("MQTT client setup complete, loop started.")

# Function to check if a move is valid
def is_valid_move(grid, row, col, num):
    for x in range(GRID_SIZE):
        if grid[row][x] == num or grid[x][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if grid[start_row + i][start_col + j] == num:
                return False
    return True

# Function to process clicks on the Sudoku grid

def grid_click(event):
    global current_player, start_time  # Ajouter une variable pour mesurer le temps

    x, y = event.x, event.y
    
    # Vérification que l'événement est dans les limites de la grille
    if MARGIN < x < MARGIN + GRID_SIZE * CELL_SIZE and MARGIN < y < MARGIN + GRID_SIZE * CELL_SIZE:
        row = (y - MARGIN) // CELL_SIZE
        col = (x - MARGIN) // CELL_SIZE
        
        # Vérifier si la difficulté a été choisie
        if not difficulty_chosen:
            messagebox.showwarning("Erreur", "Veuillez d'abord choisir un niveau de difficulté.")
            return

        # Vérifier si c'est le tour du joueur actuel
        if current_player != player_id:
            messagebox.showwarning("Tour du joueur", "Ce n'est pas votre tour de jouer.")
            return

        # Si la case est vide (valeur 0)
        if shared_grid[row][col] == 0:
            # Enregistrer le temps de début pour calculer le temps pris pour entrer un nombre
            start_time = time.time()
            
            # Changement de la couleur en bleu clair pour indiquer la sélection
            canvas.create_rectangle(
                MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE,
                MARGIN + (col + 1) * CELL_SIZE, MARGIN + (row + 1) * CELL_SIZE,
                fill="lightblue", outline="black"
            )
            
            # Demander à l'utilisateur d'entrer un chiffre
            number = simpledialog.askinteger("Entrer un nombre", "Entrez un nombre (1-9)")

            # Vérifier si le nombre est valide
            if number and 1 <= number <= 9:
                if is_valid_move(shared_grid, row, col, number):
                    # Calculer le temps pris pour entrer le chiffre
                    time_taken = time.time() - start_time
                    
                    # Si le mouvement est valide, remplir la case et la colorer en vert
                    shared_grid[row][col] = number
                    color_grid[row][col] = "lightgreen"
                    canvas.create_rectangle(
                        MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE,
                        MARGIN + (col + 1) * CELL_SIZE, MARGIN + (row + 1) * CELL_SIZE,
                        fill="lightgreen", outline="black"
                    )
                    canvas.create_text(
                        MARGIN + col * CELL_SIZE + CELL_SIZE // 2,
                        MARGIN + row * CELL_SIZE + CELL_SIZE // 2,
                        text=str(number), font=("Arial", 18)
                    )
                    
                    # Calcul des points avec bonus
                    points_earned = calculate_points(difficulty, time_taken)
                    player_scores[current_player] += points_earned
                    update_score_display()
                    reset_timer()
                    send_sync()
                else:
                    color_grid[row][col] = "red"
                    # Si le mouvement est invalide, colorer la case en rouge
                    canvas.create_rectangle(
                        MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE,
                        MARGIN + (col + 1) * CELL_SIZE, MARGIN + (row + 1) * CELL_SIZE,
                        fill="red", outline="black"
                    )
                    print(f"Mouvement invalide par le joueur {current_player + 1}.")
                    # Soustraction de points pour un mauvais mouvement
                    points_earned = calculate_points(difficulty, 0, correct_move=False)
                    player_scores[current_player] -= points_earned  # Soustraction des points
                    update_score_display()
                    send_sync()
                    switch_player()
            else:
                print("Entrée invalide. Veuillez entrer un nombre entre 1 et 9.")

        # Vérifier s'il reste des cases vides
        if any(0 in row for row in shared_grid):
            print(f"Joueur {current_player + 1}, c'est encore à vous de jouer !")
        else:
            print(f"Joueur {current_player + 1} gagne !")

    # Vérification si la partie est terminée
    winner = is_game_over()
    if winner is not None:
        if winner == 1:
            messagebox.showinfo("Fin du jeu", "Le joueur 1 gagne !")
        elif winner == 2:
            messagebox.showinfo("Fin du jeu", "Le joueur 2 gagne !")
        else:
            messagebox.showinfo("Fin du jeu", "C'est un match nul !")
        end_game()  # Arrêter le jeu



# Function to generate a filled Sudoku
def generate_filled_sudoku():
    grid = [[0 for _ in range(9)] for _ in range(9)]
    
    def fill_grid():
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    random_nums = random.sample(range(1, 10), 9)  # Shuffle numbers 1-9
                    for num in random_nums:
                        if is_valid_move(grid, row, col, num):
                            grid[row][col] = num
                            if fill_grid():
                                return True
                            grid[row][col] = 0  # Reset if not valid
                    return False  # Backtrack
        return True
    
    fill_grid()
    return grid

# Function to generate a Sudoku with holes
def generate_sudoku_with_holes(filled_grid, holes):
    grid = [row[:] for row in filled_grid]  # Copy the filled grid
    count = holes
    while count > 0:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if grid[row][col] != 0:  # Only remove if the cell is not empty
            grid[row][col] = 0
            count -= 1
    return grid

# Function to draw the Sudoku grid
def draw_grid(grid):
    canvas.delete("all")  # Clear previous drawings
    
    # Draw lines for cells
    for i in range(GRID_SIZE + 1):
        line_thickness = 3 if i % 3 == 0 else 1  # Thick lines for block divisions
        canvas.create_line(MARGIN, MARGIN + i * CELL_SIZE, MARGIN + GRID_SIZE * CELL_SIZE, MARGIN + i * CELL_SIZE, width=line_thickness)
        canvas.create_line(MARGIN + i * CELL_SIZE, MARGIN, MARGIN + i * CELL_SIZE, MARGIN + GRID_SIZE * CELL_SIZE, width=line_thickness)

    # Draw numbers and background colors
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # Default color is white
            color = color_grid[row][col] if color_grid[row][col] else "white"
            
            # Draw the background rectangle with the selected color
            canvas.create_rectangle(
                MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE,
                MARGIN + (col + 1) * CELL_SIZE, MARGIN + (row + 1) * CELL_SIZE,
                fill=color, outline="black"
            )
            
            # Draw the pre-filled numbers (if the cell is not empty)
            if grid[row][col] != 0:
                canvas.create_text(
                    MARGIN + col * CELL_SIZE + CELL_SIZE // 2,
                    MARGIN + row * CELL_SIZE + CELL_SIZE // 2,
                    text=str(grid[row][col]), font=("Arial", 18)
                )


def set_difficulty(level):
    global shared_grid, time_limit, difficulty_chosen, difficulty, base_points
    difficulty = level
    difficulty_chosen = True

    # Générer la grille solution complète du Sudoku
    filled_grid = generate_filled_sudoku()
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
    easy_button.config(state="disabled")
    medium_button.config(state="disabled")
    hard_button.config(state="disabled")


    # Générer la grille avec les trous correspondant au niveau de difficulté
    shared_grid = generate_sudoku_with_holes(filled_grid, holes)

    # Dessiner la grille et démarrer le minuteur
    draw_grid(shared_grid)
    start_timer()
    # Envoyer immédiatement les paramètres de difficulté (incluant base_points)
    send_sync()  # Envoi des données immédiatement après le réglage de la difficulté

import time



def calculate_points(difficulty, time_taken, correct_move=True):
    """
    Calcule les points pour un chiffre correct ou incorrect en fonction de la difficulté
    et du temps pris pour entrer le chiffre.
    
    Args:
        difficulty (str): Le niveau de difficulté ('easy', 'medium', 'hard')
        time_taken (float): Le temps en secondes pris pour entrer le chiffre.
        correct_move (bool): Indique si le chiffre entré est correct (True) ou incorrect (False).
    
    Returns:
        float: Le nombre total de points attribués pour ce chiffre (correct ou incorrect)
    """
    base_points = POINTS[difficulty]
    penalty_points = 1  # Pénalité fixe pour une mauvaise réponse
    bonus = 0

    # Appliquer les bonus en fonction du temps pris et du niveau de difficulté
    for threshold, bonus_points in BONUS_THRESHOLDS[difficulty]:
        if time_taken < threshold:
            bonus = bonus_points
            break  # Sortir après le premier bonus applicable

    # Si le chiffre est incorrect, soustraire uniquement la pénalité fixe
    if not correct_move:
        return max(base_points - penalty_points, 0)  # Applique une pénalité fixe sans multiplier par difficulté

    return max(base_points + bonus, 0)  # Retourne au moins 0 points, pas de score négatif


# Fonction appelée quand le joueur entre un chiffre correct
def update_score(difficulty, start_time, player_index):
    # Calcul du temps écoulé depuis l'entrée
    time_taken = (time.time() - start_time) * 1000  # Convertir en millisecondes
    
    # Calcul des points pour cette entrée
    points_earned = calculate_points(difficulty, time_taken / 1000)  # Convertir en secondes pour la fonction

    # Ajouter les points au score du joueur
    player_scores[player_index] += points_earned

    # Mettre à jour l'affichage des scores
    update_score_display()


def clear_grid():
    global game_grid
    for row in game_grid:
        for case in row:
            if case:  # Si la case est un widget d'entrée, on le réinitialise
                case.delete(0, 'end')  # Effacer le contenu de la case
    print("Grid cleared.")

# Fonction pour alterner le joueur actuel
def switch_player():
    global current_player, timer_running
    timer_running = False  # Arrête le minuteur avant de changer de joueur
    current_player = 1 - current_player  # Alterne entre 0 et 1
    print(f"Current Player: Player {current_player + 1}")  # Affiche le joueur actuel

    # Envoyer la synchronisation avec le nouveau joueur actuel
    send_sync()
    
    # Redémarrer le minuteur uniquement pour le nouveau joueur
    if current_player == player_id:
        start_timer()  # Démarrer le minuteur si c'est notre tour

    # Verrouiller ou déverrouiller la grille en fonction du joueur actuel
    if current_player != player_id:
        lock_grid(True)   # Verrouille si ce n'est pas notre tour
    else:
        lock_grid(False)  # Déverrouille si c'est notre tour
    

# Fonction pour mettre la grille en mode lecture seule (empêcher les clics)
def lock_grid(lock):
    if lock:
        # Empêcher l'interaction avec les cellules
        canvas.unbind("<Button-1>")  # Désactive les clics sur la grille
    else:
        # Réactiver les clics pour permettre au joueur actif d'interagir
        canvas.bind("<Button-1>", grid_click)  # Réactive le clic sur la grille





# Function to update the score display
def update_score_display():
    score_label.config(text=f"Scores: Player 1: {player_scores[0]}, Player 2: {player_scores[1]}")

def start_timer():
    global timer_running, timer
    timer_running = True  # Indiquer que le minuteur est en cours
    timer = time_limit
    update_timer_display()  # Met à jour l'affichage du minuteur
    countdown()

def countdown():
    global timer, timer_running
    if timer > 0 and timer_running:  # Compte à rebours uniquement si le minuteur est en cours
        timer -= 1000  # Décrémente de 1 seconde
        update_timer_display()
        window.after(1000, countdown)  # Appelle countdown toutes les 1000 ms (1 seconde)
    elif timer <= 0 and timer_running:
        timer_running = False  # Stoppe le minuteur pour éviter de réappeler `switch_player`
        print(f"Player {current_player + 1}'s time is up! Switching to the next player.")
        switch_player()  # Passe au joueur suivant quand le temps est écoulé

def reset_timer():
    global timer, timer_running
    timer = time_limit  # Reset to the original time limit
    timer_running = True  # Assurez-vous que le minuteur est activé
    update_timer_display()  # Update the timer display

def update_timer_display():
    timer_label.config(text=f"Time Left: {timer // 1000} seconds")  # Display time in seconds



# Fonction pour redémarrer le jeu
def restart_game():
    global difficulty_chosen, player_scores, current_player, shared_grid, color_grid, difficulty, time_limit, timer, timer_running, base_points
    
    # Réinitialiser l'état de jeu
    difficulty_chosen = False
    player_scores = [0, 0]  # Réinitialiser les scores
    current_player = 0      # Revenir au joueur 1
    difficulty = None
    time_limit = 0
    base_points = 0
    timer = 0               # Réinitialiser le minuteur
    timer_running = False   # Arrêter le minuteur
    
    # Réinitialiser la grille de jeu et les couleurs
    shared_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    color_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Effacer la grille visuelle et mettre à jour l'affichage
    draw_grid(shared_grid)
    update_score_display()
    timer_label.config(text="Time Left: 0 seconds")  # Réinitialiser l'affichage du minuteur
    
    # Réactiver les boutons de difficulté pour une nouvelle sélection
    easy_button.config(state="normal")
    medium_button.config(state="normal")
    hard_button.config(state="normal")
    
    # Envoyer les nouvelles données de synchronisation pour informer les autres joueurs
    send_sync()
    
    print("Game has been restarted. Select a difficulty to start.")


# Function to end the game
def end_game():
    global timer_running
    timer_running = False  # Arrête le minuteur
    lock_grid(True)  # Verrouille la grille pour empêcher toute action
    update_timer_display()  # Met à jour l'affichage du minuteur pour afficher 0

    # Affiche un message avec les scores finaux
    messagebox.showinfo("Game Over", f"Partie terminée!\nScores:\nPlayer 1: {player_scores[0]}\nPlayer 2: {player_scores[1]}")

    # Demander si les joueurs souhaitent relancer la partie
    if messagebox.askyesno("Restart", "Voulez-vous rejouer ?"):
        restart_game()  # Relance la partie si le joueur choisit "Oui"
    else:
        print("Merci d'avoir joué!")  # Affiche un message dans la console

    
def is_game_over():
    if all(0 not in row for row in shared_grid):  # Vérifie si toutes les cases sont remplies
        # Déterminer le gagnant
        if player_scores[0] > player_scores[1]:
            return 1  # Le joueur 1 a gagné
        elif player_scores[1] > player_scores[0]:
            return 2  # Le joueur 2 a gagné
        else:
            return 0  # Match nul (si les scores sont égaux)
    return None  # Le jeu n'est pas terminé

# Configuration of the Tkinter interface
window = tk.Tk()
window.title("Sudoku Game")

# Create Sudoku Canvas
canvas = tk.Canvas(window, width=MARGIN * 2 + GRID_SIZE * CELL_SIZE, height=MARGIN * 2 + GRID_SIZE * CELL_SIZE)
canvas.pack(padx=20)

# Create a frame for buttons and score display
button_frame = tk.Frame(window)
button_frame.pack()

# Difficulty buttons
easy_button = tk.Button(button_frame, text="Easy", command=lambda: set_difficulty('easy'))
easy_button.grid(row=0, column=0)

medium_button = tk.Button(button_frame, text="Medium", command=lambda: set_difficulty('medium'))
medium_button.grid(row=0, column=1)

hard_button = tk.Button(button_frame, text="Hard", command=lambda: set_difficulty('hard'))
hard_button.grid(row=0, column=2)

# Restart button
restart_button = tk.Button(button_frame, text="Restart", command=restart_game)
restart_button.grid(row=0, column=3)

# End Game button
end_game_button = tk.Button(button_frame, text="End Game", command=end_game)
end_game_button.grid(row=0, column=4)




# Initial game settings
player_scores = [0, 0]  # Initial scores for two players
current_player = 0  # Current player
timer = 0  # Initial timer
time_limit = 0  # Time limit in milliseconds
shared_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # Initial empty grid
timer_running = False  # Timer state

score_label = tk.Label(window, text="Scores: Player 1: 0, Player 2: 0")
score_label.pack()

timer_label = tk.Label(window, text="Time Left: 0 seconds")
timer_label.pack()

# Bind mouse click event to the grid
canvas.bind("<Button-1>", grid_click)


setup_mqtt()
window.mainloop()


window = tk.Tk()
window.title("Sudoku Game")

canvas = tk.Canvas(window, width=MARGIN * 2 + GRID_SIZE * CELL_SIZE, height=MARGIN * 2 + GRID_SIZE * CELL_SIZE)
canvas.pack(padx=20)

