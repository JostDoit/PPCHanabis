import random
from multiprocessing import Process, Manager
import socket
import time
import signal
import os

couleurs = ["rouge", "vert", "bleu", "jaune", "violet"]


class Carte :
    def __init__(self, numero, couleur) :
        self.numero = numero
        self.couleur = couleur

class Tokens :
    def __init__(self, nb_joueurs, manager) :
        self.vies = manager.Value('i', 3)
        self.hint = manager.Value('i', nb_joueurs + 3)
        
class Pioche :
    def __init__(self, nb_joueurs) :
        self.pioche = []
        self.creer_pioche(nb_joueurs)

    def creer_pioche(self, nb_joueurs) :
        for i in range (nb_joueurs) :
            for j in range (5) :
                if j == 0 :
                    self.pioche += [Carte(j+1, couleurs[i]) for k in range(3)]
                elif j == 4 :
                    self.pioche.append(Carte(j+1, couleurs[i]))
                else :
                    self.pioche += [Carte(j+1, couleurs[i]) for k in range(2)]
        random.shuffle(self.pioche)

    def piocher(self) :
        if len(self.pioche) == 0 :
            print("la pioche est vide")
            return False
        return self.pioche.pop()

class Tas :
    def __init__(self, nb_joueurs, manager) :
        self.tas = manager.dict({couleurs[i] : 0 for i in range(nb_joueurs)})
    
    def ajouter_tas (self, carte) :
        self.tas[carte.couleur] = carte

def handler(sig, process, frame):
    if sig == signal.SIGUSR1:
        os.kill(process.pid, signal.SIGKILL)
        print("Game is over. Exiting all processes.")

def handlerEndGame(nb_joueurs, tas, tokens) :
    while True :
        if sum([list(tas.tas.values())[i] for i in range(nb_joueurs)]) == nb_joueurs*5 :
            os.kill(os.getpid(), signal.SIGUSR1) #ici on arrete tous les processus
        elif tokens.vies != 0 :
            os.kill(os.getpid(), signal.SIGUSR1) #ici aussi


def gameProcess(tas, tokens, nb_joueurs, port) :
    pioche = Pioche(nb_joueurs)

    ProcesshandlerEndGame = Process(target = handlerEndGame, args = (nb_joueurs, tas, tokens))
    Processsocket = Process(target = socketProcess, args = (nb_joueurs, tas, tokens, pioche, port))

    Processsocket.start()
    ProcesshandlerEndGame.start()

    ProcesshandlerEndGame.join()

def handleMessage(s, msg, tas, tokens, pioche) : #fonction qui traite le message d'un client et qui retourne le message à retourner, "allgood" s'il n'y a rien à renvoyer
    list_msg = msg.split(" ")
    if list_msg[0] == "PLAY" :
        if int(tas.tas[list_msg[2]]) == int(list_msg[1]) - 1 : #si c'est une carte valide
            tas.tas[list_msg[2]] += 1
            SendCards(s, 1, "RIGHT", pioche)

        else : #mauvaise carte, on perd un jeton vie
            tokens.vies.value -= 1
            SendCards(s, 1, "WRONG", pioche)

def client_handler(s, tas, tokens, pioche) :  #lorsqu'un client se connecte, cette fonction s'occupera de lui de manière cool
    with s :
        data = s.recv(1024)
        while len(data) :
            msgfromclient = str(data.decode())
            handleMessage(s, msgfromclient, tas, tokens, pioche)
            data = s.recv(1024)

def SendCards(s, n, msg, pioche) :  #envoie n cartes sous forme de message socket à un joueur
    for _ in range(n) :
        carte = pioche.piocher()
        message = msg + " " + str(carte.numero) + " " + carte.couleur
        s.send(message.encode())
        time.sleep(0.1)

def socketProcess(nb_joueurs, tas, tokens, pioche, port) :  # process appelé lorsqu'on initialise une connexion avec un joueur
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket :
        server_socket.bind(("localhost", port))
        server_socket.listen(nb_joueurs)
        while True :
            client_socket, address = server_socket.accept()
            SendCards(client_socket, 5, "CARD", pioche)
            p = Process(target=client_handler, args=(client_socket, tas, tokens, pioche))
            p.start()


if __name__ == "__main__" :
    with Manager() as manager :
        tas = Tas(3, manager)
        tokens = Tokens(3, manager)
        pioche = Pioche(3)
        gameProcess(tas, tokens, 3)
        print(tas.tas)
        print(tokens.vies)
        print(tokens.hint)

