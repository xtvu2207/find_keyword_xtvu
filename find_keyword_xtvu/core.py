import os
import logging
import importlib
import subprocess
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from io import BytesIO
import re

max_threads = os.cpu_count() - 3
os.environ['NUMEXPR_MAX_THREADS'] = str(max_threads)

def install_and_import(package, import_name=None):
    try:
        if import_name is None:
            importlib.import_module(package)
        else:
            importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
    finally:
        if import_name is None:
            return importlib.import_module(package)
        else:
            return importlib.import_module(import_name)

json = install_and_import('json')
pdfplumber = install_and_import('pdfplumber')
pd = install_and_import('pandas')
spacy = install_and_import('spacy')
pytesseract = install_and_import('pytesseract')
PIL = install_and_import('Pillow', 'PIL')
openpyxl = install_and_import('openpyxl')
pdf2image = install_and_import('pdf2image')
pandoc = install_and_import('pandoc')
pypandoc = install_and_import('pypandoc')
reportlab = install_and_import('reportlab')

from docx import Document
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
Event = threading.Event
Image = PIL.Image

def init_nlp(prefixe_langue):
    if prefixe_langue == "multi":
        model_name = "xx_sent_ud_sm"
        try:
            nlp = spacy.load(model_name)
            return nlp
        except OSError:
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", model_name], check=True)
                nlp = spacy.load(model_name)
                return nlp
            except Exception as e:
                raise RuntimeError(f"Impossible de charger le modèle multilingue '{model_name}'.")
    elif prefixe_langue == "en":
        variantes_modele = [
            f"{prefixe_langue}_core_web_lg",
            f"{prefixe_langue}_core_web_md",
            f"{prefixe_langue}_core_web_sm"
        ]
    else:
        variantes_modele = [
            f"{prefixe_langue}_core_news_lg",
            f"{prefixe_langue}_core_news_md",
            f"{prefixe_langue}_core_news_sm"
        ]

    for nom_modele in variantes_modele:
        try:
            nlp = spacy.load(nom_modele)
            return nlp
        except OSError:
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", nom_modele], check=True)
                nlp = spacy.load(nom_modele)
                return nlp
            except Exception as e:
                continue

    fallback_model = "xx_sent_ud_sm"
    try:
        nlp = spacy.load(fallback_model)
        return nlp
    except OSError:
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", fallback_model], check=True)
            nlp = spacy.load(fallback_model)
            return nlp
        except Exception as e:
            raise RuntimeError(f"Impossible de charger un modèle de langue pour '{prefixe_langue}' et le modèle de secours '{fallback_model}'.")

def extraire_phrases(texte, mot_clé, nb_phrases_avant, nb_phrases_apres, nlp):
    doc = nlp(texte)
    phrases_avec_contexte = []
    phrases = list(doc.sents)
    for i, sent in enumerate(phrases):
        if mot_clé.lower() in sent.text.lower():
            start = max(0, i - nb_phrases_avant)
            end = min(len(phrases), i + nb_phrases_apres + 1)
            phrases_contexte = [s.text for s in phrases[start:end]]
            phrases_avec_contexte.append(" ".join(phrases_contexte))
    return phrases_avec_contexte

def compter_mots(phrase):
    return len(phrase.split())

def effectuer_ocr(image, pytesseract):
    return pytesseract.image_to_string(image, lang='fra')

def extraire_blocs_texte(page):
    blocs = []
    if page.extract_text():
        for bloc in page.extract_words():
            blocs.append({
                'x0': bloc['x0'],
                'top': bloc['top'],
                'x1': bloc['x1'],
                'bottom': bloc['bottom'],
                'text': bloc['text']
            })
    return blocs

def extraire_ocr_des_images(page, bbox, pytesseract):
    try:
        image_page = page.to_image(resolution=300).original
        width, height = image_page.size
        x0, y0, x1, y1 = bbox
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(x1, width), min(y1, height)
        image_recadree = image_page.crop((x0, y0, x1, y1))
        return effectuer_ocr(image_recadree, pytesseract)
    except Exception as e:
        if str(e) != "tile cannot extend outside image":
            logging.error(f"Erreur lors de l'extraction OCR de l'image: {str(e)}")
        return ""

