import os
import sys
import joueur
import game
from multiprocessing import Process, Manager, Queue
import time
import threading

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

def main(port):
    printTitle()
    with Manager() as manager:

        # Création des joueurs
        nb_joueurs = 0
        while nb_joueurs < 2 or nb_joueurs > 5 :
            try :
                nb_joueurs = int(input("Entrez le nombre de joueurs (entre 2 à 5) : "))
            except ValueError :
                nb_joueurs = 0

        # Initialisation des objets de la partie
        tas = game.Tas(nb_joueurs, manager)
        tokens = game.Tokens(nb_joueurs, manager)
        
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
        processes.append(Process(target = game.gameProcess, args = (tas, tokens, nb_joueurs, port)))
        

        threads = []
        # Création des threads joueurs
        for player in joueurs:
            threads.append(threading.Thread(target = player.run, args = (tas, tokens, clear, nb_joueurs, port)))
        

        # Lancement des processus
        for p in processes:
            p.start()
            time.sleep(1)
        
        # Lancement des threads
        for t in threads:
            t.start()
            time.sleep(1)
        
        # Attente de la fin des processus
        for p in processes:
            p.join()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("required index argument missing, terminating.", file=sys.stderr)
        sys.exit(1)
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"bad index argument: {sys.argv[1]}, terminating.", file=sys.stderr)
        sys.exit(2)

    main(port)