Bien sûr ! Je vais vous aider à créer les fichiers nécessaires pour votre projet. Voici comment vous pouvez structurer chaque fichier, y compris `README.md` et `LICENSE`.

### **1. Fichier `README.md`**

Ce fichier sert à documenter votre projet, expliquer son utilisation, et fournir des informations utiles pour les utilisateurs. Voici un exemple de contenu pour `README.md` :

```markdown
# find_keyword_xtvu

`find_keyword_xtvu` est un package Python permettant de rechercher des mots-clés dans des fichiers PDF, DOCX, ODT et RTF, et d'extraire les phrases contenant ces mots-clés.

## Installation

Vous pouvez installer ce package via pip :

```bash
pip install find_keyword_xtvu
```

## Utilisation

Voici un exemple de base pour utiliser le package `find_keyword_xtvu` :

```python
from find_keyword_xtvu import find_keyword_xtvu

find_keyword_xtvu(
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=["recycling", "composting"],
    taille=20,
    timeout=200,
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/input",
    output_path="/path/to/output"
)
```

### Arguments

- `threads_rest` : Nombre de threads à réserver pour d'autres tâches (par défaut 1).
- `nb_phrases_avant` : Nombre de phrases à inclure avant le mot-clé (par défaut 10).
- `nb_phrases_apres` : Nombre de phrases à inclure après le mot-clé (par défaut 10).
- `keywords` : Liste des mots-clés à rechercher (par défaut une liste prédéfinie).
- `taille` : Taille maximale des fichiers à traiter en MB (par défaut 20 MB).
- `timeout` : Durée maximale pour le traitement d'une page en secondes (par défaut 200).
- `tesseract_cmd` : Chemin vers l'exécutable Tesseract (par défaut "/usr/local/bin/tesseract").
- `input_path` : Chemin vers le dossier contenant les fichiers à traiter.
- `output_path` : Chemin vers le dossier où les résultats seront enregistrés.

## Contribution

Les contributions sont les bienvenues ! Si vous souhaitez améliorer ce projet, n'hésitez pas à soumettre des pull requests.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.