def traiter_page(page, id_dossier, fichier, num_page, keywords, nb_phrases_avant, nb_phrases_apres, nlp, pytesseract):
    data = []
    pages_problematiques = []
    logging.info(f"Traitement de la page {num_page} du fichier {fichier} dans le dossier {id_dossier}")
    try:
        blocs_texte = extraire_blocs_texte(page)
        for img in page.images:
            x0, y0, x1, y1 = img["x0"], img["top"], img["x1"], img["bottom"]
            texte_ocr = extraire_ocr_des_images(page, (x0, y0, x1, y1), pytesseract)
            if texte_ocr:
                blocs_texte.append({
                    'x0': x0,
                    'top': y0,
                    'x1': x1,
                    'bottom': y1,
                    'text': texte_ocr
                })
        blocs_texte.sort(key=lambda x: (x['top'], x['x0']))
        texte_complet = " ".join([bloc['text'] for bloc in blocs_texte])
        if texte_complet:
            for mot_clé in keywords:
                phrases = extraire_phrases(texte_complet, mot_clé, nb_phrases_avant, nb_phrases_apres, nlp)
                for phrase in phrases:
                    data.append({
                        'Dossier_PDF': id_dossier,
                        'Document_PDF': fichier,
                        'Num_Page': num_page,
                        'Mots_Clés_Trouvés': mot_clé,
                        'Longueur_Phrase_Conteint_Mots_Clés': compter_mots(phrase),
                        'Info': phrase
                    })
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la page {num_page} du fichier {fichier}: {str(e)}")
        pages_problematiques.append(num_page)
    return data, pages_problematiques

def convertir_en_docx_in_memory(doc_path, pypandoc):
    try:
        temp_docx_path = doc_path.rsplit('.', 1)[0] + '_temp.docx'
        pypandoc.convert_file(doc_path, 'docx', outputfile=temp_docx_path)
        with open(temp_docx_path, 'rb') as f:
            docx_buffer = BytesIO(f.read())
        os.remove(temp_docx_path)
        return docx_buffer
    except Exception as e:
        logging.error(f"Erreur lors de la conversion de {doc_path} en DOCX en mémoire: {str(e)}")
        return None

def convertir_docx_en_pdf_en_memoire(docx_path):
    try:
        doc = Document(docx_path)
        pdf_buffer = BytesIO()
        pdf = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        for para in doc.paragraphs:
            text = para.text
            style = styles['Normal']
            p = Paragraph(text, style)
            elements.append(p)
            elements.append(Spacer(1, 0.2 * inch)) 
        pdf.build(elements)
        pdf_buffer.seek(0)  
        return pdf_buffer.read()
    except Exception as e:
        logging.error(f"Erreur lors de la conversion en PDF en mémoire: {str(e)}")
        return None

