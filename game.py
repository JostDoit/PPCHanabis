import random
from multiprocessing import Process, Manager
import socket
import time

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

def handlerEndGame(nb_joueurs, tas, tokens) :
    while True :
        if sum([list(tas.tas.values())[i] for i in range(nb_joueurs)]) == nb_joueurs*5 :
            break
        elif tokens.vies != 0 : 
            break


def gameProcess(tas, tokens, nb_joueurs) :
    pioche = Pioche(nb_joueurs)

    ProcesshandlerEndGame = Process(target = handlerEndGame, args = (nb_joueurs, tas, tokens))
    Processsocket = Process(target = socketProcess, args = (nb_joueurs, tas, tokens, pioche))

    Processsocket.start()
    ProcesshandlerEndGame.start()

    ProcesshandlerEndGame.join()

def handleMessage(msg, tas, tokens, pioche) : #fonction qui traite le message d'un client et qui retourne le message à retourner, "allgood" s'il n'y a rien à renvoyer
    list_msg = msg.split(" ")
    if list_msg[0] == "PLAY" :
        if int(tas.tas[list_msg[2]]) == int(list_msg[1]) - 1 : #si c'est une carte valide
            tas.tas[list_msg[2]] += 1
            carte = pioche.piocher()
            return "RIGHT " + carte.couleur + " " + str(carte.numero)

        else : #mauvaise carte, on perd un jeton vie
            tokens.vies -= 1
            carte = pioche.piocher()
            return "WRONG " + carte.couleur + " " + str(carte.numero)
    


def client_handler(s, a, tas, tokens, pioche) :
    with s :
        data = s.recv(1024)
        msgfromclient = str(data.decode())
        msgtoclient = handleMessage(msgfromclient, tas, tokens, pioche)
        s.send(msgtoclient.encode())

        while len(data) :
            s.sendall(data)
            data = s.recv(1024)
            msgfromclient = str(data.decode())
            msgtoclient = handleMessage(msgfromclient, tas, tokens, pioche)
            s.send(msgtoclient.encode())

def SendCards(s, n, msg, pioche) :
    for i in range(n) :
        carte = pioche.piocher()
        message = msg + " " + str(carte.numero) + " " + carte.couleur
        s.send(message.encode())
        time.sleep(1)

def socketProcess(nb_joueurs, tas, tokens, pioche) :
    HOST = "localhost"
    PORT = 6668
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket :
        server_socket.bind((HOST, PORT))
        server_socket.listen(nb_joueurs)
        while True :
            client_socket, address = server_socket.accept()
            SendCards(client_socket, 5, "CARD", pioche)
            p = Process(target=client_handler, args=(client_socket, address, tas, tokens, pioche))
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

