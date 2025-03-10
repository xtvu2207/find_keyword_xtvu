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

max_threads = os.cpu_count() // 2
os.environ["NUMEXPR_MAX_THREADS"] = str(max_threads)


def install_and_import(package, import_name=None):
    try:
        if import_name is None:
            importlib.import_module(package)
        else:
            importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", package]
        )
    finally:
        if import_name is None:
            return importlib.import_module(package)
        else:
            return importlib.import_module(import_name)


json = install_and_import("json")
pdfplumber = install_and_import("pdfplumber")
pd = install_and_import("pandas")
spacy = install_and_import("spacy")
pytesseract = install_and_import("pytesseract")
PIL = install_and_import("Pillow", "PIL")
openpyxl = install_and_import("openpyxl")
pandoc = install_and_import("pandoc")
pypandoc = install_and_import("pypandoc")
reportlab = install_and_import("reportlab")
tempfile = install_and_import("tempfile")
collections = install_and_import("collections")
scipy = install_and_import("scipy")
json = install_and_import("json")
# multiprocessing = install_and_import("multiprocessing")
filelock = install_and_import("filelock")
shutil = install_and_import("shutil")
gc = install_and_import("gc")

from filelock import FileLock
from scipy.spatial.distance import cosine
from collections import defaultdict
from docx import Document  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # type: ignore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
Event = threading.Event
Image = PIL.Image


def init_nlp(language_prefix):
    RED = "\033[91m"
    RESET = "\033[0m"

    if language_prefix == "multi":
        model_name = "xx_sent_ud_sm"
        try:
            nlp = spacy.load(model_name)
            return nlp
        except OSError:
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name], check=True
                )
                nlp = spacy.load(model_name)
                return nlp
            except Exception as e:
                logging.error(
                    f"{RED}Unable to load the multilingual model '{model_name}'.{RESET}"
                )
                sys.exit(1)
    elif language_prefix == "en":
        model_variants = [
            f"{language_prefix}_core_web_lg",
            f"{language_prefix}_core_web_md",
            f"{language_prefix}_core_web_sm",
        ]
    else:
        model_variants = [
            f"{language_prefix}_core_news_lg",
            f"{language_prefix}_core_news_md",
            f"{language_prefix}_core_news_sm",
        ]

    for model_name in model_variants:
        try:
            nlp = spacy.load(model_name)
            return nlp
        except OSError:
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name], check=True
                )
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
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", fallback_model], check=True
            )
            nlp = spacy.load(fallback_model)
            return nlp
        except Exception as e:
            logging.error(
                f"{RED}Unable to load a language model for '{language_prefix}' and the fallback model '{fallback_model}'.{RESET}"
            )
            sys.exit(1)


