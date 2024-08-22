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
#xlsxwriter = install_and_import('xlsxwriter')

from docx import Document
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
Event = threading.Event
Image = PIL.Image




def init_nlp(language_prefix):
    RED = '\033[91m'
    RESET = '\033[0m'

    if language_prefix == "multi":
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
                logging.error(f"{RED}Unable to load the multilingual model '{model_name}'.{RESET}")
                sys.exit(1)
    elif language_prefix == "en":
        model_variants = [
            f"{language_prefix}_core_web_lg",
            f"{language_prefix}_core_web_md",
            f"{language_prefix}_core_web_sm"
        ]
    else:
        model_variants = [
            f"{language_prefix}_core_news_lg",
            f"{language_prefix}_core_news_md",
            f"{language_prefix}_core_news_sm"
        ]

    for model_name in model_variants:
        try:
            nlp = spacy.load(model_name)
            return nlp
        except OSError:
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", model_name], check=True)
                nlp = spacy.load(model_name)
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
            logging.error(f"{RED}Unable to load a language model for '{language_prefix}' and the fallback model '{fallback_model}'.{RESET}")
            sys.exit(1)


def extraire_phrases(texte, mot_clé, nb_phrases_avant, nb_phrases_apres, nlp, fusion_keyword_before_after):
    doc = nlp(texte)
    phrases_avec_contexte = []
    phrases_deja_incluses = set()
    phrases = list(doc.sents)
    mot_clé_pattern = re.compile(rf'\b{re.escape(mot_clé.lower())}\b')
    
    if fusion_keyword_before_after:
        for i, sent in enumerate(phrases):
            if mot_clé_pattern.search(sent.text.lower()):
                start = max(0, i - nb_phrases_avant)
                end = min(len(phrases), i + nb_phrases_apres + 1)

                phrases_contexte = [phrases[idx].text for idx in range(start, end)]
                extrait_actuel = " ".join(phrases_contexte)
                phrase_cible = sent.text
                if not any(phrase_cible in extrait for extrait in phrases_deja_incluses):
                    phrases_avec_contexte.append(extrait_actuel)
                    phrases_deja_incluses.add(extrait_actuel)

    else:
        for i, sent in enumerate(phrases):
            if mot_clé_pattern.search(sent.text.lower()):
                start = max(0, i - nb_phrases_avant)
                end = min(len(phrases), i + nb_phrases_apres + 1)
                phrases_contexte = [s.text for s in phrases[start:end]]
                phrases_avec_contexte.append(" ".join(phrases_contexte))
    
    return phrases_avec_contexte




def compter_mots(phrase):
    return len(phrase.split())

def effectuer_ocr(image, pytesseract, lang_OCR_tesseract):
    return pytesseract.image_to_string(image, lang=lang_OCR_tesseract)

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



def extraire_ocr_des_images(page, bbox, pytesseract,lang_OCR_tesseract):
    RED = '\033[91m'
    RESET = '\033[0m'

    try:
        image_page = page.to_image(resolution=300).original
        width, height = image_page.size
        x0, y0, x1, y1 = bbox
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(x1, width), min(y1, height)
        image_recadree = image_page.crop((x0, y0, x1, y1))
        return effectuer_ocr(image_recadree, pytesseract, lang_OCR_tesseract)
    except Exception as e:
        if str(e) != "tile cannot extend outside image":
            logging.error(f"{RED}Error during OCR extraction from the image: {str(e)}{RESET}")
        return ""


