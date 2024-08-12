# English version
`find_keyword_xtvu` is a Python package that allows searching for keywords in PDF, DOCX, ODT, and RTF files and extracting the sentences containing these keywords.

## Installation

You can install this package via pip:

```bash
pip install find_keyword_xtvu
```

## Directory Structure

The directory organization containing the .py code and documents can be structured as follows:
```
/Parent Folder
│
├── .py                     # The main Python script
│
├── fichiers_entre          # Folder containing subfolders of PDF files
│   ├── files1              # Subfolder containing input .pdf, .docx, .otd, and .rtf files
│   ├── files2          
│   ├── files3          
│   ...
└── resultats               # Folder containing the results
```

## Usage

1. **Place the files in the input directory**:
   - Place the PDF, DOCX, ODT, or RTF files you want to analyze in the `fichiers_entree` folder. By default, you can organize them in a single subfolder (like `files1`) or in multiple subfolders (`files2`, `files3`, etc.) according to your needs.
   
2. **Define the keywords**:
   - Open the `script_principal.py` script and modify the `KEYWORDS` list to include the keywords you want to search for in the files.
   
3. **Run the script**:
   - Run the `.py` script in an IDE like Visual Studio Code.

The `.py` file uses the `find_keyword_xtvu` package and can be organized as follows:

```python
from find_keyword_xtvu import find_keyword_xtvu

find_keyword_xtvu(
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=["recycling", "composting"],
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/input",
    output_path="/path/to/output"
)
```

If you are on Windows, the .py file can be organized as follows to avoid multicore-related errors:
```python
from find_keyword_xtvu import find_keyword_xtvu
if __name__ == "__main__":
    find_keyword_xtvu(
        threads_rest=1,
        nb_phrases_avant=10,
        nb_phrases_apres=10,
        keywords=["recycling", "composting"],
        taille=20,
        timeout=200,
        result_keyword_table_name="",
        freque_document_keyword_table_name="",
        tesseract_cmd="/usr/local/bin/tesseract",
        input_path="/path/to/input",
        output_path="/path/to/output"
    )
```

### Arguments

- `threads_rest`: Number of threads to reserve for other tasks (default: `1`).
- `nb_phrases_avant`: Number of sentences to include before the keyword (default: `10`).
- `nb_phrases_apres`: Number of sentences to include after the keyword (default: `10`).
- `keywords`: List of keywords to search for (default: `["recycling", "composting"]`).
- `taille`: Maximum size of files to process in megabytes (default: `20` MB).
- `timeout`: Maximum time to process a page in seconds (default: `200`).
- `result_keyword_table_name`: Name of the table for keyword results.
- `freque_document_keyword_table_name`: Name of the table for document keyword frequency.
- `tesseract_cmd`: Path to the Tesseract executable (default: `"/usr/local/bin/tesseract"`).
- `input_path`: Path to the folder containing the files to process.
- `output_path`: Path to the folder where results will be saved.


## Contribution

Contributions are welcome! If you want to improve this project or have any questions, feel free to contact me at vuxuantung09134@gmail.com.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

# Version Française

`find_keyword_xtvu` est un package Python permettant de rechercher des mots-clés dans des fichiers PDF, DOCX, ODT et RTF, et d'extraire les phrases contenant ces mots-clés.

## Installation

Vous pouvez installer ce package via pip :

```bash
pip install find_keyword_xtvu
```

## Structure du Répertoire

L'organisation du dossier contenant le code .py et les documents peut être structurée comme suit :
```
/Dossier parent
│
├── .py                     # Le script Python principal
│
├── fichiers_entre          # Dossier contenant les sous-dossiers de fichiers PDF
│   ├── files1              # Sous-dossier contenant les fichiers .pdf, .docx, .otd et .rtf d'entrée
│   ├── files2          
│   ├── files3          
│   ...
└── resultats               # Dossier contenant les résultats
```

## Utilisation

1. **Placez les fichiers dans le répertoire d'entrée** :
   - Mettez les fichiers PDF, DOCX, ODT, ou RTF que vous souhaitez analyser dans le dossier `fichiers_entree`. Par défaut, vous pouvez les organiser dans un seul sous-dossier (comme `files1`) ou dans plusieurs sous-dossiers (`files2`, `files3`, etc.) selon vos besoins.
   
2. **Définissez les mots-clés** :
   - Ouvrez le script `script_principal.py` et modifiez la liste `KEYWORDS` pour inclure les mots-clés que vous souhaitez rechercher dans les fichiers.
   
3. **Exécutez le script** :
   - Exécutez le script `.py` dans un IDE comme Visual Studio Code.

Le fichier `.py` utilise le package `find_keyword_xtvu` et peut être organisé comme suit :

```python
from find_keyword_xtvu import find_keyword_xtvu

find_keyword_xtvu(
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=["recycling", "composting"],
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/input",
    output_path="/path/to/output"
)
```

Si vous êtes sur Windows, le fichier .py peut être organisé comme suit pour éviter les erreurs liées au multicore :
```python
from find_keyword_xtvu import find_keyword_xtvu
if __name__ == "__main__":
    find_keyword_xtvu(
        threads_rest=1,
        nb_phrases_avant=10,
        nb_phrases_apres=10,
        keywords=["recycling", "composting"],
        taille=20,
        timeout=200,
        result_keyword_table_name="",
        freque_document_keyword_table_name="",
        tesseract_cmd="/usr/local/bin/tesseract",
        input_path="/path/to/input",
        output_path="/path/to/output"
    )
```

### Arguments

- `threads_rest` : Nombre de threads à réserver pour d'autres tâches (valeur par défaut : `1`).
- `nb_phrases_avant` : Nombre de phrases à inclure avant le mot-clé (valeur par défaut : `10`).
- `nb_phrases_apres` : Nombre de phrases à inclure après le mot-clé (valeur par défaut : `10`).
- `keywords` : Liste des mots-clés à rechercher (par défaut : `["recycling", "composting"]`).
- `taille` : Taille maximale des fichiers à traiter en mégaoctets (valeur par défaut : `20` MB).
- `timeout` : Durée maximale pour le traitement d'une page en secondes (valeur par défaut : `200`).
- `result_keyword_table_name` : Nom de la table pour les résultats des mots-clés.
- `freque_document_keyword_table_name` : Nom de la table pour la fréquence des mots-clés dans les documents.
- `tesseract_cmd` : Chemin vers l'exécutable Tesseract (valeur par défaut : `"/usr/local/bin/tesseract"`).
- `input_path` : Chemin vers le dossier contenant les fichiers à traiter.
- `output_path` : Chemin vers le dossier où les résultats seront enregistrés.


## Contribution

Les contributions sont les bienvenues ! Si vous souhaitez améliorer ce projet ou avez des questions, n'hésitez pas à me contacter à l'adresse vuxuantung09134@gmail.com.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.