def check_tesseract_requirements(tesseract_cmd, lang_OCR_tesseract, full_check=False):
    RED = "\033[91m"
    RESET = "\033[0m"
    YELLOW = "\033[93m"

    if not tesseract_cmd:
        logging.error(
            f"{RED}You chose to use pytesseract, but you didn't provide a Tesseract path. Please provide a valid Tesseract path or set use_tesseract to False if you don't want to use Tesseract.{RESET}"
        )
        sys.exit(1)

    try:
        result = subprocess.run(
            [tesseract_cmd, "--list-langs"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        available_languages = result.stdout.splitlines()

        if lang_OCR_tesseract not in available_languages:
            if full_check:
                if not lang_OCR_tesseract:
                    logging.error(
                        f"{RED}Full Tesseract requires a specific language for OCR, but no language was provided. Please provide a valid language code or set use_full_tesseract to False.{RESET}"
                    )
                    sys.exit(1)
                else:
                    logging.error(
                        f"{RED}Tesseract is missing the required language '{lang_OCR_tesseract}'. You cannot use full Tesseract for text extraction. Please install the necessary language files or set use_full_tesseract to False.{RESET}"
                    )
                    sys.exit(1)
            else:
                logging.warning(
                    f"{YELLOW}Tesseract does not have the language '{lang_OCR_tesseract}' installed. Some OCR functionality may not work as expected.{RESET}"
                )
                return False

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"{RED}Error while checking Tesseract languages: {str(e)}{RESET}")
        sys.exit(1)

    except Exception as e:
        logging.error(f"{RED}Error with Tesseract setup: {str(e)}{RESET}")
        sys.exit(1)


def sauvegarder_informations_et_textes_global(
    cache_folder_path, id_dossier, fichier, num_page, texte_page, max_retries=3
):
    document_info = {
        "PDF_Folder": id_dossier,
        "PDF_Document": fichier,
        "Page_Number": num_page,
        "Text": texte_page,
    }

    cache_folder_path = os.path.join(cache_folder_path, f"cache_{id_dossier}.json")

    lock_path = cache_folder_path + ".lock"

    with FileLock(lock_path):
        for attempt in range(max_retries):
            try:
                if os.path.exists(cache_folder_path):
                    with open(cache_folder_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = {}

                key = f"{id_dossier}_{fichier}"
                if key not in data:
                    data[key] = []

                page_found = False
                for entry in data[key]:
                    if entry["Page_Number"] == num_page:
                        entry["Text"] = texte_page
                        page_found = True
                        break

                if not page_found:
                    data[key].append(document_info)

                with tempfile.NamedTemporaryFile(
                    "w",
                    delete=False,
                    dir=os.path.dirname(cache_folder_path),
                    encoding="utf-8",
                ) as temp_file:
                    json.dump(data, temp_file, ensure_ascii=False, indent=4)
                    temp_file_path = temp_file.name

                shutil.move(temp_file_path, cache_folder_path)

                with open(cache_folder_path, "r", encoding="utf-8") as f:
                    validated_data = json.load(f)

                if key in validated_data and any(
                    entry["Page_Number"] == num_page for entry in validated_data[key]
                ):
                    logging.info(
                        f"Page {num_page} of file {fichier} in folder {id_dossier} successfully saved to cache."
                    )
                    break
                else:
                    logging.warning(
                        f"Validation failed for page {num_page} of file {fichier}. Retrying..."
                    )

            except Exception as e:
                logging.error(
                    f"Error during attempt {attempt + 1} to save page {num_page} of file {fichier}: {str(e)}"
                )
                if attempt < max_retries - 1:
                    logging.info("Retrying...")
                else:
                    logging.error(
                        f"Failed to save page {num_page} of file {fichier} after {max_retries} attempts."
                    )


def compter_occurrences_mot_cle(phrase, mots_cles, nlp, exact_match):
    total_occurrences = 0

    if not exact_match:
        phrase = " ".join([token.lemma_.lower() for token in nlp(phrase)])
    if isinstance(mots_cles, str):
        mots_cles = [mots_cles]

    for mot_cle in mots_cles:
        if exact_match:
            pattern = re.compile(rf"\b{re.escape(mot_cle.lower())}\b", re.IGNORECASE)
        else:
            mot_cle_lemme = nlp(mot_cle)[0].lemma_.lower()
            pattern = re.compile(rf"\b{re.escape(mot_cle_lemme)}\b", re.IGNORECASE)

        occurrences = len(pattern.findall(phrase.lower()))
        total_occurrences += occurrences
    return total_occurrences


def convertir_en_docx_in_memory(doc_path, pypandoc):
    RED = "\033[91m"
    RESET = "\033[0m"

    try:
        temp_docx_path = doc_path.rsplit(".", 1)[0] + "_temp.docx"
        pypandoc.convert_file(doc_path, "docx", outputfile=temp_docx_path)
        with open(temp_docx_path, "rb") as f:
            docx_buffer = BytesIO(f.read())
        os.remove(temp_docx_path)
        return docx_buffer
    except Exception as e:
        logging.error(
            f"{RED}Error converting {doc_path} to DOCX in memory: {str(e)}{RESET}"
        )
        return None


def convertir_docx_en_pdf_en_memoire(docx_path):
    RED = "\033[91m"
    RESET = "\033[0m"

    try:
        doc = Document(docx_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf_file:
            pdf = SimpleDocTemplate(temp_pdf_file.name, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            for para in doc.paragraphs:
                text = para.text
                style = styles["Normal"]
                p = Paragraph(text, style)
                elements.append(p)
                elements.append(Spacer(1, 0.2 * inch))
            pdf.build(elements)

        with open(temp_pdf_file.name, "rb") as f:
            pdf_content = f.read()

        os.remove(temp_pdf_file.name)

        return pdf_content
    except Exception as e:
        logging.error(f"{RED}Error during PDF conversion in memory: {str(e)}{RESET}")
        return None


def effectuer_ocr(image, pytesseract, lang_OCR_tesseract):
    return pytesseract.image_to_string(image, lang=lang_OCR_tesseract)


def extraire_blocs_texte(page):
    blocs = []
    if page.extract_text():
        for bloc in page.extract_words():
            blocs.append(
                {
                    "x0": bloc["x0"],
                    "top": bloc["top"],
                    "x1": bloc["x1"],
                    "bottom": bloc["bottom"],
                    "text": bloc["text"],
                }
            )
    return blocs


def extraire_ocr_des_images(page, bbox, pytesseract, lang_OCR_tesseract):
    RED = "\033[91m"
    RESET = "\033[0m"

    try:
        image_page = page.to_image(resolution=500).original
        width, height = image_page.size
        x0, y0, x1, y1 = bbox
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(x1, width), min(y1, height)
        image_recadree = image_page.crop((x0, y0, x1, y1))
        return effectuer_ocr(image_recadree, pytesseract, lang_OCR_tesseract)
    except Exception as e:
        if str(e) != "tile cannot extend outside image":
            logging.error(
                f"{RED}Error during OCR extraction from the image: {str(e)}{RESET}"
            )
        return ""


def extraire_phrases(
    texte,
    mot_clé,
    nb_phrases_avant,
    nb_phrases_apres,
    nlp,
    fusion_keyword_before_after,
    exact_match,
):
    doc = nlp(texte)
    phrases_avec_contexte = []
    phrases = list(doc.sents)

    if isinstance(mot_clé, list):
        if exact_match:
            mot_clé_pattern = re.compile(
                rf"\b({'|'.join(re.escape(mot.lower()) for mot in mot_clé)})\b"
            )
        else:
            mot_clé_lemme = [
                " ".join([token.lemma_.lower() for token in nlp(mot)])
                for mot in mot_clé
            ]
    else:
        if exact_match:
            mot_clé_pattern = re.compile(rf"\b{re.escape(mot_clé.lower())}\b")
        else:
            mot_clé_lemme = " ".join([token.lemma_.lower() for token in nlp(mot_clé)])

    dernier_extrait = None

    def ajouter_extrait(i):
        start = max(0, i - nb_phrases_avant)
        end = min(len(phrases), i + nb_phrases_apres + 1)
        phrases_contexte = " ".join([phrases[idx].text for idx in range(start, end)])
        return phrases_contexte

    def similarite_semantique(a, b):
        vec_a = nlp(a).vector
        vec_b = nlp(b).vector
        return 1 - cosine(vec_a, vec_b)

    for i, sent in enumerate(phrases):
        phrase_mots_clee_actuelle = sent.text.lower()

        if exact_match:
            if isinstance(mot_clé, list):
                if mot_clé_pattern.search(phrase_mots_clee_actuelle):
                    extrait_actuel = ajouter_extrait(i)
                    if fusion_keyword_before_after:
                        if (
                            dernier_extrait is None
                            or similarite_semantique(dernier_extrait, extrait_actuel)
                            < 0.95
                        ):
                            phrases_avec_contexte.append(extrait_actuel)
                            dernier_extrait = extrait_actuel
                    else:
                        phrases_avec_contexte.append(extrait_actuel)
            else:
                if mot_clé_pattern.search(phrase_mots_clee_actuelle):
                    extrait_actuel = ajouter_extrait(i)
                    if fusion_keyword_before_after:
                        if (
                            dernier_extrait is None
                            or similarite_semantique(dernier_extrait, extrait_actuel)
                            < 0.95
                        ):
                            phrases_avec_contexte.append(extrait_actuel)
                            dernier_extrait = extrait_actuel
                    else:
                        phrases_avec_contexte.append(extrait_actuel)
        else:
            if isinstance(mot_clé, list):
                if any(mot in phrase_mots_clee_actuelle for mot in mot_clé_lemme):
                    extrait_actuel = ajouter_extrait(i)
                    if fusion_keyword_before_after:
                        if (
                            dernier_extrait is None
                            or similarite_semantique(dernier_extrait, extrait_actuel)
                            < 0.95
                        ):
                            phrases_avec_contexte.append(extrait_actuel)
                            dernier_extrait = extrait_actuel
                    else:
                        phrases_avec_contexte.append(extrait_actuel)
            else:
                if mot_clé_lemme in phrase_mots_clee_actuelle:
                    extrait_actuel = ajouter_extrait(i)
                    if fusion_keyword_before_after:
                        if (
                            dernier_extrait is None
                            or similarite_semantique(dernier_extrait, extrait_actuel)
                            < 0.95
                        ):
                            phrases_avec_contexte.append(extrait_actuel)
                            dernier_extrait = extrait_actuel
                    else:
                        phrases_avec_contexte.append(extrait_actuel)

    return phrases_avec_contexte


def traiter_page(
    page,
    id_dossier,
    fichier,
    num_page,
    keywords,
    nb_phrases_avant,
    nb_phrases_apres,
    nlp,
    pytesseract,
    fusion_keyword_before_after,
    use_tesseract,
    lang_OCR_tesseract,
    exact_match,
    phrase_incomplete,
    use_full_tesseract,
):
    RED = "\033[91m"
    RESET = "\033[0m"

    data = []
    pages_problematiques = []
    logging.info(f"Processing page {num_page} of file {fichier} in folder {id_dossier}")

    try:
        if use_tesseract and use_full_tesseract:
            image_page = page.to_image(resolution=500).original
            texte_complet = effectuer_ocr(image_page, pytesseract, lang_OCR_tesseract)
        else:
            blocs_texte = extraire_blocs_texte(page)

            if use_tesseract:
                for img in page.images:
                    x0, y0, x1, y1 = img["x0"], img["top"], img["x1"], img["bottom"]
                    texte_ocr = extraire_ocr_des_images(
                        page, (x0, y0, x1, y1), pytesseract, lang_OCR_tesseract
                    )
                    if texte_ocr:
                        blocs_texte.append(
                            {
                                "x0": x0,
                                "top": y0,
                                "x1": x1,
                                "bottom": y1,
                                "text": texte_ocr,
                            }
                        )
                blocs_texte.sort(key=lambda x: (x["top"], x["x0"]))

            texte_complet = " ".join([bloc["text"] for bloc in blocs_texte])

        if phrase_incomplete:
            texte_complet = phrase_incomplete + " " + texte_complet
        if texte_complet and not texte_complet.strip().endswith((".", "!", "?")):
            phrases = list(nlp(texte_complet).sents)
            phrase_incomplete = phrases.pop(-1).text.strip()
            texte_complet = " ".join([phrase.text for phrase in phrases])
        else:
            phrase_incomplete = ""

        if texte_complet:
            for mot_clé in keywords:
                phrases = extraire_phrases(
                    texte_complet,
                    mot_clé,
                    nb_phrases_avant,
                    nb_phrases_apres,
                    nlp,
                    fusion_keyword_before_after,
                    exact_match,
                )
                mot_clé_str = (
                    ", ".join(mot_clé) if isinstance(mot_clé, list) else mot_clé
                )
                for phrase in phrases:
                    result_entry = {
                        "PDF_Folder": id_dossier,
                        "PDF_Document": fichier,
                        "Page_Number": num_page,
                        "Keywords_Found": mot_clé_str,
                        "Occurrences_Of_Keyword_In_Phrases": compter_occurrences_mot_cle(
                            phrase, mot_clé, nlp, exact_match
                        ),
                        "Info": phrase,
                    }
                    if fusion_keyword_before_after:
                        for keyword_group in keywords:
                            if isinstance(keyword_group, list):
                                for keyword in keyword_group:
                                    result_entry[keyword] = compter_occurrences_mot_cle(
                                        phrase, keyword, nlp, exact_match
                                    )
                            else:
                                result_entry[keyword_group] = (
                                    compter_occurrences_mot_cle(
                                        phrase, keyword_group, nlp, exact_match
                                    )
                                )

                    data.append(result_entry)
    except Exception as e:
        logging.error(
            f"{RED}Error processing page {num_page} of file {fichier}: {str(e)}{RESET}"
        )
        pages_problematiques.append(num_page)

    return data, pages_problematiques, phrase_incomplete, texte_complet


def traiter_page_from_text(
    texte_complet,
    id_dossier,
    fichier,
    num_page,
    keywords,
    nb_phrases_avant,
    nb_phrases_apres,
    nlp,
    fusion_keyword_before_after,
    exact_match,
):
    data = []
    pages_problematiques = []
    RED = "\033[91m"
    RESET = "\033[0m"

    try:
        for mot_clé in keywords:
            phrases = extraire_phrases(
                texte_complet,
                mot_clé,
                nb_phrases_avant,
                nb_phrases_apres,
                nlp,
                fusion_keyword_before_after,
                exact_match,
            )
            mot_clé_str = ", ".join(mot_clé) if isinstance(mot_clé, list) else mot_clé
            for phrase in phrases:
                result_entry = {
                    "PDF_Folder": id_dossier,
                    "PDF_Document": fichier,
                    "Page_Number": num_page,
                    "Keywords_Found": mot_clé_str,
                    "Occurrences_Of_Keyword_In_Phrases": compter_occurrences_mot_cle(
                        phrase, mot_clé, nlp, exact_match
                    ),
                    "Info": phrase,
                }
                if fusion_keyword_before_after:
                    for keyword_group in keywords:
                        if isinstance(keyword_group, list):
                            for keyword in keyword_group:
                                result_entry[keyword] = compter_occurrences_mot_cle(
                                    phrase, keyword, nlp, exact_match
                                )
                        else:
                            result_entry[keyword_group] = compter_occurrences_mot_cle(
                                phrase, keyword_group, nlp, exact_match
                            )

                data.append(result_entry)
    except Exception as e:
        logging.error(
            f"{RED}Error processing text for page {num_page} of file {fichier}: {str(e)}{RESET}"
        )
        pages_problematiques.append(num_page)

    return data, pages_problematiques


def traiter_fichier_pdf(
    args,
    timeout,
    keywords,
    nb_phrases_avant,
    nb_phrases_apres,
    nlp,
    fusion_keyword_before_after,
    tesseract_cmd,
    use_tesseract,
    lang_OCR_tesseract,
    exact_match,
    use_full_tesseract,
    cache_folder_path,
):
    RED = "\033[91m"
    RESET = "\033[0m"

    chemin_pdf, id_dossier, fichier = args

    if use_tesseract:
        pytesseract = install_and_import("pytesseract")
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    else:
        pytesseract = None

    pypandoc = install_and_import("pypandoc")

    logging.info(f"Processing file {fichier} in folder {id_dossier}")
    data = []
    pages_problematiques = []

    texte_complet_document = []

    cache_file_path = os.path.join(cache_folder_path, f"cache_{id_dossier}.json")

    if not cache_file_path:
        texte_sauvegarde = {}
    else:
        if os.path.exists(cache_file_path):
            with open(cache_file_path, "r", encoding="utf-8") as f:
                texte_sauvegarde = json.load(f)
        else:
            texte_sauvegarde = {}

    key = f"{id_dossier}_{fichier}"

    if key in texte_sauvegarde:
        logging.info(f"Using saved text for file {fichier}")
        for page_info in texte_sauvegarde[key]:
            num_page = page_info["Page_Number"]
            texte_complet = page_info["Text"]

            page_data, problematic_pages = traiter_page_from_text(
                texte_complet,
                id_dossier,
                fichier,
                num_page,
                keywords,
                nb_phrases_avant,
                nb_phrases_apres,
                nlp,
                fusion_keyword_before_after,
                exact_match,
            )

            data.extend(page_data)
            pages_problematiques.extend(problematic_pages)
    else:
        phrase_incomplete = ""
        try:
            if chemin_pdf.endswith((".rtf", ".odt")):
                docx_buffer = convertir_en_docx_in_memory(chemin_pdf, pypandoc)
                if docx_buffer is None:
                    raise Exception(
                        f"{RED}Error converting file {fichier} to DOCX{RESET}"
                    )
                pdf_bytes = convertir_docx_en_pdf_en_memoire(docx_buffer)
                if pdf_bytes is None:
                    raise Exception(f"{RED}Error converting DOCX file in memory{RESET}")
            elif chemin_pdf.endswith(".docx"):
                pdf_bytes = convertir_docx_en_pdf_en_memoire(chemin_pdf)
                if pdf_bytes is None:
                    raise Exception(
                        f"{RED}Error converting DOCX file {chemin_pdf}{RESET}"
                    )
            else:
                with open(chemin_pdf, "rb") as f:
                    pdf_bytes = f.read()

            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for num_page in range(len(pdf.pages)):
                    page = pdf.pages[num_page]
                    with ThreadPoolExecutor(max_workers=1) as page_executor:
                        future = page_executor.submit(
                            traiter_page,
                            page,
                            id_dossier,
                            fichier,
                            num_page + 1,
                            keywords,
                            nb_phrases_avant,
                            nb_phrases_apres,
                            nlp,
                            pytesseract,
                            fusion_keyword_before_after,
                            use_tesseract,
                            lang_OCR_tesseract,
                            exact_match,
                            phrase_incomplete,
                            use_full_tesseract,
                        )
                        try:
                            (
                                page_data,
                                problematic_pages,
                                phrase_incomplete,
                                texte_complet,
                            ) = future.result(timeout=timeout)

                            data.extend(page_data)
                            pages_problematiques.extend(problematic_pages)
                            texte_complet_document.append((num_page + 1, texte_complet))
                        except Exception as e:
                            logging.error(
                                f"{RED}Timeout or error processing page {num_page + 1} of file {fichier}: {str(e)}{RESET}"
                            )
                            pages_problematiques.append(num_page + 1)
                    gc.collect()
                pdf.close()

                if cache_file_path:
                    for num_page, texte_page in texte_complet_document:
                        sauvegarder_informations_et_textes_global(
                            cache_folder_path, id_dossier, fichier, num_page, texte_page
                        )

        except Exception as e:
            logging.error(f"{RED}Error opening file {chemin_pdf}: {str(e)}{RESET}")
            return None, {
                "PDF_Folder": id_dossier,
                "PDF_Document": fichier,
                "Issue": str(e),
            }

    if pages_problematiques:
        issue_description = (
            f"Timeout or error on pages {', '.join(map(str, pages_problematiques))}"
        )
        return data, {
            "PDF_Folder": id_dossier,
            "PDF_Document": fichier,
            "Issue": issue_description,
        }

    data.sort(key=lambda x: x["Page_Number"])
    gc.collect()
    return data, None


def nettoyer_donnees(dataframe):
    def clean_cell(cell):
        if isinstance(cell, str):
            cell = re.sub(r"[^\x20-\x7E]", "", cell)
            return cell.strip()
        return cell

    for col in dataframe.columns:
        if dataframe[col].dtype == "object":
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


def generer_tables_contingence(data, nlp, fusion_keyword_before_after, exact_match):
    df_data = pd.DataFrame(data)
    tables_contingence = {}

    def lemmatize_text(text, nlp):
        return " ".join([token.lemma_.lower() for token in nlp(text)])

    def lemmatize_keyword(keyword, nlp):
        return nlp(keyword)[0].lemma_.lower()

    def split_keywords(keywords):
        if isinstance(keywords, str):
            return [k.strip() for k in keywords.split(",")]
        return [keywords]

    if fusion_keyword_before_after:
        for id_dossier, group in df_data.groupby("PDF_Folder"):
            keyword_counts = defaultdict(lambda: defaultdict(int))
            group = group.sort_values(by=["PDF_Document", "Page_Number"])

            for document, doc_group in group.groupby("PDF_Document"):
                combined_info = " ".join(doc_group["Info"].tolist())
                if not exact_match:
                    combined_info = lemmatize_text(combined_info, nlp)

                for keywords_str in doc_group["Keywords_Found"].unique():
                    keywords_list = split_keywords(keywords_str)
                    for keyword in keywords_list:
                        if not exact_match:
                            keyword = lemmatize_keyword(keyword, nlp)
                        pattern = re.compile(
                            rf"\b{re.escape(keyword)}\b", re.IGNORECASE
                        )
                        count = len(pattern.findall(combined_info.lower()))
                        keyword_counts[document][keyword] += count

            df_keyword_counts = pd.DataFrame(keyword_counts).fillna(0).T
            tables_contingence[id_dossier] = df_keyword_counts

    else:
        for id_dossier, group in df_data.groupby("PDF_Folder"):
            table = group.pivot_table(
                index="PDF_Document",
                columns="Keywords_Found",
                values="Occurrences_Of_Keyword_In_Phrases",
                aggfunc="count",
                fill_value=0,
            )
            tables_contingence[id_dossier] = table

    return tables_contingence


def enregistrer_tables_contingence(
    tables_contingence, output_path, freque_document_keyword_table_name
):
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    if not freque_document_keyword_table_name:
        logging.warning(
            f"{YELLOW}No contingency table name for document by keyword provided, the table name has been set to 'freque_document_keyword' by default{RESET}"
        )
        freque_document_keyword_table_name = "freque_document_keyword"

    excel_path = os.path.join(output_path, f"{freque_document_keyword_table_name}.xlsx")

    with pd.ExcelWriter(excel_path) as writer:
        for id_dossier, table in tables_contingence.items():
            table.to_excel(writer, sheet_name=id_dossier[:31])

    logging.info(f"{GREEN}Contingency tables have been saved in {excel_path}{RESET}")


def enregistrer_tables_contingence_ensemble(
    tables_contingence, output_path, freque_document_keyword_table_name
):
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    if not freque_document_keyword_table_name:
        logging.warning(
            f"{YELLOW}No contingency table name for document by keyword provided, the table name has been set to 'freque_document_keyword' by default{RESET}"
        )
        freque_document_keyword_table_name = "freque_document_keyword"

    excel_path = os.path.join(output_path, f"{freque_document_keyword_table_name}.xlsx")

    combined_df = pd.DataFrame()

    for id_dossier, table in tables_contingence.items():
        table["PDF_Folder"] = id_dossier
        table.reset_index(inplace=True)
        table.rename(columns={"index": "Document_Name"}, inplace=True)
        combined_df = pd.concat([combined_df, table])

    columns = ["PDF_Folder"] + [
        col for col in combined_df.columns if col != "PDF_Folder"
    ]
    combined_df = combined_df[columns]

    with pd.ExcelWriter(excel_path) as writer:
        combined_df.to_excel(writer, sheet_name="Contingency_Tables", index=False)

    logging.info(
        f"{GREEN}All contingency tables have been combined and saved in {excel_path}{RESET}"
    )


def find_keyword_xtvu(
    prefixe_langue="fr",
    threads_rest=None,
    nb_phrases_avant=10,
    nb_phrases_apres=10,
    keywords=None,
    exact_match=True,
    taille=20,
    timeout=200,
    result_keyword_table_name="",
    freque_document_keyword_table_name="",
    fusion_keyword_before_after=False,
    tesseract_cmd="",
    use_tesseract=False,
    use_full_tesseract=False,
    lang_OCR_tesseract="fra",
    input_path="/path/to/input",
    output_path="/path/to/output",
    poppler_path="",
    cache_folder_path="/path/to/cache_dir",
):
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    tesseract_cmd = tesseract_cmd.replace("\\", "/")
    input_path = input_path.replace("\\", "/")
    output_path = output_path.replace("\\", "/")
    cache_folder_path = cache_folder_path.replace("\\", "/")

    if use_tesseract:
        if not check_tesseract_requirements(
            tesseract_cmd, lang_OCR_tesseract, full_check=use_full_tesseract
        ):
            if not use_full_tesseract:
                logging.warning(
                    f"{YELLOW}Tesseract might not work correctly without all required files.{RESET}"
                )

    if not keywords:
        logging.error(
            f"{RED}The keyword list (KEYWORDS) cannot be empty. Please provide a valid list.{RESET}"
        )
        sys.exit(1)
    if not output_path or not os.path.isdir(output_path):
        logging.error(
            f"{RED}The output directory path (output_path) is invalid or not defined.{RESET}"
        )
        sys.exit(1)
    if not input_path or not os.path.isdir(input_path):
        logging.error(
            f"{RED}The input directory path (input_path) is invalid or not defined.{RESET}"
        )
        sys.exit(1)
    if not cache_folder_path:
        logging.warning(
            f"{YELLOW}No path provided for the cache directory. Text documents will not be saved for future use.{RESET}"
        )
    else:
        if not os.path.exists(cache_folder_path):
            try:
                os.makedirs(cache_folder_path)
                logging.info(
                    f"{GREEN}Directory created for the cache: {cache_folder_path}{RESET}"
                )
            except Exception as e:
                logging.error(
                    f"{RED}Failed to create directory for cache: {str(e)}. Text documents will not be saved for future use.{RESET}"
                )
                cache_folder_path = ""

    if threads_rest is None:
        max_threads = os.cpu_count() // 2
    else:
        max_threads = os.cpu_count() - threads_rest
    os.environ["NUMEXPR_MAX_THREADS"] = str(max_threads)
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

            if fichier.endswith((".docx", ".odt", ".pdf", ".rtf")):
                chemin_pdf = chemin_complet
            else:
                logging.warning(
                    f"{YELLOW}File ignored because unsupported: {fichier}{RESET}"
                )
                heavy_or_slow_files.append(
                    {
                        "PDF_Folder": id_dossier,
                        "PDF_Document": fichier,
                        "Issue": f"The file is in {os.path.splitext(fichier)[1]} format, which is not supported yet. Please convert to .docx / .odt / .pdf / .rtf.",
                    }
                )
                continue

            if taille_fichier > file_size_limit:
                logging.warning(
                    f"{YELLOW}File ignored because too large: {fichier}{RESET}"
                )
                heavy_or_slow_files.append(
                    {
                        "PDF_Folder": id_dossier,
                        "PDF_Document": fichier,
                        "Issue": f"File larger than {taille} MB",
                    }
                )
                continue

            pdf_files.append((chemin_pdf, id_dossier, fichier))

    try:
        with ProcessPoolExecutor(max_workers=max_threads) as executor:
            futures = {
                executor.submit(
                    traiter_fichier_pdf,
                    pdf_file,
                    timeout,
                    keywords,
                    nb_phrases_avant,
                    nb_phrases_apres,
                    nlp,
                    fusion_keyword_before_after,
                    tesseract_cmd,
                    use_tesseract,
                    lang_OCR_tesseract,
                    exact_match,
                    use_full_tesseract,
                    cache_folder_path,
                ): pdf_file
                for pdf_file in pdf_files
            }
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
                    logging.error(
                        f"{RED}Error processing file {fichier}: {str(e)}{RESET}"
                    )
                    heavy_or_slow_files.append(
                        {
                            "PDF_Folder": id_dossier,
                            "PDF_Document": fichier,
                            "Issue": str(e),
                        }
                    )

        data.sort(key=lambda x: (x["PDF_Document"], x["Page_Number"]))

        resultat_path = output_path or os.path.join(
            os.path.expanduser("~"), "Desktop", "resultat"
        )
        os.makedirs(resultat_path, exist_ok=True)

        if data:
            tables_contingence = generer_tables_contingence(
                data,
                nlp,
                fusion_keyword_before_after=fusion_keyword_before_after,
                exact_match=exact_match,
            )
            enregistrer_tables_contingence_ensemble(
                tables_contingence, resultat_path, freque_document_keyword_table_name
            )
            # enregistrer_tables_contingence(tables_contingence, resultat_path, freque_document_keyword_table_name)
        else:
            logging.error(
                f"{RED}There are no documents containing the keywords! Please check your keywords :-){RESET}"
            )
            sys.exit(1)

        columns = [
            "PDF_Folder",
            "PDF_Document",
            "Page_Number",
            "Keywords_Found",
            "Occurrences_Of_Keyword_In_Phrases",
            "Info",
        ]

        if fusion_keyword_before_after:
            for keyword_group in keywords:
                if isinstance(keyword_group, list):
                    columns.extend(keyword_group)
                else:
                    columns.append(keyword_group)

        df = pd.DataFrame(data, columns=columns)
        df_heavy_or_slow = pd.DataFrame(
            heavy_or_slow_files, columns=["PDF_Folder", "PDF_Document", "Issue"]
        )

        df_heavy_or_slow = df_heavy_or_slow.drop_duplicates()

        if not result_keyword_table_name:
            logging.warning(
                f"{YELLOW}No result table name provided, the table name has been set to 'res' by default{RESET}"
            )
            result_keyword_table_name = "res"

        df_path = os.path.join(resultat_path, f"{result_keyword_table_name}.xlsx")
        heavy_or_slow_df_path = os.path.join(resultat_path, "heavy_or_slow_df.xlsx")
        df.to_excel(df_path, index=False)
        df_heavy_or_slow.to_excel(heavy_or_slow_df_path, index=False)

        logging.info(f"{GREEN}The results have been saved in {resultat_path}{RESET}")
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"The script took {elapsed_time:.2f} seconds to execute.")
    finally:
        lock_path = cache_folder_path + ".lock"
        if os.path.exists(lock_path):
            os.remove(lock_path)
