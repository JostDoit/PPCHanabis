class Couleurs:
    RESET = '\033[0m'
    ROUGE = '\033[91m'
    VERT = '\033[92m'
    BLEU = '\033[94m'

def print_en_couleur(texte, couleur):
    print(f"{couleur}{texte}{Couleurs.RESET}")

# Exemples d'utilisation
print_en_couleur("Texte en rouge", Couleurs.ROUGE)
print_en_couleur("Texte en vert", Couleurs.VERT)
print_en_couleur("Texte en bleu", Couleurs.BLEU)
print_en_couleur("Texte en ?", Couleurs.RESET)