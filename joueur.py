import threading
import socket
import game
import sys

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
    def __init__(self, id) :
        self.id = id
        self.tour = False
        self.hand = []  # liste des cartes en main, les cartes sont des objets de la classe Carte
        self.known_hand = []
        self.message_queues_in = {} # Dictionnaire contenant les Message queue pour les messages entrants entre les joueurs
        self.message_queues_out = {} # Dictionnaire contenant les Message queue pour les messages sortants entre les joueurs
    
    def play_card(self, indice_card_to_play, game_socket) :
        """Envoie au serveur la carte à jouer"""
        card_to_play = self.hand[indice_card_to_play]
        message = "PLAY " + " ".join(map(str, (card_to_play.numero, card_to_play.couleur)))
        game_socket.sendall(message.encode())
        del self.known_hand[indice_card_to_play]
        del self.hand[indice_card_to_play]
        return self.draw_card(game_socket)
        
    
    def draw_card(self, game_socket) :
        """Récupère une carte de la pioche"""
        data = game_socket.recv(1024).decode().split()        
        new_card = game.Carte(data[1], data[2])
        self.hand.append(new_card)
        self.known_hand.append((False, False))
        resultat = data[0]
        if resultat != "CARD" :
            return resultat

    def draw_first_hand(self, game_socket) :
        """Récupère les 5 premières cartes de la pioche"""
        for _ in range(5) :
            self.draw_card(game_socket)

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
    
    def is_couleur_carte_known(self, indice) :
        """Renvoie la couleur de la carte si elle est connue, sinon renvoie "" """
        if self.known_hand[indice][1] :
            return self.hand[indice].couleur
        else :
            return ""
    
    def show_hand(self) :
        """Affiche la main du joueur"""
        for i in range(5) :
            self.print_en_couleur("┌───────┐ ", self.is_couleur_carte_known(i))
        print()       
            
        for i in range(5) :
            self.print_en_couleur("|       | ", self.is_couleur_carte_known(i))
        print()
        
        for i in range(5) :
            valeur_carte = "?"
            if self.known_hand[i][0] :
                valeur_carte = self.hand[i].numero
            self.print_en_couleur(f"|   {valeur_carte}   | ", self.is_couleur_carte_known(i))
        print()
        
        for i in range(5) :
            self.print_en_couleur("|       | ", self.is_couleur_carte_known(i))
        print()
        
        for i in range(5) :
            self.print_en_couleur("└───────┘ ", self.is_couleur_carte_known(i))
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
    
    def run(self, tas, tokens, clear_func) :
        """Fonction principale du joueur"""
        # Création de la socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as game_socket :
            # Connexion au serveur
            game_socket.connect(("localhost", 6669))
            self.draw_first_hand(game_socket)
            while True :
                if self.tour :
                    clear_func()
                    print("Joueur", self.id, "à ton tour !")
                    print(f"Il vous reste acctuellement {tokens.vies.value} vies et {tokens.hint.value} hints disponibles.")
                    print("Voici le tas :")
                    self.show_tas(tas)
                    print("Tes cartes :")
                    self.show_hand()

                    choix = " "
                    while choix not in ["1", "2"] :
                        print("C'est à toi de jouer !")
                        print("1 - Jouer une carte")
                        print("2 - Donner un hint")
                        choix = input("Entrez votre choix : ")
                        if choix == "1" :
                            indice_carte_a_jouer = int(input("Quelle carte veux-tu jouer ? (de 1 à 5)"))                            
                            resultat = self.play_card(indice_carte_a_jouer - 1, game_socket)
                            if resultat == "WRIGHT" :
                                print("Bonne carte, bien joué !")
                            elif resultat == "WRONG" :
                                print("Mauvaise carte, tu t'es trompé, noob !")
                                tokens.vies -= 1
                            print("Au tour du joueur suivant !")
                            self.tour = False

                        elif choix == "2" :
                            print("Entrez le numéro du joueur à qui donner le hint")
                            numero_joueur = int(input())
                            print("Entrez le type de hint (color ou number)")
                            type_hint = input()
                            if type_hint == "color" :
                                print("Entrez la couleur du hint (rouge, vert, bleu, jaune ou violet)")
                                valeur_hint = input()
                                hint = " ".join(map(str, (type_hint, valeur_hint)))
                                self.give_hint(hint, numero_joueur)
                            elif type_hint == "number" :
                                print("Entrez le numéro du hint (de 1 à 5)")
                                valeur_hint = int(input())
                                hint = " ".join(map(str, (type_hint, valeur_hint)))
                                self.give_hint(hint, numero_joueur)
                        else :
                            print("Choix invalide")
                    


        
if __name__ == "__main__" :
    pass
