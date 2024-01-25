import random
from multiprocessing import Process, Manager

NOMBRE_JOUEURS = 3
couleurs = ["rouge", "vert", "bleu", "jaune", "blanc"]


class Carte :
    def __init__(self, numero, couleur) :
        self.numero = numero
        self.couleur = couleur

class Tokens :
    def __init__(self,manager) :
        self.vies = manager.Value('i', 3)
        self.hint = manager.Value('i',NOMBRE_JOUEURS + 3)
        
class Pioche :
    def __init__(self) :
        self.pioche = []
        self.creer_pioche()
    
    def creer_pioche(self) :
        for i in range (NOMBRE_JOUEURS) :
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
    def __init__(self, manager) :
        self.tas = manager.dict({couleurs[i] : None for i in range(NOMBRE_JOUEURS)})
    
    def ajouter_tas (self, carte) :
        self.tas[carte.couleur] = carte

def handlerEndGame(tas, list_tokens):
    while True :
        if sum([list(tas.tas.values())[i] for i in range(NOMBRE_JOUEURS)]) == 5*NOMBRE_JOUEURS :
            None #fin du jeu : le tas est finito pipo
        elif [list_tokens[i].vies for i in range(NOMBRE_JOUEURS)].count(0) != 0 : 
            None #fin du jeu : un des joueurs n'a plus de vies, cest ciao


def gameProcess() :
    with Manager() as manager :
        pioche = Pioche()
        list_tokens = manager.list([Tokens(manager) for i in range(NOMBRE_JOUEURS)])
        tas = Tas(manager)
        ProcesshandlerEndGame = Process(target = handlerEndGame, args = (tas, list_tokens))
        ProcesshandlerEndGame.start()


if __name__ == '__main__' :
    game = Process(target = gameProcess, args = ())
    game.start()
    game.join()
