import multiprocessing

def processus_enfant(queue):
    user_input = input("Entrez quelque chose dans le processus enfant : ")
    queue.put(user_input)

if __name__ == "__main__":
    # Création d'une file d'attente partagée entre le processus parent et le processus enfant
    ma_queue = multiprocessing.Queue()

    # Création d'un processus enfant
    processus = multiprocessing.Process(target=processus_enfant, args=(ma_queue,))

    # Démarrage du processus enfant
    processus.start()

    # Attente que le processus enfant se termine
    processus.join()

    # Récupération des données de la file d'attente
    user_input_from_child = ma_queue.get()

    # Affichage de l'entrée utilisateur du processus enfant
    print(f"Entrée utilisateur du processus enfant : {user_input_from_child}")