def traiter_fichier_pdf(args, timeout, keywords, nb_phrases_avant, nb_phrases_apres,nlp):
    chemin_pdf, id_dossier, fichier = args

    pytesseract = install_and_import('pytesseract')
    pypandoc = install_and_import('pypandoc')

    logging.info(f"Traitement du fichier {fichier} dans le dossier {id_dossier}")
    data = []
    pages_problematiques = []
    try:
        if chemin_pdf.endswith(('.rtf','.odt')):
            docx_buffer = convertir_en_docx_in_memory(chemin_pdf, pypandoc)
            if docx_buffer is None:
                raise Exception(f"Erreur lors de la conversion du fichier {fichier} en DOCX")
            pdf_bytes = convertir_docx_en_pdf_en_memoire(docx_buffer)
            if pdf_bytes is None:
                raise Exception(f"Erreur lors de la conversion du fichier DOCX en mémoire")
        elif chemin_pdf.endswith('.docx'):
            pdf_bytes = convertir_docx_en_pdf_en_memoire(chemin_pdf)
            if pdf_bytes is None:
                raise Exception(f"Erreur lors de la conversion du fichier DOCX {chemin_pdf}")
        else:
            with open(chemin_pdf, "rb") as f:
                pdf_bytes = f.read()

        images = convert_from_bytes(pdf_bytes)
        for num_page, image in enumerate(images, start=1):
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                page = pdf.pages[num_page - 1]
                with ThreadPoolExecutor(max_workers=1) as page_executor:
                    future = page_executor.submit(traiter_page, page, id_dossier, fichier, num_page, keywords, nb_phrases_avant, nb_phrases_apres, nlp, pytesseract)
                    try:
                        page_data, problematic_pages = future.result(timeout=timeout)
                        data.extend(page_data)
                        pages_problematiques.extend(problematic_pages)
                    except Exception as e:
                        logging.error(f"Timeout ou erreur lors du traitement de la page {num_page} du fichier {fichier}: {str(e)}")
                        pages_problematiques.append(num_page)
    except Exception as e:
        logging.error(f"Erreur à l'ouverture du fichier {chemin_pdf}: {str(e)}")
        return None, {'Dossier_PDF': id_dossier, 'Document_PDF': fichier, 'Issue': str(e)}
    
    if pages_problematiques:
        issue_description = f'Délai dépassé ou erreur sur les pages {", ".join(map(str, pages_problematiques))}'
        return data, {'Dossier_PDF': id_dossier, 'Document_PDF': fichier, 'Issue': issue_description}
    
    data.sort(key=lambda x: x['Num_Page'])
    return data, None

def nettoyer_donnees(dataframe, nlp):
    def clean_cell(cell):
        if isinstance(cell, str):
            doc = nlp(cell)
            cleaned_tokens = []
            for token in doc:
                if token.is_alpha or token.is_digit or token.ent_type_:
                    cleaned_tokens.append(token.text)
            return " ".join(cleaned_tokens).strip()
        return cell

    for col in dataframe.columns:
        if dataframe[col].dtype == 'object':
            dataframe.loc[:, col] = dataframe[col].apply(clean_cell)

    return dataframe


def generer_tables_contingence(data):
    df_data = pd.DataFrame(data)
    tables_contingence = {}
    for id_dossier, group in df_data.groupby('Dossier_PDF'):
        table = group.pivot_table(
            index='Document_PDF',
            columns='Mots_Clés_Trouvés',
            values='Longueur_Phrase_Conteint_Mots_Clés',
            aggfunc='count',
            fill_value=0
        )
        tables_contingence[id_dossier] = table
    return tables_contingence

def enregistrer_tables_contingence(tables_contingence, output_path,freque_document_keyword_table_name):
    if not freque_document_keyword_table_name:
        logging.warning("Aucun nom de table de contingence document par keyword fourni, le nom de cette table a été défini par défaut à 'freque_document_keyword'")
        freque_document_keyword_table_name = "freque_document_keyword"
    excel_path = os.path.join(output_path, f"{freque_document_keyword_table_name}.xlsx")
    with pd.ExcelWriter(excel_path) as writer:
        for id_dossier, table in tables_contingence.items():
            table.to_excel(writer, sheet_name=id_dossier[:31])
    logging.info(f"Les tables de contingence ont été enregistrées dans {excel_path}")

