import threading
import socket

class Joueur :
    """Classe représentant un joueur de la partie"""
    def __init__(self) :
        self.id = 0
        self.name = ""
        self.tour = False                
        self.hand = []  # liste des cartes en main, les cartes sont des objets de la classe Carte
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_queues_in = {} # Dictionnaire contenant les Message queue pour les messages entrants entre les joueurs
        self.message_queues_out = {} # Dictionnaire contenant les Message queue pour les messages sortants entre les joueurs
    
    def connect_to_game(self, ip, port, methode) :
        """Se connecte à la partie"""
        with self.socket as joueur_socket :
            # Connection au serveur
            joueur_socket.connect((ip, port))
            
    
    def play_card(self, card_to_play, game_socket) :
        """Envoie au serveur la carte à jouer"""
        message = "PLAY " + " ".join(map(str, card_to_play))
        game_socket.sendall(message.encode())
    
    def draw_card(self, game_socket) :
        """Récupère une carte de la pioche"""
        data = game_socket.recv(1024).decode()
        

    def hint(self, hint, player_to_hint) :
        pass
    
    def get_action(self) :
        """Thread qui attend une action du joueur"""
        
        pass

    def get_ohter_player_real_hand(self, player) :
        pass

    def get_other_player_known_hand(self, player) :
        pass

    def get_suits_in_construction(self) :
        pass

    