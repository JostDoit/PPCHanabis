NOMBRE_JOUEURS = 3

couleurs = ["rouge", "vert", "bleu", "jaune", "blanc"]

class Carte :
    def __init__(self, numero, couleur) :
        self.numero = numero
        self.couleur = couleur



class Pioche :
    global NOMBRE_JOUEURS
    def __init__(self, NOMBRE_JOUEURS) :
        self.pioche = []
        for i in range (NOMBRE_JOUEURS) :
            for j in range (10) :
                if 