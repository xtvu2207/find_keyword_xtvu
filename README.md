# English version
The `find_keyword_xtvu` Python package facilitates the search for keywords across **PDF, DOCX, ODT, and RTF** files, enabling the extraction of sentences that contain these keywords. It also offers support for **multiple languages** and can run on **multicore CPUs**.

## What's New in Version 5.5.1
**Multilingual Support**: This new version now supports multiple languages by integrating SpaCy's NLP models. You can now search for keywords and extract sentences in languages such as English, French, German, Spanish, and more. The supported models are listed in the [SpaCy documentation](https://spacy.io/usage/models).


## Installation

You can install this package via pip:

```bash
pip install find-keyword-xtvu==<latest_version_on_PyPi>
```

## Directory Structure

The directory organization containing the .py code and documents can be structured as follows:
```
/Parent Folder
│
├── script_principal.py     # The main Python script
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
   - Place the PDF, DOCX, ODT, or RTF files you want to analyze into the subfolders within the `fichiers_entree` directory. By default, you can organize them in a single subfolder (e.g., files1) or in multiple subfolders (files2, files3, etc.), depending on your needs.
   
2. **Define the keywords**:
   - Open the `script_principal.py` script and modify the `KEYWORDS` list to include the keywords you want to search for in the files.
   
3. **Run the script**:
   - Run the `script_principal.py` script in an IDE like Visual Studio Code.

The `script_principal.py` file uses the `find_keyword_xtvu` package and can be organized as follows:

```python
from find_keyword_xtvu import find_keyword_xtvu

find_keyword_xtvu(
    prefixe_langue = 'fr',
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=[""],
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/fichiers_entre",
    output_path="/path/to/resultats"
)
```

If you are on Windows, the `script_principal.py` file can be organized as follows to avoid multicore-related errors:
```python
from find_keyword_xtvu import find_keyword_xtvu
if __name__ == "__main__":
    find_keyword_xtvu(
        prefixe_langue = 'fr',
        threads_rest=1,
        nb_phrases_avant=10,
        nb_phrases_apres=10,
        keywords=[""],
        taille=20,
        timeout=200,
        result_keyword_table_name="",
        freque_document_keyword_table_name="",
        tesseract_cmd="/usr/local/bin/tesseract",
        input_path="/path/to/fichiers_entre",
        output_path="/path/to/resultats"
    )
```

## Arguments
- `prefixe_langue`: Language prefix to specify the language model to use (default value: `'fr'`). To know the supported languages and their prefixes, see the [SpaCy documentation](https://spacy.io/usage/models). If you provide an unsupported prefix, or if you want to use the multilingual model, specify the `multi` argument. In either case, the multilingual model `xx_ent_wiki_sm` will be used. Learn more about this model [here](https://spacy.io/models/xx).
- `threads_rest`: Number of threads to reserve for other tasks (default value: `1`).
- `nb_phrases_avant`: Number of sentences to include before the keyword (default value: `10`).
- `nb_phrases_apres`: Number of sentences to include after the keyword (default value: `10`).
- `keywords`: List of keywords to search for (default: `[""]`).
- `taille`: Maximum file size to process in megabytes (default value: `20` MB).
- `timeout`: Maximum time for processing a page in seconds (default value: `200`).
- `result_keyword_table_name`: Name of the table for keyword results. If this field is empty, a default name for this table will be `res`.
- `freque_document_keyword_table_name`: Name of the table for the results of the contingency tables of keyword frequency in each file folder. If this field is empty, the default name for this table will be `freque_document_keyword`.
- `tesseract_cmd`: Path to the Tesseract executable (default value: `"/usr/local/bin/tesseract"`).
- `input_path`: Path to the folder containing the files to be processed.
- `output_path`: Path to the folder where the results will be saved.

## Outputs

The `find_keyword_xtvu` function will generate the following three Excel workbooks (.xlsx):
1. A file containing the results of the keywords found in the documents, with a name that can be defined by the `result_keyword_table_name` argument in the `find_keyword_xtvu` function.
2. A file containing the contingency tables of keyword frequency in the documents, with a name that can be defined by the `freque_document_keyword_table_name` argument in the `find_keyword_xtvu` function. Each contingency table shows how many times each keyword was found in each document within a specific folder. These tables are saved in different sheets within a single Excel workbook, with each sheet representing a folder.
3. A file listing problematic files, named `heavy_or_slow_df.xlsx`.


## Contribution

Contributions are welcome! If you would like to improve this project or if you have any questions, feel free to contact me at vuxuantung09134@gmail.com (in French, English, or Vietnamese).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

# Version Française

`find_keyword_xtvu` est un package Python permettant de rechercher des mots-clés dans des fichiers PDF, DOCX, ODT et RTF, et d'extraire les phrases contenant ces mots-clés.

## Installation

Vous pouvez installer ce package via pip :

```bash
pip install find-keyword-xtvu==<dernière_version_sur_PyPi>
```

## Structure du Répertoire

L'organisation du dossier contenant le code .py et les documents peut être structurée comme suit :
```
/Dossier parent
│
├── script_principal.py     # Le script Python principal
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
    - Mettez les fichiers PDF, DOCX, ODT, ou RTF que vous souhaitez analyser dans les sous-dossiers du dossier `fichiers_entree`. Par défaut, vous pouvez les organiser dans un seul sous-dossier (par exemple, `files1`) ou dans plusieurs sous-dossiers (`files2`, `files3`, etc.), selon vos besoins.
    