def traiter_page(page, id_dossier, fichier, num_page, keywords, nb_phrases_avant, nb_phrases_apres, nlp, pytesseract, fusion_keyword_before_after, use_tesseract,lang_OCR_tesseract):
    RED = '\033[91m'
    RESET = '\033[0m'

    data = []
    pages_problematiques = []
    logging.info(f"Processing page {num_page} of file {fichier} in folder {id_dossier}")
    try:
        blocs_texte = extraire_blocs_texte(page)
        
        if use_tesseract:
            for img in page.images:
                x0, y0, x1, y1 = img["x0"], img["top"], img["x1"], img["bottom"]
                texte_ocr = extraire_ocr_des_images(page, (x0, y0, x1, y1), pytesseract,lang_OCR_tesseract)
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
                phrases = extraire_phrases(texte_complet, mot_clé, nb_phrases_avant, nb_phrases_apres, nlp, fusion_keyword_before_after)
                for phrase in phrases:
                    data.append({
                        'PDF_Folder': id_dossier,
                        'PDF_Document': fichier,
                        'Page_Number': num_page,
                        'Keywords_Found': mot_clé,
                        'Length_Of_Extracted_Phrase': compter_mots(phrase),
                        'Info': phrase
                    })
    except Exception as e:
        logging.error(f"{RED}Error processing page {num_page} of file {fichier}: {str(e)}{RESET}")
        pages_problematiques.append(num_page)
    return data, pages_problematiques


def convertir_en_docx_in_memory(doc_path, pypandoc):
    RED = '\033[91m'
    RESET = '\033[0m'

    try:
        temp_docx_path = doc_path.rsplit('.', 1)[0] + '_temp.docx'
        pypandoc.convert_file(doc_path, 'docx', outputfile=temp_docx_path)
        with open(temp_docx_path, 'rb') as f:
            docx_buffer = BytesIO(f.read())
        os.remove(temp_docx_path)
        return docx_buffer
    except Exception as e:
        logging.error(f"{RED}Error converting {doc_path} to DOCX in memory: {str(e)}{RESET}")
        return None


def convertir_docx_en_pdf_en_memoire(docx_path):
    RED = '\033[91m'
    RESET = '\033[0m'

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
        logging.error(f"{RED}Error during PDF conversion in memory: {str(e)}{RESET}")
        return None


