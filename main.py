import os
import sys
import joueur
import game_objects
from multiprocessing import Process, Manager, Queue
import threading
import signal

def clear() :
    # Permet de nettoyer la console au lancement du jeu et entre chaque tour (windows et linux)
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

def handler(sig, frame) :
    if sig == signal.SIGUSR1 or sig == signal.SIGINT:
        exit_flag.set()
        try:
            os.kill(game.pid, signal.SIGUSR1)
        except:
            pass
        try:
            handlerendgame.terminate()
        except:
            pass

def handlerEndGame(nb_joueurs, tas, tokens) :
    while True :
        if (sum([list(tas.tas.values())[i] for i in range(nb_joueurs)]) == nb_joueurs*5) or (tokens.vies.value == 0) :
            os.kill(os.getppid(), signal.SIGUSR1)
            break
    

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("required index argument missing, terminating.", file=sys.stderr)
        sys.exit(1)
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"bad index argument: {sys.argv[1]}, terminating.", file=sys.stderr)
        sys.exit(2)
    exit_flag = threading.Event()
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGINT, handler)
    printTitle()
    
    with Manager() as manager:        

        # Demande du nombre de joueurs
        nb_joueurs = 0
        while nb_joueurs < 2 or nb_joueurs > 5 :
            try :
                nb_joueurs = int(input("Entrez le nombre de joueurs (entre 2 à 5) : "))
            except ValueError :
                nb_joueurs = 0
                print("Veuillez entrer un nombre valide")
        
        # Création du bon nombre d'objets joueurs
        joueurs = []
        for i in range(nb_joueurs):
            joueurs.append(joueur.Joueur(i, nb_joueurs))
        joueurs[0].tour = True

        # Initialisation des objets partagés de la partie
        tas = game_objects.Tas(nb_joueurs, manager)
        tokens = game_objects.Tokens(nb_joueurs, manager)
        
        # Création des queues
        for i in range(nb_joueurs):
            for j in range(nb_joueurs):
                if i != j:
                    q = Queue()
                    joueurs[i].message_queues_out[j] = q
                    joueurs[j].message_queues_in[i] = q
                    

        # Création du processus de jeu
        game = Process(target = game_objects.gameProcess, args = (tas, tokens, nb_joueurs, port))
        

        # Création des threads joueurs
        threads = []        
        for player in joueurs:
            threads.append(threading.Thread(target = player.run, args = (tas, tokens, clear, port, exit_flag)))
        
        # Lancement du processus de jeu et des threads joueurs
        game.start()
        for t in threads :
            t.start()
        
        handlerendgame = Process(target = handlerEndGame, args = (nb_joueurs, tas, tokens))
        handlerendgame.start()
        
        # Attente de la fin du processus de jeu et des threads joueurs
        handlerendgame.join()
        
        for t in threads:
            t.join()
        
        game.join()