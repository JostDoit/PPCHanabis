import threading
import socket
import game_objects
import sys
import time

class Couleurs :
    """Classe contenant les codes ANSI pour les couleurs"""
    RESET = '\033[0m'
    ROUGE = '\033[91m'
    VERT = '\033[92m'
    BLEU = '\033[94m'
    JAUNE = '\033[93m'
    VIOLET = '\033[95m'

class Joueur :
    """Classe représentant un joueur de la partie"""
    def __init__(self, id, nb_joueurs) :
        self.id = id    # id du joueur
        self.tour = False   # booléen indiquant si c'est le tour du joueur
        self.nb_joueurs = nb_joueurs    # nombre de joueurs dans la partie
        self.hand = {}  # dictionnaire contenant les mains des joueurs, les cles etant l'id d'un joueur et la valeur une liste contenant les cartes (des objets Carte)
        self.known_hand = {}    # dictionnaire contenant les informations que possède chaque joueur sur sa main, les cles etant l'id d'un joueur et la valeur une liste contenant des tuples (bool, bool) indiquant si la couleur et/ou le numero de la carte est connu
        self.message_queues_in = {} # Dictionnaire contenant les Message queue pour les messages entrants entre les joueurs, les cles etant l'id d'un joueur et la valeur une Message queue
        self.message_queues_out = {} # Dictionnaire contenant les Message queue pour les messages sortants entre les joueurs, les cles etant l'id d'un joueur et la valeur une Message queue
        self.color_options = []
        self.running = True
        self.message_queue_in_handlers = []

        self.init_hands()
        self.init_known_hand()
        self.init_color_options()
    
    def init_known_hand(self) :
        """Initialise le dictionnaire known_hand avec des tuples (False, False)"""
        for i in range(self.nb_joueurs) :
            self.known_hand[i] = []
            for _ in range(5) :
                self.known_hand[i].append([False, False])
    
    def init_hands(self) :
        """Initialise le dictionnaire hand avec des listes vides"""
        for i in range(self.nb_joueurs) :
            self.hand[i] = []
            for _ in range(5) :
                self.hand[i].append(game_objects.Carte(0, 0))
    
    def init_color_options(self) :
        """Initialise la liste des couleurs possibles"""
        colors = ["rouge", "vert", "bleu", "jaune", "violet"]
        for i in range(self.nb_joueurs) :
            self.color_options.append(colors[i])
    
    def draw_first_hand(self, game_socket) :
        """Récupère les 5 premières cartes de la pioche"""
        for _ in range(5) :
            self.draw_card(game_socket)
    
    def draw_card(self, game_socket, indice_card_to_play = -1) :
        """Récupère une carte de la pioche"""
        data = game_socket.recv(1024).decode().split()
        new_card = game_objects.Carte(data[1], data[2])
        self.hand[self.id].insert(0, new_card)
        self.known_hand[self.id].insert(0, [False, False])        
        resultat = data[0]
        # Test s'il s'agit d'une carte piochée au début du jeu ou après un PLAY
        if resultat != "CARD" :
            self.show_new_hand_to_other(indice_card_to_play)
            return resultat

    def play_card(self, indice_card_to_play, game_socket) :
        """Envoie au serveur la carte à jouer"""
        card_to_play = self.hand[self.id][indice_card_to_play]
        numero_carte = card_to_play.numero
        couleur_carte = card_to_play.couleur
        message = "PLAY " + " ".join(map(str, (numero_carte, couleur_carte)))
        game_socket.sendall(message.encode())
        del self.known_hand[self.id][indice_card_to_play]
        del self.hand[self.id][indice_card_to_play]
        return self.draw_card(game_socket, indice_card_to_play), numero_carte, couleur_carte
        
    
    def show_my_hand_to_other(self) :
        """Envoie sa main aux autres joueurs"""
        for i in range(self.nb_joueurs) :
            if i != self.id :
                for j in range(5) :
                    message = " ".join(map(str, ("HAND", j, self.hand[self.id][j].numero, self.hand[self.id][j].couleur)))
                    self.message_queues_out[i].put(message)
    
    def show_new_hand_to_other(self, indice_card_to_play) :
        """Préviens l'indice de la carte jouée aux autres joueurs et annonce la carte piochée"""
        for i in range(self.nb_joueurs) :
            if i != self.id :
                message = " ".join(map(str, ("PLAY", indice_card_to_play, self.hand[self.id][0].numero, self.hand[self.id][0].couleur)))
                self.message_queues_out[i].put(message)

    def give_hint(self, type_hint, valeur_hint, numero_joueur) :
        """Envoie un hint à un joueur"""
        type_hint = type_hint.upper()
        if type_hint == "COLOR" :
            hint = " ".join(map(str, (type_hint, valeur_hint, numero_joueur)))
        else :
            hint = " ".join(map(str, (type_hint, valeur_hint, numero_joueur)))
        
        for message_queue in self.message_queues_out.values() :
            message_queue.put(hint)
        self.receive_hint(type_hint, valeur_hint, numero_joueur)
    
    def notify_turn(self, id_joueur) :
        """Préviens un autre joueur que c'est son tour"""
        self.message_queues_out[id_joueur].put("TURN")
    
    def end_turn(self) :
        """Fin du tour du joueur"""
        player_to_notify = (self.id + 1) % self.nb_joueurs
        print(f"Au tour du joueur {player_to_notify} !\n")
        input("Appuyez sur entrée pour lancer le tour du joueur suivant...")            
        self.tour = False
        self.notify_turn(player_to_notify)
    
    def handle_message_queues_in(self) :
        """Crée les handlers pour les messages entrants"""
        for id_joueur, message_queue in self.message_queues_in.items() :
            self.message_queue_in_handlers.append(threading.Thread(target = self.handle_message_queue_in, args = (message_queue, id_joueur)))
        for handler in self.message_queue_in_handlers :
            handler.start()
    
    def handle_message_queue_in(self, message_queue, id_joueur) :
        """Lit les messages entrants"""
        while self.running :
            if message_queue.empty() :
                continue
            else:
                message = message_queue.get().split()
                if message[0] == "HAND" :
                    self.receive_other_player_hand(id_joueur, int(message[1]), message[2], message[3])
                elif message[0] == "PLAY" :
                    self.receive_other_player_card(id_joueur, int(message[1]), message[2], message[3])
                elif message[0] == "TURN" :
                    self.tour = True
                else:
                    self.receive_hint(message[0], message[1], int(message[2]))
    
    def receive_other_player_hand(self, id_joueur, indice_card, valeur_carte, couleur_carte) :
        """Récupère les mains des autres joueurs"""
        self.hand[id_joueur][indice_card] = game_objects.Carte(valeur_carte, couleur_carte)
    
    def receive_other_player_card(self, id_joueur, indice_card, valeur_carte, couleur_carte) :
        """Récupère l'indice de la carte jouée par un autre jouer et les infos de la carte piochée"""
        del self.hand[id_joueur][indice_card]
        del self.known_hand[id_joueur][indice_card]
        self.hand[id_joueur].insert(0, game_objects.Carte(valeur_carte, couleur_carte))
        self.known_hand[id_joueur].insert(0, [False, False])

    def receive_hint(self, type_hint, value_hint, player_who_received_hint) :
        """Reçoit un hint d'un joueur"""
        if type_hint == "COLOR" :
            print(f"Le joueur {player_who_received_hint} a reçu un hint sur la couleur {value_hint}")
            for i in range(5) :
                if self.hand[player_who_received_hint][i].couleur == value_hint :
                    self.known_hand[player_who_received_hint][i][1] = True
        else :
            for i in range(5) :
                if self.hand[player_who_received_hint][i].numero == value_hint :
                    self.known_hand[player_who_received_hint][i][0] = True
    
    def print_en_couleur(self, texte, couleur):
        if couleur == "" :
            couleur = Couleurs.RESET
        elif couleur == "rouge" :
            couleur = Couleurs.ROUGE
        elif couleur == "vert" :
            couleur = Couleurs.VERT
        elif couleur == "bleu" :
            couleur = Couleurs.BLEU
        elif couleur == "jaune" :
            couleur = Couleurs.JAUNE
        elif couleur == "violet" :
            couleur = Couleurs.VIOLET
        print(f"{couleur}{texte}{Couleurs.RESET}", end="")
    
    def is_couleur_carte_known(self, indice, id_player, show_all) :
        """Renvoie la couleur de la carte si elle est connue, sinon renvoie "" """
        if self.known_hand[id_player][indice][1] or show_all:
            return self.hand[id_player][indice].couleur
        else :
            return ""
    
    def show_hand(self, id_player, show_all = False ) :
        """Affiche la main d'un joueur"""
        for i in range(5) :
            self.print_en_couleur("┌───────┐ ", self.is_couleur_carte_known(i, id_player, show_all))
        print()       
            
        for i in range(5) :
            self.print_en_couleur("|       | ", self.is_couleur_carte_known(i, id_player, show_all))
        print()
        
        for i in range(5) :
            valeur_carte = "?"
            if self.known_hand[id_player][i][0] or show_all:
                valeur_carte = self.hand[id_player][i].numero
            self.print_en_couleur(f"|   {valeur_carte}   | ", self.is_couleur_carte_known(i, id_player, show_all))
        print()
        
        for i in range(5) :
            self.print_en_couleur("|       | ", self.is_couleur_carte_known(i, id_player, show_all))
        print()
        
        for i in range(5) :
            self.print_en_couleur("└───────┘ ", self.is_couleur_carte_known(i, id_player, show_all))
        print()
        print()
    
    
    def show_tas(self, tas) :
        """Affiche le tas"""
        for couleur in tas.tas.keys() :
            self.print_en_couleur("┌───────┐ ", couleur)
        print()
        
        for couleur in tas.tas.keys() :
            self.print_en_couleur("|       | ", couleur)
        print()
        
        for couleur in tas.tas.keys() :            
            self.print_en_couleur(f"|   {tas.tas[couleur]}   | ", couleur)
        print()
        
        for couleur in tas.tas.keys() :
            self.print_en_couleur("|       | ", couleur)
        print()
        
        for couleur in tas.tas.keys() :
            self.print_en_couleur("└───────┘ ", couleur)
        print()
        print()
    
    def run(self, tas, tokens, clear_func, port, exit_flag) :
        """Fonction principale du joueur"""
        # Création de la socket du joueur
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as game_socket :
            # Connexion au serveur
            connexion_try = 10
            while connexion_try > 0 :
                try :
                    game_socket.connect(("localhost", port))
                    break
                except ConnectionRefusedError :
                    connexion_try -= 1
                    time.sleep(0.01)
            if connexion_try == 0 :
                print("Connexion au serveur impossible")
                sys.exit(1)

            # Lancement des handlers pour les messages entrants
            self.handle_message_queues_in()
            
            # Piche des premières cartes
            self.draw_first_hand(game_socket)
            
            # Envoie de la main aux autres joueurs
            self.show_my_hand_to_other()

            waiting_to_receive_other_players_hands = True
            while waiting_to_receive_other_players_hands :
                for i in range(self.nb_joueurs) :                    
                    if i != self.id :
                        wait_player = True
                        while wait_player :
                            for j in range(5) :
                                if self.hand[i][j].numero != 0 :
                                    wait_player = False
                                else :
                                    wait_player = True
                        if self.id == 0 :                            
                            print(f"Réception de la main du joueur {i} !")
                waiting_to_receive_other_players_hands = False

            
            # Boucle d'un tour de jeu
            while not exit_flag.is_set() :
                if self.tour :
                    clear_func()
                    print("Joueur", self.id, "à ton tour !\n")
                    print(f"Il vous reste acctuellement {tokens.vies.value} vies et {tokens.hint.value} hints disponibles.\n")
                    print("Voici le tas :")
                    self.show_tas(tas)
                    
                    print("Tes cartes :")
                    self.show_hand(self.id)
                    
                    print("Les cartes des autres joueurs :\n")
                    for i in range(self.nb_joueurs) :
                        if i != self.id :
                            print(f"Cartes du joueur {i} :")
                            self.show_hand(i, True)
                            print("Indices qu'il a sur sa main :")
                            self.show_hand(i)

                    choix = " "
                    while choix not in ["1", "2"] :
                        print("C'est à toi de jouer !")
                        print("1 - Jouer une carte")
                        print("2 - Donner un hint")
                        choix = input("Entrez votre choix : ")
                        
                        if choix == "1" :                
                                indice_carte_a_jouer = 0
                                while indice_carte_a_jouer < 1 or indice_carte_a_jouer > 5 :
                                    try :
                                        indice_carte_a_jouer = int(input("Quelle carte veux-tu jouer ? (de 1 à 5) : "))
                                    except ValueError :
                                        indice_carte_a_jouer = 0
                                        print("Veuillez entrer un nombre valide")                     
                                resultat, valeure, couleure = self.play_card(indice_carte_a_jouer - 1, game_socket)
                                print(f"Vous avez joué la carte {valeure} {couleure}")
                                if resultat == "RIGHT" :
                                    print("\nBien joué ! Vous pouviez jouer cette carte !")
                                    print("Voici à quoi ressemble le tas maintenant :")
                                    self.show_tas(tas)
                                elif resultat == "WRONG" :
                                    print("\nMauvaise carte ! Vous perdez une vie !")
                                
                                self.end_turn()
                            
                        elif choix == "2" :
                            if tokens.hint.value > 0 :
                                numero_joueur = -1
                                type_hint = ""
                                valeur_hint = ""
                                if self.nb_joueurs == 2 :
                                    numero_joueur = (self.id + 1) % 2
                                else :
                                    while (numero_joueur < 0 or numero_joueur >= self.nb_joueurs):
                                        try:
                                            numero_joueur = int(input("Entrez le numéro du joueur à qui donner le hint : "))
                                        except ValueError:
                                            print("Choix invalide")
                                while type_hint not in ["1", "2"] :
                                    print("Entrez le type de hint :")
                                    print("1 - Couleur")
                                    print("2 - Numéro")
                                    type_hint = input("Votre choix :")
                                    if type_hint not in ["1", "2"] :
                                        print("Choix invalide !\n")
                                
                                if type_hint == "1" :
                                    while valeur_hint not in self.color_options :                              
                                        valeur_hint = input(f"Entrez la couleur du hint {self.color_options} : ")
                                
                                elif type_hint == "2  " :
                                    while valeur_hint not in ["1", "2", "3", "4", "5"] :
                                        valeur_hint = input("Entrez le numéro du hint (de 1 à 5) : ")
                                    
                                self.give_hint(type_hint ,valeur_hint, numero_joueur)
                                tokens.hint.value -= 1                        
                                self.end_turn()
                            
                            else: 
                                print("Vous n'avez plus d'indice disponible !")
                                choix = " "
            self.running = False
            for handler in self.message_queue_in_handlers :
                handler.join()
                print(f"Thread handler {handler} joined")
        
if __name__ == "__main__" :
    pass