def traiter_fichier_pdf(args, timeout, keywords, nb_phrases_avant, nb_phrases_apres, nlp, fusion_keyword_before_after, tesseract_cmd, use_tesseract, poppler_path,lang_OCR_tesseract):
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    chemin_pdf, id_dossier, fichier = args

    if use_tesseract:
        pytesseract = install_and_import('pytesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    else:
        pytesseract = None

    pypandoc = install_and_import('pypandoc')

    logging.info(f"Processing file {fichier} in folder {id_dossier}")
    data = []
    pages_problematiques = []
    try:
        if chemin_pdf.endswith(('.rtf', '.odt')):
            docx_buffer = convertir_en_docx_in_memory(chemin_pdf, pypandoc)
            if docx_buffer is None:
                raise Exception(f"{RED}Error converting file {fichier} to DOCX{RESET}")
            pdf_bytes = convertir_docx_en_pdf_en_memoire(docx_buffer)
            if pdf_bytes is None:
                raise Exception(f"{RED}Error converting DOCX file in memory{RESET}")
        elif chemin_pdf.endswith('.docx'):
            pdf_bytes = convertir_docx_en_pdf_en_memoire(chemin_pdf)
            if pdf_bytes is None:
                raise Exception(f"{RED}Error converting DOCX file {chemin_pdf}{RESET}")
        else:
            with open(chemin_pdf, "rb") as f:
                pdf_bytes = f.read()

        images = convert_from_bytes(pdf_bytes, 500, poppler_path = poppler_path)
        for num_page, image in enumerate(images, start=1):
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                page = pdf.pages[num_page - 1]
                with ThreadPoolExecutor(max_workers=1) as page_executor:
                    future = page_executor.submit(traiter_page, page, id_dossier, fichier, num_page, keywords, nb_phrases_avant, nb_phrases_apres, nlp, pytesseract, fusion_keyword_before_after, use_tesseract,lang_OCR_tesseract)
                    try:
                        page_data, problematic_pages = future.result(timeout=timeout)
                        data.extend(page_data)
                        pages_problematiques.extend(problematic_pages)
                    except Exception as e:
                        logging.error(f"{RED}Timeout or error processing page {num_page} of file {fichier}: {str(e)}{RESET}")
                        pages_problematiques.append(num_page)
    except Exception as e:
        logging.error(f"{RED}Error opening file {chemin_pdf}: {str(e)}{RESET}")
        return None, {'PDF_Folder': id_dossier, 'PDF_Document': fichier, 'Issue': str(e)}
    
    if pages_problematiques:
        issue_description = f'Timeout or error on pages {", ".join(map(str, pages_problematiques))}'
        return data, {'PDF_Folder': id_dossier, 'PDF_Document': fichier, 'Issue': issue_description}
    
    data.sort(key=lambda x: x['Page_Number'])
    return data, None


def nettoyer_donnees(dataframe):
    def clean_cell(cell):
        if isinstance(cell, str):
            cell = re.sub(r'[^\x20-\x7E]', '', cell)
            return cell.strip()
        return cell

    for col in dataframe.columns:
        if dataframe[col].dtype == 'object':
            dataframe[col] = dataframe[col].apply(clean_cell)

    return dataframe

def supprimer_phrases_redondantes(texte, nlp):
    doc = nlp(texte)
    phrases_vues = set()
    texte_sans_redondances = []
    
    for sent in doc.sents:
        phrase = sent.text.strip()
        if phrase not in phrases_vues:
            phrases_vues.add(phrase)
            texte_sans_redondances.append(phrase)
    
    return " ".join(texte_sans_redondances)

def generer_tables_contingence(data, nlp):
    df_data = pd.DataFrame(data)
    tables_contingence = {}
    
    for id_dossier, group in df_data.groupby('PDF_Folder'):
        keyword_counts = {}
        
        for document, doc_group in group.groupby('PDF_Document'):
            combined_info = " ".join(doc_group['Info'].tolist())
            
            combined_info = supprimer_phrases_redondantes(combined_info, nlp)
            
            keyword_counts[document] = {}
            for keyword in doc_group['Keywords_Found'].unique():
                count = len(re.findall(rf'\b{re.escape(keyword)}\b', combined_info, flags=re.IGNORECASE))
                keyword_counts[document][keyword] = count
        
        df_keyword_counts = pd.DataFrame(keyword_counts).T.fillna(0)
        tables_contingence[id_dossier] = df_keyword_counts

    return tables_contingence


def enregistrer_tables_contingence(tables_contingence, output_path, freque_document_keyword_table_name):
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    if not freque_document_keyword_table_name:
        logging.warning(f"{YELLOW}No contingency table name for document by keyword provided, the table name has been set to 'freque_document_keyword' by default{RESET}")
        freque_document_keyword_table_name = "freque_document_keyword"
    
    excel_path = os.path.join(output_path, f"{freque_document_keyword_table_name}.xlsx")
    
    with pd.ExcelWriter(excel_path) as writer:
        for id_dossier, table in tables_contingence.items():
            table.to_excel(writer, sheet_name=id_dossier[:31])
    
    logging.info(f"{GREEN}Contingency tables have been saved in {excel_path}{RESET}")


def find_keyword_xtvu(
    prefixe_langue='fr',
    threads_rest=1,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=None,
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    fusion_keyword_before_after=False,
    tesseract_cmd="",
    use_tesseract=False,
    lang_OCR_tesseract = "fra",  
    input_path="/path/to/input",
    output_path="/path/to/output",
    poppler_path = ""
):
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    tesseract_cmd = tesseract_cmd.replace("\\", "/")
    input_path = input_path.replace("\\", "/")
    output_path = output_path.replace("\\", "/")

    if not keywords:
        logging.error(f"{RED}The keyword list (KEYWORDS) cannot be empty. Please provide a valid list.{RESET}")
        sys.exit(1)
    if not output_path or not os.path.isdir(output_path):
        logging.error(f"{RED}The output directory path (output_path) is invalid or not defined.{RESET}")
        sys.exit(1)
    if not input_path or not os.path.isdir(input_path):
        logging.error(f"{RED}The input directory path (input_path) is invalid or not defined.{RESET}")
        sys.exit(1)
    if use_tesseract and not tesseract_cmd:
        logging.error(f"{RED}You chose to use pytesseract, but you didn't provide a Tesseract path. Please provide a Tesseract path or set use_tesseract to False if you don't want to use pytesseract.{RESET}")
        sys.exit(1)
    if not poppler_path:
        logging.error(f"{RED}The Poppler path (poppler_path) is invalid or not defined. Please ensure that Poppler is installed and the path to the 'bin' directory is correctly set.{RESET}")
        sys.exit(1)

        
    max_threads = os.cpu_count() - threads_rest
    os.environ['NUMEXPR_MAX_THREADS'] = str(max_threads)
    file_size_limit = taille * 1024 * 1024
    nlp = init_nlp(prefixe_langue)

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
                logging.warning(f"{YELLOW}File ignored because unsupported: {fichier}{RESET}")
                heavy_or_slow_files.append({
                    'PDF_Folder': id_dossier,
                    'PDF_Document': fichier,
                    'Issue': f"The file is in {os.path.splitext(fichier)[1]} format, which is not supported yet. Please convert to .docx / .odt / .pdf / .rtf."
                })
                continue

            if taille_fichier > file_size_limit:
                logging.warning(f"{YELLOW}File ignored because too large: {fichier}{RESET}")
                heavy_or_slow_files.append({
                    'PDF_Folder': id_dossier,
                    'PDF_Document': fichier,
                    'Issue': f'File larger than {taille} MB'
                })
                continue
            
            pdf_files.append((chemin_pdf, id_dossier, fichier))
    
    with ProcessPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(traiter_fichier_pdf, pdf_file, timeout, keywords, nb_phrases_avant, nb_phrases_apres, nlp, fusion_keyword_before_after, tesseract_cmd, use_tesseract,poppler_path,lang_OCR_tesseract): pdf_file for pdf_file in pdf_files}
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
                logging.error(f"{RED}Error processing file {fichier}: {str(e)}{RESET}")
                heavy_or_slow_files.append({'PDF_Folder': id_dossier, 'PDF_Document': fichier, 'Issue': str(e)})

    data.sort(key=lambda x: (x['PDF_Document'], x['Page_Number']))

    resultat_path = output_path or os.path.join(os.path.expanduser("~"), "Desktop", "resultat")
    os.makedirs(resultat_path, exist_ok=True)

    if data:
        tables_contingence = generer_tables_contingence(data, nlp)
        enregistrer_tables_contingence(tables_contingence, resultat_path, freque_document_keyword_table_name)
    else:
        logging.error(f"{RED}There are no documents containing the keywords! Please check your keywords ={RESET}")
        sys.exit(1)

    df = pd.DataFrame(data, columns=['PDF_Folder', 'PDF_Document', 'Page_Number', 'Keywords_Found', 'Length_Of_Extracted_Phrase', 'Info'])
    df_heavy_or_slow = pd.DataFrame(heavy_or_slow_files, columns=['PDF_Folder', 'PDF_Document', 'Issue'])

    df_heavy_or_slow = df_heavy_or_slow.drop_duplicates()
    
    if not result_keyword_table_name:
        logging.warning(f"{YELLOW}No result table name provided, the table name has been set to 'res' by default{RESET}")
        result_keyword_table_name = "res"

    df_path = os.path.join(resultat_path, f"{result_keyword_table_name}.xlsx")
    heavy_or_slow_df_path = os.path.join(resultat_path, "heavy_or_slow_df.xlsx")
    df.to_excel(df_path, index=False)
    df_heavy_or_slow.to_excel(heavy_or_slow_df_path, index=False)

    logging.info(f"{GREEN}The results have been saved in {resultat_path}{RESET}")
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"The script took {elapsed_time:.2f} seconds to execute.")