2. **Définissez les mots-clés** :
   - Ouvrez le script `script_principal.py` et modifiez la liste `KEYWORDS` pour inclure les mots-clés que vous souhaitez rechercher dans les fichiers.
   
3. **Exécutez le script** :
   - Exécutez le script `script_principal.py`dans un IDE comme Visual Studio Code.

Le fichier `script_principal.py` utilise le package `find_keyword_xtvu` et peut être organisé comme suit :

```python
from find_keyword_xtvu import find_keyword_xtvu

find_keyword_xtvu(
    prefixe_langue = 'fr',
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=[""],
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/fichiers_entre",
    output_path="/path/to/resultats"
)
```

Si vous êtes sur Windows, le fichier `script_principal.py` peut être organisé comme suit pour éviter les erreurs liées au multicore :
```python
from find_keyword_xtvu import find_keyword_xtvu
if __name__ == "__main__":
    find_keyword_xtvu(
        prefixe_langue = 'fr',
        threads_rest=1,
        nb_phrases_avant=10,
        nb_phrases_apres=10,
        keywords=[""],
        taille=20,
        timeout=200,
        result_keyword_table_name="",
        freque_document_keyword_table_name="",
        tesseract_cmd="/usr/local/bin/tesseract",
        input_path="/path/to/fichiers_entre",
        output_path="/path/to/resultats"
    )
```

## Arguments
- `prefixe_langue` : Préfixe de langue pour spécifier le modèle linguistique à utiliser (valeur par défaut : `'fr'`). Pour connaître les langues supportées et leurs préfixes, consultez la [documentation SpaCy](https://spacy.io/usage/models). Si vous fournissez un préfixe non supporté, ou si vous souhaitez utiliser le modèle multilingue, spécifiez l'argument `multi`. Dans les deux cas, le modèle multilingue `xx_ent_wiki_sm` sera utilisé. En savoir plus sur ce modèle [ici](https://spacy.io/models/xx).
- `threads_rest` : Nombre de threads à réserver pour d'autres tâches (valeur par défaut : `1`).
- `nb_phrases_avant` : Nombre de phrases à inclure avant le mot-clé (valeur par défaut : `10`).
- `nb_phrases_apres` : Nombre de phrases à inclure après le mot-clé (valeur par défaut : `10`).
- `keywords` : Liste des mots-clés à rechercher (par défaut : `[""]`).
- `taille` : Taille maximale des fichiers à traiter en mégaoctets (valeur par défaut : `20` MB).
- `timeout` : Durée maximale pour le traitement d'une page en secondes (valeur par défaut : `200`).
- `result_keyword_table_name` : Nom de la table pour les résultats des mots-clés. Si ce champ est vide, un nom par défaut pour cette table sera `res`.
- `freque_document_keyword_table_name` : Nom de la table pour les résultats des tables de contingence de la fréquence des mots-clés dans chaque dossier de fichiers. Si ce champ est vide, le nom par défaut pour cette table sera `freque_document_keyword`.
- `tesseract_cmd` : Chemin vers l'exécutable Tesseract (valeur par défaut : `"/usr/local/bin/tesseract"`).
- `input_path` : Chemin vers le dossier contenant les fichiers à traiter.
- `output_path` : Chemin vers le dossier où les résultats seront enregistrés.

## Sorties

La fonction `find_keyword_xtvu` va générer trois classeurs Excel (.xlsx) suivants :
1. Un fichier contenant les résultats des mots-clés trouvés dans les documents avec un nom pouvant être défini par l'argument `result_keyword_table_name` dans la fonction `find_keyword_xtvu`.
2. Un fichier contenant les tables de contingence de la fréquence des mots-clés dans les documents avec un nom pouvant être défini par l'argument `freque_document_keyword_table_name` dans la fonction `find_keyword_xtvu`. Chaque table de contingence montre combien de fois chaque mot-clé a été trouvé dans chaque document au sein d'un dossier spécifique. Ces tables sont enregistrées sous différentes feuilles dans un seul classeur Excel, avec chaque feuille représentant un dossier.
3. Un fichier répertoriant les fichiers problématiques, nommé `heavy_or_slow_df.xlsx`.






## Contribution

Les contributions sont les bienvenues ! Si vous souhaitez améliorer ce projet ou si vous avez des questions, n'hésitez pas à me contacter à l'adresse vuxuantung09134@gmail.com (en français, anglais ou vietnamien).

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.