def find_keyword_xtvu(
    prefixe_langue = 'fr',
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=None,
    taille=20,
    timeout=200,
    result_keyword_table_name = "",
    freque_document_keyword_table_name="",
    tesseract_cmd="/usr/local/bin/tesseract",
    input_path="/path/to/input",
    output_path="/path/to/output"
):
    if not keywords:
        raise ValueError("La liste des mots-clés (KEYWORDS) ne peut pas être vide. Veuillez fournir une liste valide.")
    if not output_path or not os.path.isdir(output_path):
        raise ValueError("Le chemin du répertoire de sortie (output_path) est invalide ou non défini.")
    if not input_path or not os.path.isdir(input_path):
        raise ValueError("Le chemin du répertoire d'entrée (input_path) est invalide ou non défini.")
    if not tesseract_cmd:
        raise ValueError("Le chemin vers Tesseract (TESSERACT_CMD) doit être défini.")

    # Configuration du nombre de threads et des variables globales
    max_threads = os.cpu_count() - threads_rest
    os.environ['NUMEXPR_MAX_THREADS'] = str(max_threads)
    file_size_limit = taille * 1024 * 1024

    nlp = init_nlp(prefixe_langue)

    # Exécution principale
    data = []
    heavy_or_slow_files = []
    start_time = time.time()
    pdf_files = []

    for racine, dossiers, fichiers in os.walk(input_path):
        for fichier in fichiers:
            chemin_complet = os.path.join(racine, fichier)
            id_dossier = os.path.basename(racine)
            taille_fichier = os.path.getsize(chemin_complet)

            if fichier.endswith(('.docx', '.odt', '.pdf', '.rtf')):
                chemin_pdf = chemin_complet
            else:
                logging.warning(f"Fichier ignoré car non supporté: {fichier}")
                heavy_or_slow_files.append({
                    'Dossier_PDF': id_dossier,
                    'Document_PDF': fichier,
                    'Issue': f"Le fichier est en format {os.path.splitext(fichier)[1]}, veuillez convertir en .docx / .odt / .pdf / .rtf"
                })
                continue

            if taille_fichier > file_size_limit:
                logging.warning(f"Fichier ignoré car trop volumineux: {fichier}")
                heavy_or_slow_files.append({
                    'Dossier_PDF': id_dossier,
                    'Document_PDF': fichier,
                    'Issue': f'Fichier supérieur à {taille} MB'
                })
                continue
            
            pdf_files.append((chemin_pdf, id_dossier, fichier))
    
    with ProcessPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(traiter_fichier_pdf, pdf_file, timeout, keywords, nb_phrases_avant, nb_phrases_apres, nlp): pdf_file for pdf_file in pdf_files}
        for future in as_completed(futures):
            pdf_file = futures[future]
            try:
                file_data, issue = future.result()
                if file_data:
                    data.extend(file_data)
                if issue:
                    heavy_or_slow_files.append(issue)
            except Exception as e:
                chemin_pdf, id_dossier, fichier = pdf_file
                logging.error(f"Erreur lors du traitement du fichier {fichier}: {str(e)}")
                heavy_or_slow_files.append({'Dossier_PDF': id_dossier, 'Document_PDF': fichier, 'Issue': str(e)})

    data.sort(key=lambda x: (x['Document_PDF'], x['Num_Page']))

    resultat_path = output_path or os.path.join(os.path.expanduser("~"), "Desktop", "resultat")
    os.makedirs(resultat_path, exist_ok=True)

    if data:
        tables_contingence = generer_tables_contingence(data)
        enregistrer_tables_contingence(tables_contingence, resultat_path, freque_document_keyword_table_name)
    else:
        logging.error("Il n'y a aucun document contenant les mots-clés ! Veuillez vérifier vos mots-clés =)")
        sys.exit(1)

    df = pd.DataFrame(data, columns=['Dossier_PDF', 'Document_PDF', 'Num_Page', 'Mots_Clés_Trouvés', 'Longueur_Phrase_Conteint_Mots_Clés', 'Info'])
    df = nettoyer_donnees(df, nlp)
    df_heavy_or_slow = pd.DataFrame(heavy_or_slow_files, columns=['Dossier_PDF', 'Document_PDF', 'Issue'])

    df_heavy_or_slow = df_heavy_or_slow.drop_duplicates()
    
    if not result_keyword_table_name:
        logging.warning("Aucun nom de table de résultat fourni, le nom de cette table a été défini par défaut à 'res'")
        result_keyword_table_name = "res"

    df_path = os.path.join(resultat_path, f"{result_keyword_table_name}.xlsx")
    heavy_or_slow_df_path = os.path.join(resultat_path, "heavy_or_slow_df.xlsx")
    df.to_excel(df_path, index=False)
    df_heavy_or_slow.to_excel(heavy_or_slow_df_path, index=False)

    logging.info(f"Les résultats ont été enregistrés dans {resultat_path}")
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Le script a pris {elapsed_time:.2f} secondes pour s'exécuter.")
