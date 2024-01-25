import os
import sys
import joueur
import game
from multiprocessing import Process, Manager, Queue

def clear() :
    os.system('cls' if os.name == 'nt' else 'clear')

def printTitle() :
    clear()
    print("""
    ██╗  ██╗ █████╗ ███╗   ██╗ █████╗ ██████╗ ██╗███████╗
    ██║  ██║██╔══██╗████╗  ██║██╔══██╗██╔══██╗██║██╔════╝
    ███████║███████║██╔██╗ ██║███████║██████╔╝██║███████╗
    ██╔══██║██╔══██║██║╚██╗██║██╔══██║██╔══██╗██║╚════██║
    ██║  ██║██║  ██║██║ ╚████║██║  ██║██████╔╝██║███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝ ╚═╝╚══════╝
    """)

def main():
    printTitle()
    with Manager() as manager:
        # Initialisation des objets de la partie
        tas = game.Tas(manager)
        tokens = game.Tokens(manager)

        # Création des joueurs
        nb_joueurs = 0
        while nb_joueurs < 2 or nb_joueurs > 5 :
            try :
                nb_joueurs = int(input("Entrez le nombre de joueurs (entre 2 à 5) : "))
            except ValueError :
                nb_joueurs = 0
        
        joueurs = []
        for i in range(nb_joueurs):
            joueurs.append(joueur.Joueur(i))
        joueurs[0].tour = True

        # Création des queues
        for player in joueurs:
            for other_joueur in joueurs:
                if player.id != other_joueur.id:
                    player.message_queues_in[other_joueur.id] = Queue()
                    player.message_queues_out[other_joueur.id] = Queue()

        # Création des processus
        processes = []
        processes.append(Process(target = game.gameProcess, args = (tas, tokens)))
        processes = [Process(target = joueurs[i].run, args = (tas, tokens, clear)) for i in range(nb_joueurs)]
        

        # Lancement des processus
        for p in processes:
            p.start()
        
        # Attente de la fin des processus
        for p in processes:
            p.join()

if __name__ == "__main__":
    main()