import sys
import json
from pathlib import Path

# Setup path so we can import src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.core.parsing.french_medical_parser import FrenchDrugNoticeParser, MedicalTextCleaner

# Hardcode a fake, messy OCR string simulating a French drug notice
MOCK_OCR_TEXT = """
N O T I C E : I N F O R M A T I ON S  P O U R  L ' U T I L I S A T E U R

DOLIPRANE 1000 mg, comprimé sécable
Paracétamol

Veuillez lire attentivement cette notice avant de prendre ce médica-
ment car elle contient des informations importantes pour vous.
Vous devez toujours prendre ce médicament en suivant scrupuleusement
les informations fournies dans cette notice.

http://www.ansm.sante.fr ou jean.dupont@email.com

1. QU'EST-CE QUE DOLIPRANE 1000 mg, comprimé sécable ET DANS QUELS CAS EST-IL UTILISE ?
Ce médicament est un antalgique et un antipyrétique.
Il est indiqué en cas de douleur et/ou fièvre telles que maux de tête, 
états grippaux, douleurs dentaires, courbatures, règles douloureuses.
§%&*^*&&( ignore this OCR noise >>>>>

2. QUELLES SONT LES INFORMATIONS A CONNAITRE AVANT DE PRENDRE DOLIPRANE 1000 mg, comprimé sécable ?
Contre-indications:
Ne prenez jamais DOLIPRANE 1000 mg, comprimé sécable dans les cas suivants:
- allergie connue au paracétamol ou aux autres constituants,
- maladie grave du foie.

Faites attention avec ce médicament:
En cas de surdosage ou de prise par erreur d'une dose trop élevée, consultez immédiatement votre médecin.

Grossesse et allaitement :
L'utilisation de ce médicament est possible pendant la grossesse et l'allaitement si 
besoin, à la dose efficace la plus faible possible.

3. COMMENT PRENDRE DOLIPRANE 1000 mg, comprimé sécable ?
Posologie
Réservé à l'adulte et à l'enfant à partir de 50 kg (environ 15 ans).
La posologie habituelle est de 1 demi à 1 comprimé à 1000 mg par prise, à 
renouveler en cas de besoin au bout de 6 à 8 heures.

4. QUELS SONT LES EFFETS INDESIRABLES EVENTUELS ?
Comme tous les médicaments, ce médicament peut provoquer des effets 
indésirables, mais ils ne surviennent pas systématiquement chez tout le monde.
Rarement: éruption cutanée, rougeur de la peau ou réaction allergique.

5. COMMENT CONSERVER DOLIPRANE 1000 mg, comprimé sécable ?
Tenir ce médicament hors de la vue et de la portée des enfants.
Pas de précautions particulières de conservation. Ne jetez aucun 
médicament au tout-à-l'égout.

6. CONTENU DE L'EMBALLAGE ET AUTRES INFORMATIONS
Ce que contient DOLIPRANE 1000 mg
La substance active est: Paracétamol ... 1000 mg
"""

def main():
    print("=======================================")
    print("1) RAW (MESSY) OCR TEXT:")
    print("=======================================")
    print(MOCK_OCR_TEXT[:400] + "...\n(truncated for brevity)\n")

    print("\n=======================================")
    print("2) RUNNING CLEANER:")
    print("=======================================")
    clean_text = MedicalTextCleaner.clean(MOCK_OCR_TEXT)
    # Notice how "médica- \n ment" gets joined to "médicament"
    # and links/emails disappear
    print(clean_text[:400] + "...\n(truncated for brevity)\n")

    print("\n=======================================")
    print("3) PARSING THE TEXT INTO STRUCTURED JSON:")
    print("=======================================")
    parser = FrenchDrugNoticeParser()
    parsed_data = parser.parse(MOCK_OCR_TEXT)

    # Output to JSON format to simulate an API response
    result_dict = parsed_data.to_dict()
    # Let's remove the raw clean text from output just to show fields clearly
    del result_dict['texte_brut_nettoye'] 

    print(json.dumps(result_dict, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
