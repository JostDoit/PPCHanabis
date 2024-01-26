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
    def __init__(self, id, nb_joueurs) :
        self.id = id
        self.tour = False
        self.nb_joueurs = nb_joueurs
        self.hand = {}  # liste des cartes en main, les cartes sont des objets de la classe Carte
        self.known_hand = {}
        self.message_queues_in = {} # Dictionnaire contenant les Message queue pour les messages entrants entre les joueurs
        self.message_queues_out = {} # Dictionnaire contenant les Message queue pour les messages sortants entre les joueurs
    
    def play_card(self, indice_card_to_play, game_socket) :
        """Envoie au serveur la carte à jouer"""
        card_to_play = self.hand[indice_card_to_play]
        message = "PLAY " + " ".join(map(str, (card_to_play.numero, card_to_play.couleur)))
        game_socket.sendall(message.encode())
        del self.known_hand[self.id][indice_card_to_play]
        del self.hand[self.id][indice_card_to_play]
        return self.draw_card(game_socket)
        
    
    def draw_card(self, game_socket) :
        """Récupère une carte de la pioche"""
        data = game_socket.recv(1024).decode().split()
        new_card = game.Carte(data[1], data[2])
        self.hand[self.id].append(new_card)
        self.known_hand[self.id].append((False, False))
        resultat = data[0]
        if resultat != "CARD" :
            return resultat

    def draw_first_hand(self, game_socket) :
        """Récupère les 5 premières cartes de la pioche"""
        for _ in range(5) :
            self.draw_card(game_socket)
        
        for i in range(self.nb_joueurs) :
            self.known_hand[i] = []
            for _ in range(5) :
                self.known_hand[i].append((False, False))
            
    
    def get_other_players_hands(self) :
        """Récupère les mains des autres joueurs"""
        for message_queue in self.message_queues_in.values() :
            for _ in range(5) :
                message = message_queue.get().split()
                self.hand[int(message[1])] = game.Carte(message[2], message[3])
    
    def show_my_hand_to_other(self) :
        """Envoie sa main aux autres joueurs"""
        for i in range(self.nb_joueurs) :
            for j in range(5) :
                message = " ".join(map(str, ("HAND", self.id, self.hand[j].couleur, self.hand[j].numero)))
                self.message_queues_out[i].put(message)

    def give_hint(self, hint) :
        """Envoie un hint à un joueur"""
        for message_queue in self.message_queues_out.values() :
            message_queue.put(hint)

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
    
    def run(self, tas, tokens, clear_func, port) :
        """Fonction principale du joueur"""
        # Création de la socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as game_socket :
            # Connexion au serveur
            game_socket.connect(("localhost", port))
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
                    print("Les cartes des autres joueurs :")
                    self.show_other_players_hands()

                    choix = " "
                    while choix not in ["1", "2"] :
                        print("C'est à toi de jouer !")
                        print("1 - Jouer une carte")
                        print("2 - Donner un hint")
                        choix = input("Entrez votre choix : ")
                        if choix == "1" :
                            indice_carte_a_jouer = int(input("Quelle carte veux-tu jouer ? (de 1 à 5) : "))                            
                            resultat = self.play_card(indice_carte_a_jouer - 1, game_socket)
                            print(resultat)
                            if resultat == "WRIGHT" :
                                print("Bonne carte, bien joué !")
                            elif resultat == "WRONG" :
                                print("Mauvaise carte, tu t'es trompé, noob !")
                            print("Au tour du joueur suivant !")
                            self.tour = False

                        elif choix == "2" :
                            numero_joueur = int(input("Entrez le numéro du joueur à qui donner le hint : "))
                            type_hint = input("Entrez le type de hint (color ou number) : ")
                            if type_hint == "color" :                                
                                valeur_hint = input("Entrez la couleur du hint (rouge, vert, bleu, jaune ou violet) : ")
                                hint = " ".join(map(str, ("COLOR", valeur_hint, numero_joueur)))
                                self.give_hint(hint)

                            elif type_hint == "number" :
                                valeur_hint = int(input("Entrez le numéro du hint (de 1 à 5) : "))
                                hint = " ".join(map(str, ("NUMBER", valeur_hint, numero_joueur)))
                                self.give_hint(hint)
                            
                            self.tour = False
                        else :
                            print("Choix invalide")
                    


        
if __name__ == "__main__" :
    pass
