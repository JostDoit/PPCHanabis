import multiprocessing
import threading
import time
import signal
import os

def worker():
    while not exit_flag.is_set():
        print("Thread working...")
        time.sleep(1)

def signal_handler(signum, frame):
    exit_flag.set()

if __name__ == "__main__":
    exit_flag = threading.Event()
    signal.signal(signal.SIGINT, signal_handler)

    # Créer un processus principal
    main_process = multiprocessing.Process(target=worker)

    # Démarrer le processus principal
    main_process.start()

    try:
        # Attendre la fin du processus principal
        main_process.join()
    except KeyboardInterrupt:
        # Si vous appuyez sur Ctrl+C, cela déclenchera le signal SIGINT
        pass
    finally:
        # Set exit_flag pour demander à tous les threads de s'arrêter
        exit_flag.set()

        # Attendre que tous les threads se terminent
        main_process.join()

    print("Programme terminé.")
