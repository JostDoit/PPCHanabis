import threading
import socket
import game

class Joueur :
    """Classe représentant un joueur de la partie"""
    def __init__(self) :
        self.id = 0
        self.name = ""
        self.tour = False                
        self.hand = []  # liste des cartes en main, les cartes sont des objets de la classe Carte
        self.known_hand = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_queues_in = {} # Dictionnaire contenant les Message queue pour les messages entrants entre les joueurs
        self.message_queues_out = {} # Dictionnaire contenant les Message queue pour les messages sortants entre les joueurs
    
    def play_card(self, card_to_play, game_socket) :
        """Envoie au serveur la carte à jouer"""
        message = "PLAY " + " ".join(map(str, (card_to_play.numero, card_to_play.couleur)))
        game_socket.sendall(message.encode())
        self.hand.remove(card_to_play)
    
    def draw_card(self, game_socket) :
        """Récupère une carte de la pioche"""
        data = game_socket.recv(1024).decode().split()
        new_card = game.Carte(data[0], data[1])
        self.hand.append(new_card)

    def draw_first_hand(self, game_socket) :
        """Récupère les 5 premières cartes de la pioche"""
        for _ in range(5) :
            self.draw_card(game_socket)
            self.known_hand.append((False, False))

    def give_hint(self, hint, player_to_hint) :
        """Envoie un hint à un joueur"""
        self.message_queues_out[player_to_hint].put(hint)

    def receive_hint(self, hint, player_who_hinted) :
        """Reçoit un hint d'un joueur"""
        received_hint = self.message_queues_in[player_who_hinted].get().split()
        if received_hint[0] == "COLOR" :
            for i in range(5) :
                if self.hand[i].couleur == received_hint[1] :
                    self.known_hand[i][0] = True
        else :
            for i in range(5) :
                if self.hand[i].numero == received_hint[1] :
                    self.known_hand[i][1] = True