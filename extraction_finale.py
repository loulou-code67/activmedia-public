import re
import pdfplumber
import pandas as pd
import fitz  # PyMuPDF

INVENTAIRE_CSV = "/Users/loulou/Desktop/Stage/inventaire_collecte_documents.csv"

OUTPUT_ALL = "/Users/loulou/Desktop/Stage/documents_structures_clean.csv"
OUTPUT_MAIN = "/Users/loulou/Desktop/Stage/factures_devis_clean.csv"
OUTPUT_EXPENSES = "/Users/loulou/Desktop/Stage/depenses_clean.csv"
OUTPUT_EXPENSES_AVANT_NETTOYAGE = "/Users/loulou/Desktop/Stage/depenses_clean_avant_nettoyage.csv"
OUTPUT_EXCLUDED = "/Users/loulou/Desktop/Stage/documents_exclus.csv"

MOTS_A_IGNORER = {
    "annuel", "mensuel", "facture", "factures", "devis", "bilan", "bilans",
    "client", "clients", "fournisseur", "fournisseurs", "compta",
    "stage", "document", "documents", "pdf"
}

NORMALISATION_LIBELLES = {
    # Énergie / télécom
    "edf": "EDF",
    "engie": "ENGIE",
    "orange": "ORANGE",
    "sfr": "SFR",
    "free": "FREE",

    # Logiciels / SaaS
    "zoom": "ZOOM",
    "adobe": "ADOBE",
    "google": "GOOGLE",
    "microsoft": "MICROSOFT",
    "openai": "OPENAI",
    "chatgpt": "OPENAI",
    "make": "MAKE",
    "celonis": "MAKE",
    "ovh": "OVH",
    "notion": "NOTION",
    "airtable": "AIRTABLE",
    "stripe": "STRIPE",
    "wprocket": "WPROCKET",
    "digiforma": "DIGIFORMA",
    "a world for us": "DIGIFORMA",
    "elephorm": "ELEPHORM",
    "fastrp": "ELEPHORM",
    "yamm": "YAMM",
    "talarian": "YAMM",

    # Matériel / achats
    "amazon": "AMAZON",
    "apple": "APPLE",
    "fnac direct": "FNAC DIRECT",
    "fnac": "FNAC DIRECT",
    "darty": "DARTY",
    "thomann": "THOMANN",
    "mabex": "MABEX",
    "foxway": "FOXWAY",
    "micrologik": "MICROLOGIK",
    "oviala": "OVIALA",
    "icasque": "ICASQUE",
    "xiaomi": "XIAOMI",

    # Transport
    "fedex": "FEDEX",
    "tnt": "FEDEX",
    "sncf": "SNCF",

    # Restauration
    "nespresso": "NESPRESSO",
    "rossini": "ROSSINI",
    "pedro": "PEDRO SAS",
    "delicity": "PEDRO SAS",

    # Travaux
    "rt rénovation": "RT RENOVATION",
    "r.t rénovation": "RT RENOVATION",
    "rt renovation": "RT RENOVATION",
    "r.t renovation": "RT RENOVATION",
    "lab ac30": "LAB",
    "sarl l.a.b": "LAB",
    "l.a.b": "LAB",
    "lab06": "LAB",
    "lab renovation": "LAB",
    "bureau.lab06": "LAB",
    "lab ": "LAB",

    # Prestations / freelances / formation
    "maava consulting": "MAAVA CONSULTING",
    "maava": "MAAVA CONSULTING",

    "studio87": "STUDIO87",
    "studiographique87": "STUDIO87",
    "leslie doyhamboure": "STUDIO87",

    "rochetaing": "JEAN-DOMINIQUE ROCHETAING",
    "jean-dominique": "JEAN-DOMINIQUE ROCHETAING",
    "jeandominique": "JEAN-DOMINIQUE ROCHETAING",

    "nikolova rositsa": "COM INTO BLOSSOM",
    "nikolova": "COM INTO BLOSSOM",
    "rositsa": "COM INTO BLOSSOM",
    "com into blossom": "COM INTO BLOSSOM",

    "pellegrin": "PE CONSULTANT SEO",
    "enrick": "PE CONSULTANT SEO",
    "pe consultant": "PE CONSULTANT SEO",

    "meunier": "LAURA MEUNIER",
    "mouchvoz": "LAURA MEUNIER",

    "arnaud degrave": "ARNAUD DEGRAVE",
    "degrave": "ARNAUD DEGRAVE",

    "françois maestrati": "FRANCOIS MAESTRATI",
    "francois maestrati": "FRANCOIS MAESTRATI",
    "maestrati": "FRANCOIS MAESTRATI",

    "julian guillen": "JULIAN GUILLEN",
    "guillen": "JULIAN GUILLEN",

    "brainyup": "BRAINYUP",

    "activaj": "ACTIVAJ",
    "pépite": "PEPITE",
    "pepite": "PEPITE",
    "ecri": "ECRI",
    "entrarts": "ENTRARTS",
    "berthelot": "TESS BERTHELOT",
    "freddela": "FREDERIC DE LAVENNE",
    "lavenne": "FREDERIC DE LAVENNE",

    # À ignorer / éviter comme fournisseur
    "activmedia": "ACTIVMEDIA",
}

MOIS_FR = {
    "janvier": "01",
    "février": "02",
    "fevrier": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "août": "08",
    "aout": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "décembre": "12",
    "decembre": "12",
}

MOIS_FR_COURT = {
    "jan": "01",
    "fev": "02",
    "fév": "02",
    "mar": "03",
    "avr": "04",
    "mai": "05",
    "jun": "06",
    "jui": "07",
    "jul": "07",
    "aou": "08",
    "aoû": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
    "déc": "12",
}

MOIS_EN = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

MOIS_EN_COURT = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def nettoyer_texte(texte):
    if not texte:
        return ""
    texte = texte.replace("\xa0", " ")
    texte = texte.replace("\u202f", " ")
    texte = texte.replace("¤", "€")
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n+", "\n", texte)
    return texte.strip()


def lire_pdf_texte(pdf_path, max_pages=20):
    try:
        doc = fitz.open(pdf_path)
        texte = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            texte.append(page.get_text("text"))
        doc.close()
        return nettoyer_texte("\n".join(texte))
    except Exception:
        return ""


def convertir_montant_vers_float(valeur):
    if valeur is None:
        return None

    valeur = str(valeur).lower()
    valeur = valeur.replace("€", "").replace("eur", "").replace("$", "").replace("usd", "")
    valeur = valeur.replace("\u202f", " ").replace("\xa0", " ")
    valeur = valeur.strip()

    signe = -1 if valeur.startswith("-") else 1
    valeur = valeur.lstrip("+-").strip()
    valeur = valeur.replace(" ", "")

    if "," in valeur:
        valeur = valeur.replace(".", "")
        valeur = valeur.replace(",", ".")
    else:
        if valeur.count(".") > 1:
            valeur = valeur.replace(".", "")

    try:
        return signe * float(valeur)
    except Exception:
        return None


def normaliser_date(date_str):
    if not date_str or pd.isna(date_str):
        return None

    s = str(date_str).strip().lower()

    # YYYYMMDD
    m = re.fullmatch(r"(20\d{2})(\d{2})(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # DD/MM/YYYY
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # DD-MM-YYYY (🔥 NOUVEAU)
    m = re.match(r"(\d{2})-(\d{2})-(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # DD-MM-YYYY HH:MM (🔥 PITCHOUN)
    m = re.match(r"(\d{2})-(\d{2})-(\d{4})\s*/?\s*\d{2}:\d{2}", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # YYYY-MM-DD
    m = re.match(r"(20\d{2})-(\d{2})-(\d{2})", s)
    if m:
        return s

    # FR mois texte
    m = re.match(r"(\d{1,2})\s+([a-zéûôîàèù]+)\s+(\d{4})", s)
    if m:
        jour, mois_txt, annee = m.groups()
        mois = (
            MOIS_FR.get(mois_txt)
            or MOIS_FR_COURT.get(mois_txt[:3])
        )
        if mois:
            return f"{annee}-{mois}-{jour.zfill(2)}"

    # EN mois texte (🔥 IMPORTANT)
    m = re.match(r"([a-z]+)\s+(\d{1,2}),?\s*(\d{4})", s)
    if m:
        mois_txt, jour, annee = m.groups()
        mois = (
            MOIS_EN.get(mois_txt)
            or MOIS_EN_COURT.get(mois_txt[:3])
        )
        if mois:
            return f"{annee}-{mois}-{jour.zfill(2)}"

    return None


def extraire_date(texte, nom_fichier=None):
    # 🔥 PRIORITÉ PDF RÉELS (Apple, Amazon, etc.)
    texte_min = texte.lower()

    patterns_fiables = [
        r"date de la facture[:\s]+(\d{2}\.\d{2}\.\d{4})",
        r"date de la facture.*?(\d{2}\.\d{2}\.\d{4})",
        r"date de la facture/date de la livraison.*?(\d{2}\.\d{2}\.\d{4})",
        r"facture\s*n?[°o]?\s*\S+\s+du\s+(\d{2}/\d{2}/\d{4})",
    ]

    for pattern in patterns_fiables:
        match = re.search(pattern, texte, flags=re.IGNORECASE | re.DOTALL)
        if match:
            d = normaliser_date(match.group(1))
            if d:
                return d

    patterns_prioritaires = [
        r"date d['’]émission\s*[:\-]?\s*([^\n]+)",
        r"date de la facture\s*[:\-]?\s*([^\n]+)",
        r"date de facturation\s*[:\-]?\s*([^\n]+)",
        r"date de facture\s*[:\-]?\s*([^\n]+)",
        r"invoice date\s*[:\-]?\s*([^\n]+)",
        r"date of issue\s*[:\-]?\s*([^\n]+)",
        r"date paid\s*[:\-]?\s*([^\n]+)",
        r"paid on\s*([a-zA-Z]+\s+\d{1,2},?\s*\d{4})",
        r"purchase date\s*[:\-]?\s*([^\n]+)",
        r"date\s*/\s*heure\s*([^\n]+)",
        r"date de l['’]opération\s*[:\-]?\s*([^\n]+)",
        r"date d['’]émission de la facture\s*[:\-]?\s*([^\n]+)",
        r"en date du\s*([^\n]+)",
        r"facture du\s*([^\n]+)",
        r"date\s*[:\-]?\s*(20\d{2}-\d{2}-\d{2})",
        r"date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
        r"date\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{4})",
        r"date de la facture\s*[:\-]?\s*([^\n]+)",
        r"date of issue\s*[:\-]?\s*([^\n]+)",      # MAKE
        r"date paid\s*([^\n]+)",                  # YAMM
        r"purchase date\s*[:\-]?\s*([^\n]+)",     # XIAOMI
        r"date\s*/\s*heure\s*([^\n]+)",           # PITCHOUN
    ]

    candidats_regex = [
        r"(20\d{2}\d{2}\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{2}\.\d{2}\.\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}\s+[a-zA-Zéûôîàèù]+\s+\d{4})",
        r"([a-zA-Z]+\s+\d{1,2},?\s*\d{4})",
        r"(\d{1,2}[-/][a-zA-Zéûôîàèù]+[-/]\d{4})",
        r"(\d{1,2}-[a-zA-Z]{3}-\d{4})",
    ]

    # 1. Dates avec libellé clair
    for pattern in patterns_prioritaires:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            brut = match.group(1).strip()

            for coupe in [
                "règlement", "reglement", "page", "échéance", "echeance",
                "tax", "invoice", "numéro", "numero", "n°", "total"
            ]:
                brut = brut.split(coupe)[0].strip()

            for c in candidats_regex:
                mm = re.search(c, brut, flags=re.IGNORECASE)
                if mm:
                    d = normaliser_date(mm.group(1))
                    if d:
                        an = int(d[:4])
                        if 2000 <= an <= 2030:
                            return d

    # 2. Recherche globale dans le texte
    patterns_global = [
        r"\b(20\d{2}\d{2}\d{2})\b",
        r"\b(\d{2}/\d{2}/\d{4})\b",
        r"\b(\d{2}-\d{2}-\d{4})\b",
        r"\b(\d{2}\.\d{2}\.\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}\s+[a-zA-Zéûôîàèù]+\s+\d{4})\b",
        r"\b([a-zA-Z]+\s+\d{1,2},?\s*\d{4})\b",
        r"\b(\d{1,2}[-/][a-zA-Zéûôîàèù]+[-/]\d{4})\b",
        r"\b(\d{1,2}-[a-zA-Z]{3}-\d{4})\b",
    ]

    for pattern in patterns_global:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            brut = match.group(1)
            d = normaliser_date(brut)
            if d:
                an = int(d[:4])
                if 2000 <= an <= 2030:
                    return d

    # 3. Recherche dans le nom du fichier
    if nom_fichier:
        nom = str(nom_fichier).lower()

        m = re.search(r"(20\d{6})", nom)
        if m:
            d = normaliser_date(m.group(1))
            if d:
                return d

        m = re.search(r"(20\d{2})[-_](\d{2})[-_](\d{2})", nom)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

        m = re.search(r"(\d{2})(\d{2})(20\d{2})", nom)
        if m:
            mois, jour, annee = m.groups()
            return f"{annee}-{mois}-{jour}"

        m = re.search(r"(\d{2}/\d{2}/\d{4})", nom)
        if m:
            d = normaliser_date(m.group(1))
            if d:
                return d

    return None

def extraire_date_depuis_pdf(row):
    try:
        chemin = row.get("chemin_fichier")

        if pd.isna(chemin) or not chemin:
            return None

        with pdfplumber.open(chemin) as pdf:
            texte = ""
            for page in pdf.pages[:2]:
                texte += "\n" + (page.extract_text() or "")

        texte = texte.replace("\n", " ")

        # =========================
        # 1. FORMAT NUMERIQUE (Amazon, ICASQUE)
        # =========================
        match = re.search(r"\b\d{2}[./]\d{2}[./]20\d{2}\b", texte)
        if match:
            return pd.to_datetime(match.group(0), dayfirst=True, errors="coerce")

        # =========================
        # 2. FORMAT ZOOM (anglais)
        # =========================
        match = re.search(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+20\d{2}\b",
            texte,
            flags=re.IGNORECASE
        )
        if match:
            return pd.to_datetime(match.group(0), errors="coerce")

        # =========================
        # 3. FORMAT ADOBE (FR TEXTE)
        # =========================
        mois_fr = {
            "JAN": "01", "FEV": "02", "FÉV": "02", "MAR": "03", "AVR": "04",
            "MAI": "05", "JUN": "06", "JUI": "07", "AOU": "08", "AOÛ": "08",
            "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12", "DÉC": "12"
        }

        match = re.search(
            r"\b(\d{1,2})[- ](JAN|FEV|FÉV|MAR|AVR|MAI|JUN|JUI|AOU|AOÛ|SEP|OCT|NOV|DEC|DÉC)[- ](20\d{2})\b",
            texte,
            flags=re.IGNORECASE
        )

        if match:
            jour = match.group(1).zfill(2)
            mois = mois_fr[match.group(2).upper()]
            annee = match.group(3)
            return pd.to_datetime(f"{annee}-{mois}-{jour}", errors="coerce")

        # =========================
        # 4. BONUS : "Date de facturation"
        # =========================
        match = re.search(
            r"Date de facturation\s*(\d{2}[-./]\d{2}[-./]\d{4}|\d{2}-[A-Z]{3}-\d{4})",
            texte,
            flags=re.IGNORECASE
        )
        if match:
            return pd.to_datetime(match.group(1), dayfirst=True, errors="coerce")

    except Exception:
        return None

    return None

def detecter_devise(texte):
    if texte is None:
        return "EUR"

    texte_min = str(texte).lower()

    if re.search(r"\busd\b|\$", texte_min):
        return "USD"

    if re.search(r"\beur\b|€", texte_min):
        return "EUR"

    return "EUR"


def extraire_numero_depuis_nom_fichier(nom_fichier):
    if not nom_fichier:
        return None

    base = str(nom_fichier)

    patterns = [
        r"(INV\d{6,})",
        r"(DS-ASE-INV-FR-\d{4}-\d+)",
        r"(IEE\d+)",
        r"(EM\d+)",
        r"(BA2C5E23-\d+)",
        r"(FA\d{4,}-\d+)",
        r"(FAC-\d{4}-\d+)",
        r"(UA\d+)",
        r"\b([A-Z]{2,5}[-_]?\d{5,})\b",
        r"(\d{8,})"
    ]

    for pattern in patterns:
        match = re.search(pattern, base, flags=re.IGNORECASE)
        if match:
            return match.group(1).replace("N°", "").strip()

    return None


def extraire_numero_document(texte, nom_fichier=None):
    patterns = [
        r"facture de régularisation du\s+\d{2}/\d{2}/\d{4}\s*n[°o]?\s*([A-Z0-9\-_\/ ]+)",
        r"facture du\s+\d{2}/\d{2}/\d{4}\s*n[°o]?\s*([A-Z0-9\-_\/ ]+)",
        r"numéro de facture\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"facture n[°o]?\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"n[°o]\s*facture\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"invoice\s*#\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"invoice number\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"receipt number\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"transaction no\.?\s*([A-Z0-9\-_\/]+)",
        r"devis n[°o]?\s*[:\-]?\s*([A-Z0-9\-_\/]+)",
        r"\b(FA\d{6,})\b",
        r"\b(FAC-\d{4}-\d+)\b",
        r"\b(UA\d+)\b",
        r"\b([A-Z]{2,5}[-_]?\d{5,})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().replace(" ", "")

    return extraire_numero_depuis_nom_fichier(nom_fichier)


def nettoyer_libelle(libelle):
    if not libelle or pd.isna(libelle):
        return None

    libelle = str(libelle).strip()
    libelle = re.sub(r"\.pdf$", "", libelle, flags=re.IGNORECASE)
    libelle = re.sub(r"[_\-]+", " ", libelle).strip()
    libelle = re.sub(r"\s+", " ", libelle).strip()
    libelle_min = libelle.lower()

    if libelle_min in MOTS_A_IGNORER:
        return None

    if re.fullmatch(r"\d+[a-z]?", libelle_min):
        return None
    if "invoice" in libelle_min or "facture" in libelle_min:
        return None
    if "compta" in libelle_min:
        return None
    if "acomptes" in libelle_min:
        return None
    if "releve" in libelle_min or "relevé" in libelle_min:
        return None

    if re.fullmatch(r"[A-F0-9]{8,}", libelle.replace(" ", "").upper()):
        return None

    if libelle_min in {"jean pons", "pons jean"}:
        return None

    if re.match(r"^(fac|facture|inv|invoice)\b", libelle_min):
        return None

    caracteres_utiles = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", libelle)
    if caracteres_utiles:
        ratio_chiffres = sum(c.isdigit() for c in caracteres_utiles) / len(caracteres_utiles)
        if ratio_chiffres > 0.45:
            return None

    mots = [m for m in re.split(r"\s+", libelle_min) if m]
    if mots and all(m in MOTS_A_IGNORER for m in mots):
        return None

    for cle, valeur in NORMALISATION_LIBELLES.items():
        if cle in libelle_min:
            return valeur

    if len(libelle) > 40:
        return None

    return libelle.upper()


def extraire_fournisseur_depuis_nom_facture(nom_fichier):
    if not nom_fichier:
        return None

    nom = str(nom_fichier).lower().strip()
    nom = re.sub(r"\.pdf$", "", nom, flags=re.IGNORECASE)

    # Mappings directs très fiables
    if "studio87" in nom:
        return "STUDIO87"

    if "rochetaing" in nom or "jeandominique" in nom:
        return "JEAN-DOMINIQUE ROCHETAING"

    if "activaj" in nom:
        return "ACTIVAJ"

    if "23640" in nom:
        return "A WORLD FOR US"

    if nom == "invoice":
        return "FNAC DIRECT"

    if "fr001058" in nom:
        return "MAAVA CONSULTING"

    # nettoyage standard
    nom = nom.replace("_", " ").replace("-", " ")
    nom = re.sub(r"([a-z])fc\d+[a-z0-9]*\b", r"\1", nom)
    nom = re.sub(r"([a-z])fc\b", r"\1", nom)
    nom = re.sub(r"\bfc\d+[a-z0-9]*\b", " ", nom)
    nom = re.sub(r"\bfacture\b", " ", nom)
    nom = re.sub(r"\bfac\b", " ", nom)
    nom = re.sub(r"\binvoice\b", " ", nom)
    nom = re.sub(r"\btrans\b", " ", nom)
    nom = re.sub(r"\bpro\b", " ", nom)
    nom = re.sub(r"\bcsp\b", " ", nom)
    nom = re.sub(r"\bei\b", " ", nom)
    nom = re.sub(r"\bsarl\b", " ", nom)
    nom = re.sub(r"\bactivmedia\b", " ", nom)
    nom = re.sub(r"\bfr\d+\b", " ", nom)
    nom = re.sub(r"\binv\d+\b", " ", nom)
    nom = re.sub(r"\d+", " ", nom)
    nom = re.sub(r"\s+", " ", nom).strip()

    if not nom:
        return None

    nom_compact = re.sub(r"[^a-z0-9]", "", nom)
    if re.fullmatch(r"[a-f0-9]{10,}", nom_compact):
        return None

    mots = [m for m in nom.split() if len(m) > 2]
    if not mots:
        return None

    fournisseur = " ".join(mots[:3]).strip().upper()

    if len(fournisseur) < 3:
        return None
    if re.fullmatch(r"[A-F0-9 ]{6,}", fournisseur):
        return None

    if fournisseur in {"FACTURE", "INVOICE", "CLIENT", "DOCUMENT", "SALES", "ACTIVMEDIA"}:
        return None

    return fournisseur


def determiner_fournisseur(row, texte):
    texte_min = str(texte or "").lower()
    nom_fichier = str(row.get("nom_fichier") or "").lower().strip()
    dossier = str(row.get("fournisseur_ou_client") or "").lower().strip()

    # =========================
    # RÈGLES PRIORITAIRES BASÉES SUR LES PDF RÉELS
    # =========================

    # MAAVA CONSULTING
    if "maava consulting" in texte_min:
        return "MAAVA CONSULTING"

    if (
        "jean pons - st" in texte_min
        or "destinataire:\njean pons" in texte_min
        or "destinataire: jean pons" in texte_min
    ):
        pass

    # A WORLD FOR US / DIGIFORMA
    if "a world for us" in texte_min or "digiforma" in texte_min:
        return "A WORLD FOR US"

    # FNAC DIRECT
    if "fnac direct" in texte_min or "fnac.com" in texte_min or "fnac" in texte_min:
        return "FNAC DIRECT"

    # HELLOWORK
    if "hellowork" in texte_min:
        return "HELLOWORK"

    # ROCHEtaing
    if "rochetaing" in texte_min or "rochetaing" in nom_fichier or "jeandominique" in nom_fichier:
        return "JEAN-DOMINIQUE ROCHETAING"

    # STUDIO87 / Leslie Doyhamboure
    if (
        "studiographique87" in texte_min
        or "leslie doyhamboure" in texte_min
        or "studio87" in nom_fichier
    ):
        return "STUDIO87"

    # NIKOLOVA
    if "nikolova rositsa" in texte_min:
        return "NIKOLOVA ROSITSA"

    # ACTIVAJ
    if "activaj" in nom_fichier or "activaj" in texte_min:
        return "ACTIVAJ"

    # =========================
    # FOURNISSEURS DÉJÀ BIEN GÉRÉS
    # =========================
    priorites_texte = [
        ("apple distribution", "APPLE"),
        ("apple", "APPLE"),
        ("micrologik", "MICROLOGIK"),
        ("foxway", "FOXWAY"),
        ("nespresso", "NESPRESSO"),
        ("rossini", "ROSSINI"),
        ("pedro sas", "PEDRO SAS"),
        ("delicity", "PEDRO SAS"),
        ("airbnb", "AIRBNB"),
        ("oviala", "OVIALA"),
        ("icasque", "ICASQUE"),
        ("papilles formation", "PAPILLES FORMATION"),
        ("pépite", "PEPITE"),
        ("pepite", "PEPITE"),
        ("adobe systems", "ADOBE"),
        ("adobe", "ADOBE"),
        ("zoom", "ZOOM"),
        ("amazon", "AMAZON"),
        ("google", "GOOGLE"),
        ("microsoft", "MICROSOFT"),
        ("free", "FREE"),
        ("orange", "ORANGE"),
        ("edf", "EDF"),
        ("fedex", "FEDEX"),
        ("tnt", "FEDEX"),
        ("openai", "OPENAI"),
        ("chatgpt", "OPENAI"),
        ("make", "MAKE"),
        ("celonis", "MAKE"),
        ("lab ac30", "LAB"),
        ("sarl l.a.b", "LAB"),
        ("lab renovation", "LAB"),
        ("bureau.lab06", "LAB"),
        ("wprocket", "WPROCKET"),
        ("ecri", "ECRI"),
        ("entrarts", "ENTRARTS"),
        ("grasa", "GRASA"),
        ("randstad", "RANDSTAD"),
        ("chu de nice", "CHU DE NICE"),
        ("light sword", "LIGHT SWORD PROD"),
        ("art et or", "ART ET OR"),
        ("art ero", "ART ET OR"),
        ("rt rénovation", "RT RENOVATION"),
        ("r.t rénovation", "RT RENOVATION"),
        ("rt renovation", "RT RENOVATION"),
        ("r.t renovation", "RT RENOVATION"),
    ]

    for cle, valeur in priorites_texte:
        if cle in texte_min:
            return valeur

    priorites_nom = [
        ("studio87", "STUDIO87"),
        ("rochetaing", "JEAN-DOMINIQUE ROCHETAING"),
        ("jeandominique", "JEAN-DOMINIQUE ROCHETAING"),
        ("activaj", "ACTIVAJ"),
        ("apple", "APPLE"),
        ("micrologik", "MICROLOGIK"),
        ("foxway", "FOXWAY"),
        ("nespresso", "NESPRESSO"),
        ("rossini", "ROSSINI"),
        ("pedro", "PEDRO SAS"),
        ("delicity", "PEDRO SAS"),
        ("airbnb", "AIRBNB"),
        ("oviala", "OVIALA"),
        ("icasque", "ICASQUE"),
        ("papilles", "PAPILLES FORMATION"),
        ("pepite", "PEPITE"),
        ("adobe", "ADOBE"),
        ("zoom", "ZOOM"),
        ("amazon", "AMAZON"),
        ("google", "GOOGLE"),
        ("microsoft", "MICROSOFT"),
        ("orange", "ORANGE"),
        ("edf", "EDF"),
        ("lab", "LAB"),
        ("wprocket", "WPROCKET"),
        ("ecri", "ECRI"),
        ("entrarts", "ENTRARTS"),
        ("grasa", "GRASA"),
        ("randstad", "RANDSTAD"),
        ("chu de nice", "CHU DE NICE"),
        ("fnac", "FNAC DIRECT"),
        ("maava", "MAAVA CONSULTING"),
        ("23640", "A WORLD FOR US"),
    ]

    for cle, valeur in priorites_nom:
        if cle in nom_fichier:
            return valeur

    for cle, valeur in priorites_nom:
        if cle in dossier and valeur != "ACTIVMEDIA":
            return valeur

    # =========================
    # BLOQUER LES FAUX FOURNISSEURS
    # =========================
    faux = {
        "ACTIVMEDIA",
        "FACTURES CLIENT ACCOMPTES",
        "FACTURES FOURNISSEURS CLIENTS ACCOMPTES",
        "2022 FACTURES",
        "RELEVES SARL",
        "RELEVES",
        "RELEVE",
        "SARL",
        "SALES",
        "INVOICE",
        "FACTURE",
        "DOCUMENT",
        "CLIENT",
    }

    if "releve" in dossier or "relevé" in dossier:
        return None

    dossier_clean = nettoyer_libelle(row.get("fournisseur_ou_client"))
    if dossier_clean and "COMPTA" not in dossier_clean and dossier_clean not in faux:
        return dossier_clean

    fournisseur_facture = extraire_fournisseur_depuis_nom_facture(row.get("nom_fichier"))
    if fournisseur_facture and fournisseur_facture not in faux:
        return fournisseur_facture

    nom_clean = nettoyer_libelle(row.get("nom_fichier"))
    if nom_clean and "COMPTA" not in nom_clean and nom_clean not in faux:
        if nom_clean not in {"FACTURE", "INVOICE", "CLIENT", "DOCUMENT", "SALES", "ACTIVMEDIA"}:
            return nom_clean

    return None


def est_document_hors_perimetre(row):
    chemin = str(row.get("chemin_fichier") or "").lower().replace("\\", "/")
    nom_fichier = str(row.get("nom_fichier") or "").lower()
    fournisseur_client = str(row.get("fournisseur_ou_client") or "").lower()

    texte_test = f"{chemin} {nom_fichier} {fournisseur_client}"

    motifs_hors_perimetre = [
        "/sci/",
        "sci/",
        "/facture clients/",
        "/factures clients/",
        "/tva jan _ avril facture clients/",
        "/tva mai _sept facture clients/",
        "/tva oct _dec facture clients/",
        "/modele tva xxx_ xxx facture clients/",
        "/tva facture clients/",
        "facture clients",
        "factures clients",
        "tva jan",
        "tva mai",
        "tva oct",
        "modele tva",
        "/releve annee",
        "/releves",
        "/relevé",
        "/recap compta",
        "/compta janvier",
        "/compta fevrier",
        "/compta mars",
        "/compta avril",
        "/compta mai",
        "/compta juin",
        "/compta juillet",
        "/compta aout",
        "/compta septembre",
        "/compta octobre",
        "/compta novembre",
        "/compta decembre",
    ]

    return any(motif in texte_test for motif in motifs_hors_perimetre)


def extraire_montant_edf(texte):
    texte_min = texte.lower()

    if re.search(r"en votre faveur", texte_min, flags=re.IGNORECASE):
        return None

    patterns = [
        r"montant total à payer\s*\(ttc\)\s+(-?\d[\d\s.,]+)\s*(€|eur)",
        r"montant total\s+(-?\d[\d\s.,]+)\s*(€|eur)\s+ttc",
        r"facture ttc\s+(-?\d[\d\s.,]+)\s*(€|eur)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_free(texte):
    texte_min = texte.lower()

    patterns = [
        r"total facture\s+([\d\.,]+)\s*€",
        r"somme à payer.*?([\d\.,]+)\s*€",
        r"montant ttc\s+([\d\.,]+)\s*€",
        r"montant prélevé.*?([\d\.,]+)\s*€",
        r"total\s+[\d\.,]+€\s+([\d\.,]+)\s*€"
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and 0 < val < 1000:
                return val

    return None


def extraire_montant_amazon(texte):
    texte_min = texte.lower()

    patterns = [
        r"total à payer\s*(-?\d[\d\s.,]+)\s*€",
        r"facture total\s*(-?\d[\d\s.,]+)\s*€",
        r"total general ttc\s*(eur)?\s*([\d,\.]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            groupes = [g for g in match.groups() if g is not None]
            for g in reversed(groupes):
                if re.search(r"\d", g):
                    val = convertir_montant_vers_float(g)
                    if val is not None and val > 0:
                        return val

    return None


def extraire_montant_transport(texte):
    texte_min = texte.lower()

    patterns = [
        r"net à payer\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"montant net à payer\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"total ttc\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_saas(texte):
    texte_min = texte.lower()

    patterns = [
        r"invoice total\s*(eur|usd|\$|€)?\s*(-?\d[\d\s.,]+)",
        r"total\s*\(including.*?\)\s*(eur|usd|\$|€)?\s*(-?\d[\d\s.,]+)",
        r"total\(eur\)\s*(-?\d[\d\s.,]+)",
        r"total\s*\(eur\)\s*(-?\d[\d\s.,]+)",
        r"total billed.*?(-?\d[\d\s.,]+)",
        r"amount due\s*(\$|usd|eur|€)?\s*(-?\d[\d\s.,]+)",
        r"total facturé.*?(-?\d[\d\s.,]+)",
        r"total \(eur\)\s*([0-9.,]+)",
        r"total ttc\s*([\d\.,]+)\s*€?",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL)
        if match:
            groupes = [g for g in match.groups() if g is not None]
            for g in reversed(groupes):
                if re.search(r"\d", g):
                    val = convertir_montant_vers_float(g)
                    if val is not None and abs(val) > 0:
                        return abs(val)

    return None


def extraire_montant_prestation(texte):
    texte_min = texte.lower()

    patterns = [
        r"montant total ttc\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"total ttc\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"montant ttc\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"net à payer\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"net a payer\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"à payer\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"montant total ht\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"total ht\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"prestations ht\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"total\s*[:\-]?\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"100,00%\s+soit\s+(-?\d[\d\s.,]+)\s*€\s+à payer",
        r"prix total \(ttc\)\s*eur\s*([\d\.,]+)",
    ]

    candidats = []

    for pattern in patterns:
        for match in re.finditer(pattern, texte_min, flags=re.IGNORECASE):
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                candidats.append(val)

    if candidats:
        return sorted(candidats, key=lambda x: abs(x), reverse=True)[0]

    return None


def extraire_montant_generique(texte):
    texte_min = texte.lower()

    patterns = [
        r"total general ttc\s*(eur)?\s*([0-9][\d\., ]+)",
        r"total général ttc\s*(eur)?\s*([0-9][\d\., ]+)",
        r"montant net à payer\s*[:\-]?\s*([0-9][\d\., ]+)",
        r"net à payer\s*[:\-]?\s*([0-9][\d\., ]+)",
        r"total ttc\s*[:\-]?\s*([0-9][\d\., ]+)",
        r"total ht\s*[:\-]?\s*([0-9][\d\., ]+)",
        r"montant total à payer[^\d\-]{0,40}([0-9][\d\s.,]+)\s*(€|eur|\$|usd)",
        r"facture ttc[^\d\-]{0,40}([0-9][\d\s.,]+)\s*(€|eur|\$|usd)",
        r"amount due[^\d\-]{0,40}([0-9][\d\s.,]+)\s*(€|eur|\$|usd)",
        r"montant dû[^\d\-]{0,20}([0-9][\d\s.,]+)\s*(€|eur)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL)
        if match:
            groupes = [g for g in match.groups() if g is not None]
            for g in reversed(groupes):
                if re.search(r"\d", str(g)):
                    val = convertir_montant_vers_float(g)
                    if val is not None and 0 < val < 100000:
                        return val

    matches = re.findall(r"([0-9]{1,6}[.,][0-9]{2})\s*(€|eur)", texte_min)

    if matches:
        valeurs = []
        for m in matches:
            val = convertir_montant_vers_float(m[0])
            if val is not None and 0 < val < 100000:
                valeurs.append(val)

        if valeurs:
            return max(valeurs, key=abs)

    return None


def extraire_montant_nespresso(texte):
    texte_min = texte.lower()

    patterns = [
        r"total facture ttc\s*€?\s*[:\-]?\s*([\d\.,]+)",
        r"total ttc\s*€?\s*[:\-]?\s*([\d\.,]+)",
        r"total ttc €\s*[:\-]?\s*([\d\.,]+)",
        r"total facture ht €\s*[:\-]?\s*([\d\.,]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_foxway(texte):
    texte_min = texte.lower()

    patterns = [
        r"gross total\s*([\d\.,]+)",
        r"net total\s*([\d\.,]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_apple(texte):
    texte_min = texte.lower()

    patterns = [
        r"prix total \(ttc\)\s*eur\s*([\d\.,]+)",
        r"prix total \(ttc\)\s*([\d\.,]+)",
        r"total \(ttc\)\s*eur\s*([\d\.,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_airbnb(texte):
    texte_min = texte.lower()

    patterns = [
        r"montant payé \(eur\)\s*([\d\.,]+)",
        r"total \(eur\)\s*([\d\.,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None


def extraire_montant_micrologik(texte):
    texte_min = texte.lower()

    patterns = [
        r"total\s*([\d\.,]+)\s*€",
        r"prix total\s*([\d\.,]+)\s*€",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and val > 0:
                return val

    return None

def extraire_montant_edf(texte):
    texte_min = texte.lower()

    if re.search(r"en votre faveur", texte_min, flags=re.IGNORECASE):
        return None

    patterns = [
        r"montant total à payer\s*\(ttc\)\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"facture ttc\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"vous serez prélevé d['’]un montant de\s*(-?\d[\d\s.,]+)\s*(€|eur)",
        r"total ttc facturés sur la période\s*(-?\d[\d\s.,]+)\s*(€|eur)",
    ]

    for pattern in patterns:
        match = re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL)
        if match:
            val = convertir_montant_vers_float(match.group(1))
            if val is not None and 0 < val < 10000:
                return val

    return None


def extraire_montant(texte, fournisseur=None):
    texte_min = texte.lower()
    fournisseur = (fournisseur or "").upper()

    if "edf" in texte_min or fournisseur == "EDF":
        val = extraire_montant_edf(texte)
        if val is not None:
            return val

    if "free" in texte_min or fournisseur == "FREE":
        val = extraire_montant_free(texte)
        if val is not None:
            return val

    if "amazon" in texte_min or fournisseur == "AMAZON" or fournisseur == "FNAC DIRECT" or fournisseur == "DARTY":
        val = extraire_montant_amazon(texte)
        if val is not None:
            return val

    if "apple" in texte_min or fournisseur == "APPLE":
        val = extraire_montant_apple(texte)
        if val is not None:
            return val

    if "airbnb" in texte_min or fournisseur == "AIRBNB":
        val = extraire_montant_airbnb(texte)
        if val is not None:
            return val

    if "micrologik" in texte_min or fournisseur == "MICROLOGIK":
        val = extraire_montant_micrologik(texte)
        if val is not None:
            return val

    if any(m in texte_min for m in ["zoom", "adobe", "invoice total", "amount due"]) or fournisseur in {"ZOOM", "ADOBE", "MAKE", "OPENAI", "GOOGLE", "MICROSOFT"}:
        val = extraire_montant_saas(texte)
        if val is not None:
            return val

    if any(m in texte_min for m in ["fedex", "tnt", "transport de", "ttc eur"]) or fournisseur == "FEDEX":
        val = extraire_montant_transport(texte)
        if val is not None:
            return val

    if "nespresso" in texte_min or fournisseur == "NESPRESSO":
        val = extraire_montant_nespresso(texte)
        if val is not None:
            return val

    if "foxway" in texte_min or fournisseur == "FOXWAY":
        val = extraire_montant_foxway(texte)
        if val is not None:
            return val

    val = extraire_montant_prestation(texte)
    if val is not None:
        return val

    val = extraire_montant_generique(texte)
    if val is not None and val < 100000:
        return val

    return None


def determiner_categorie(fournisseur, texte):
    base = ((fournisseur or "") + " " + (texte[:4000] if texte else "")).lower()
    fournisseur = (fournisseur or "").upper().strip()

    # =========================
    # RÈGLES PRIORITAIRES PAR FOURNISSEUR
    # =========================

    if fournisseur == "INTERNE":
        return "interne"

    if fournisseur in {
        "JEAN-DOMINIQUE ROCHETAING",
        "STUDIO87",
        "MAAVA CONSULTING",
        "A WORLD FOR US",
        "DIGIFORMA",
        "ACTIVAJ",
        "ART ET OR",
        "CHU DE NICE",
        "KITEMONA BRIAN",
        "RANDSTAD",
        "ENTRARTS",
        "GUERIN NOEL",
        "PION EMMANUEL",
        "DONEVA SILVIYA",
        "CHARPENTIER CLOE",
        "RAVI CORALINE",
        "THIEBAUX JOHANNA",
        "JOELLE BERNAY HARTMANN",
        "NIKOLOVA ROSITSA",
        "COM INTO BLOSSOM",
        "PE CONSULTANT SEO",
        "LAURA MEUNIER",
        "PELLEGRIN ENRICK SEO",
        "MEUNIER MOUCHVOZ LAURA",
        "PEPITE",
        "ECRI",
        "JULIAN GUILLEN",
        "BRAINYUP",
        "ARNAUD DEGRAVE",
        "FRANCOIS MAESTRATI",
    }:
        return "prestations"

    if fournisseur in {
        "FNAC DIRECT",
        "APPLE",
        "AMAZON",
        "FOXWAY",
        "OVIALA",
        "ICASQUE",
        "DARTY",
        "THOMANN",
        "MABEX",
        "XIAOMI",
        "XIAOMI PAD",
        "MICROLOGIK",
    }:
        return "materiel_achats"

    if fournisseur in {
        "GOOGLE",
        "ADOBE",
        "OPENAI",
        "MAKE",
        "MICROSOFT",
        "ZOOM",
        "WPROCKET",
        "ELEPHORM",
        "FASTRP",
        "OVH",
        "YAMM",
    }:
        return "logiciels_abonnements"

    if fournisseur in {"HELLOWORK", "FREE", "ORANGE", "SFR"}:
        return "telecom"

    if fournisseur in {"EDF", "ENGIE"}:
        return "energie"

    if fournisseur in {"ROSSINI", "PEDRO SAS", "NESPRESSO"}:
        return "restauration"

    if fournisseur in {"FEDEX", "SNCF"}:
        return "transport"

    if fournisseur in {"RT RENOVATION", "LAB"}:
        return "travaux"

    # =========================
    # RÈGLES PAR CONTENU
    # =========================

    if any(m in base for m in ["edf", "engie", "electricite", "électricité", "gaz", "tarif bleu"]):
        return "energie"

    if any(m in base for m in [
        "formation", "seo", "référencement", "referencement", "wordpress",
        "ux/ui", "webdesigner", "backlink", "prestation", "prestations",
        "consulting", "guillen", "degrave", "maestrati", "brainyup"
    ]):
        return "prestations"

    if any(m in base for m in [
        "abonnement", "leads", "maformation", "fourniture de leads",
        "internet", "fibre", "telecom", "télécom"
    ]):
        return "telecom"

    if any(m in base for m in [
        "fnac", "tv samsung", "samsung", "ordinateur", "casque",
        "commande", "materiel", "matériel", "thomann", "mabex",
        "darty", "xiaomi", "micro-ordinateur", "ipad"
    ]):
        return "materiel_achats"

    if any(m in base for m in [
        "google", "adobe", "openai", "chatgpt", "zoom", "make",
        "microsoft", "logiciel", "saas", "digiforma", "elephorm",
        "yamm", "talarian", "mail merge"
    ]):
        return "logiciels_abonnements"

    if any(m in base for m in [
        "travaux", "carrelage", "peinture", "chantier",
        "rénovation", "renovation", "pose"
    ]):
        return "travaux"

    if any(m in base for m in [
        "fedex", "tnt", "transport", "expédition", "expedition",
        "colis", "shipment", "express"
    ]):
        return "transport"

    if any(m in base for m in [
        "restaurant", "brasserie", "capsule", "café", "cafe", "nespresso"
    ]):
        return "restauration"

    if any(m in base for m in [
        "assurance", "mutuelle", "garantie décennale",
        "garantie decennale", "rc pro"
    ]):
        return "assurance"

    if any(m in base for m in ["loyer", "location", "bail"]):
        return "loyer"

    # =========================
    # FALLBACK INTELLIGENT
    # =========================

    f = fournisseur

    if any(x in f for x in ["ELEPHORM", "DIGIFORMA", "WPROCKET", "OVH", "FASTRP", "YAMM"]):
        return "logiciels_abonnements"

    if any(x in f for x in [
        "CONSULTING", "SEO", "FORMATION",
        "COM INTO BLOSSOM",
        "PE CONSULTANT SEO",
        "LAURA MEUNIER",
        "STUDIO87",
        "PELLEGRIN",
        "MEUNIER",
        "PEPITE",
        "GUILLEN",
        "DEGRAVE",
        "MAESTRATI",
        "BRAINYUP",
        "ECRI",
    ]):
        return "prestations"

    if any(x in f for x in [
        "FNAC", "DARTY", "LDLC", "BOULANGER",
        "THOMANN", "MABEX", "XIAOMI", "MICROLOGIK"
    ]):
        return "materiel_achats"

    if any(x in f for x in ["FREE", "SFR", "ORANGE"]):
        return "telecom"

    return "autre"


def determiner_type_piece(texte, type_document_initial):
    texte_min = texte.lower()

    if "receipt" in texte_min or "date paid" in texte_min or "amount paid" in texte_min or "reçu" in texte_min or "recu" in texte_min:
        return "recu"

    if "invoice" in texte_min or "facture" in texte_min or "transaction no" in texte_min:
        return "facture"

    if re.search(r"\bdevis\b", texte_min):
        return "devis"

    return type_document_initial


def document_a_exclure(nom_fichier, texte):
    texte_min = (texte or "").lower()

    motifs = [
        "bilan actif",
        "bilan passif",
        "compte de résultat",
        "compte de resultat",
        "liasse fiscale",
        "balance générale",
        "balance generale",
        "journal centralisateur",
        "états financiers",
        "etats financiers",
        "annexe au bilan",
        "edition fiscale",
    ]

    return any(m in texte_min for m in motifs)


def conserver_document(type_piece, a_exclure):
    if a_exclure:
        return False
    return type_piece in {"facture", "devis", "recu"}


def est_depense_reelle(type_piece, montant, categorie, fournisseur):
    if type_piece not in {"facture", "recu"}:
        return False
    if montant is None or pd.isna(montant):
        return False
    if float(montant) <= 0:
        return False
    if fournisseur == "INTERNE":
        return False
    return True


def pdf_est_multi_facture(nom_fichier, texte_complet):
    nom = str(nom_fichier or "").lower()
    texte_min = (texte_complet or "").lower()

    if "adobe" in nom:
        return True
    if texte_min.count("date de facturation") >= 2 and "adobe systems" in texte_min:
        return True

    return False


def traiter_un_bloc(row, chemin_pdf, nom_fichier, texte, page_num=None, exclu_hors_perimetre=False):
    a_exclure = document_a_exclure(nom_fichier, texte) or exclu_hors_perimetre

    fournisseur = determiner_fournisseur(row, texte)

    # 1. Extraction date classique depuis le texte PyMuPDF
    date_document = extraire_date(texte, nom_fichier=nom_fichier)

    # 2. Fallback pdfplumber si date non trouvée
    if date_document is None:
        date_document_pdf = extraire_date_depuis_pdf({
            "chemin_fichier": chemin_pdf
        })

        if pd.notna(date_document_pdf):
            date_document = date_document_pdf.strftime("%Y-%m-%d")

    numero_document = extraire_numero_document(texte, nom_fichier=nom_fichier)
    devise = detecter_devise(texte)
    montant_ttc = extraire_montant(texte, fournisseur=fournisseur)
    categorie = determiner_categorie(fournisseur, texte)
    type_piece = determiner_type_piece(texte, row.get("type_document"))

    a_conserver = conserver_document(type_piece, a_exclure)

    # 🔥 NOUVEAU
    type_flux = determiner_type_flux(texte, fournisseur, row)

    # 🔥 LOGIQUE DEPENSE CORRIGÉE
    est_depense = (
        type_piece in {"facture", "recu"}
        and montant_ttc is not None
        and float(montant_ttc) > 0
        and not a_exclure
        and type_flux == "depense"
    )

    return {
        "chemin_fichier": chemin_pdf,
        "nom_fichier": nom_fichier,
        "page": page_num,
        "annee": row.get("annee"),
        "type_document_source": row.get("type_document"),
        "type_piece": type_piece,
        "fournisseur": fournisseur,
        "date_document": date_document,
        "numero_document": numero_document,
        "montant_ttc": montant_ttc,
        "devise": devise,
        "categorie_depense": categorie,
        "type_flux": type_flux,
        "a_exclure": a_exclure,
        "a_conserver": a_conserver,
        "est_depense": est_depense,
        "motif_exclusion": "hors_perimetre" if exclu_hors_perimetre else None,
        "statut_extraction_metier": "ok"
    }


def determiner_type_flux(texte, fournisseur, row=None):
    texte_min = str(texte or "").lower()
    nom_fichier = str(row.get("nom_fichier", "")).lower() if row is not None else ""
    dossier = str(row.get("fournisseur_ou_client", "")).lower() if row is not None else ""
    fournisseur_up = (fournisseur or "").upper().strip()

    # =========================
    # HORS PÉRIMÈTRE
    # =========================
    if "sci" in dossier:
        return "hors_perimetre"

    # =========================
    # DÉPENSES PRIORITAIRES
    # Important : EDF contient aussi "ACTIVMEDIA GLOBAL SYNERGY"
    # car Activmedia est le client. Donc EDF doit passer AVANT les recettes.
    # =========================
    if (
        fournisseur_up == "EDF"
        or "edf-sa" in texte_min
        or "edf sa" in texte_min
        or "facture edf" in nom_fichier
        or "particulier.edf.fr" in nom_fichier
    ):
        return "depense"

    fournisseurs_depense = {
        "ADOBE", "APPLE", "AMAZON", "EDF", "FREE", "FOXWAY", "NESPRESSO",
        "AIRBNB", "MICROLOGIK", "GOOGLE", "OPENAI", "MICROSOFT", "MAKE",
        "ZOOM", "FNAC DIRECT", "HELLOWORK", "MAAVA CONSULTING",
        "A WORLD FOR US", "FEDEX", "ORANGE", "OVIALA", "ICASQUE",
        "PAPILLES FORMATION", "PEPITE", "ROSSINI", "PEDRO SAS",
        "RT RENOVATION", "LAB",
        "JULIAN GUILLEN", "BRAINYUP", "ARNAUD DEGRAVE",
        "FRANCOIS MAESTRATI", "THOMANN", "MABEX", "DARTY",
        "YAMM", "ECRI", "COM INTO BLOSSOM", "PE CONSULTANT SEO",
        "LAURA MEUNIER", "ELEPHORM", "DIGIFORMA", "XIAOMI",
        "SNCF", "STUDIO87", "JEAN-DOMINIQUE ROCHETAING",
        "JIMMY FAIRLY", "APSI", "WEEZEVENT", "MHR CONSULT", "IKEA",
    }

    # =========================
    # CAS SPÉCIAL : FACTURES ACTIVMEDIA → ROCHEtaing = RECETTE
    # =========================
    if (
        "rochetaing" in texte_min
        and "activmedia global synergy" in texte_min
    ):
        return "recette"

    if (
        "facture_" in nom_fichier 
        and "rochetaing" in nom_fichier
        and "activmedia" in nom_fichier
    ):
        return "recette"

    if "activmedia-global-synergy" in nom_fichier:
        return "recette"

    if fournisseur_up in fournisseurs_depense:
        return "depense"

    # =========================
    # RECETTES : factures émises par ACTIVMEDIA
    # On ne met PAS juste "activmedia global synergy",
    # car beaucoup de factures fournisseurs l'ont comme client.
    # =========================
    patterns_recette = [
        r"émetteur\s*:?\s*activ ?media",
        r"emetteur\s*:?\s*activ ?media",
        r"vendeur\s*:?\s*activ ?media",
        r"prestataire\s*:?\s*activ ?media",
        r"société\s*:?\s*activ ?media",
        r"societe\s*:?\s*activ ?media",
        r"organisme de formation\s*:?\s*activ ?media",
        r"facture émise par\s+activ ?media",
        r"facture emise par\s+activ ?media",

        # Cas type facture client / formation :
        # Activmedia apparaît en haut/émetteur et le client est plus bas.
        r"activmedia global synergy.*?(client|destinataire|bénéficiaire|beneficiaire)\s*:?",
    ]

    for pattern in patterns_recette:
        if re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL):
            return "recette"

    # =========================
    # DÉPENSES : Activmedia est client / destinataire
    # =========================
    patterns_depense = [
        r"facturé à\s+.*activ ?media",
        r"facture à\s+.*activ ?media",
        r"client\s*:?\s+.*activ ?media",
        r"destinataire\s*:?\s+.*activ ?media",
        r"acheteur\s*:?\s+.*activ ?media",
        r"bill to\s*:?\s+.*activ ?media",
        r"billed to\s*:?\s+.*activ ?media",
        r"jean pons.*activ ?media",
        r"\bactivmedia\b.*(?:7 rue henry de cessole|132 corniche fleurie)",
    ]

    for pattern in patterns_depense:
        if re.search(pattern, texte_min, flags=re.IGNORECASE | re.DOTALL):
            return "depense"

    # =========================
    # Recettes probables via dossier / nom fichier
    # =========================
    if any(x in nom_fichier for x in ["facture_client", "facture client", "client_", "vente_"]):
        return "recette"

    if any(x in dossier for x in ["facture client", "factures clients", "clients"]):
        return "recette"

    # =========================
    # Dernier fallback
    # =========================
    return "depense"


def est_depense_reelle(type_piece, montant, categorie, fournisseur, type_flux="depense"):
    if type_piece not in {"facture", "recu"}:
        return False
    if montant is None or pd.isna(montant):
        return False
    if float(montant) <= 0:
        return False
    if type_flux != "depense":
        return False
    return True


def traiter_documents():
    inventaire = pd.read_csv(INVENTAIRE_CSV)
    inventaire = inventaire[inventaire["pdf_texte_detecte"] == True].copy()

    resultats = []

    total = len(inventaire)
    print(f"Documents texte à traiter : {total}")

    for idx, (_, row) in enumerate(inventaire.iterrows(), start=1):
        chemin_pdf = row["chemin_fichier"]
        nom_fichier = row.get("nom_fichier")
        exclu_hors_perimetre = est_document_hors_perimetre(row)

        print(f"[{idx}/{total}] {chemin_pdf}")

        try:
            doc = fitz.open(chemin_pdf)
        except Exception:
            resultats.append({
                "chemin_fichier": chemin_pdf,
                "nom_fichier": nom_fichier,
                "page": None,
                "annee": row.get("annee"),
                "type_document_source": row.get("type_document"),
                "type_piece": row.get("type_document"),
                "fournisseur": nettoyer_libelle(row.get("fournisseur_ou_client")),
                "date_document": None,
                "numero_document": extraire_numero_depuis_nom_fichier(nom_fichier),
                "montant_ttc": None,
                "devise": None,
                "categorie_depense": "autre",
                "a_exclure": True if exclu_hors_perimetre else False,
                "a_conserver": False,
                "est_depense": False,
                "motif_exclusion": "hors_perimetre" if exclu_hors_perimetre else None,
                "statut_extraction_metier": "ouverture_pdf_impossible"
            })
            continue

        textes_pages = []
        for i, page in enumerate(doc):
            if i >= 20:
                break
            textes_pages.append(nettoyer_texte(page.get_text("text")))

        texte_complet = nettoyer_texte("\n".join([t for t in textes_pages if t]))

        if not texte_complet:
            doc.close()
            resultats.append({
                "chemin_fichier": chemin_pdf,
                "nom_fichier": nom_fichier,
                "page": None,
                "annee": row.get("annee"),
                "type_document_source": row.get("type_document"),
                "type_piece": row.get("type_document"),
                "fournisseur": nettoyer_libelle(row.get("fournisseur_ou_client")),
                "date_document": None,
                "numero_document": extraire_numero_depuis_nom_fichier(nom_fichier),
                "montant_ttc": None,
                "devise": None,
                "categorie_depense": "autre",
                "a_exclure": True if exclu_hors_perimetre else False,
                "a_conserver": False,
                "est_depense": False,
                "motif_exclusion": "hors_perimetre" if exclu_hors_perimetre else None,
                "statut_extraction_metier": "texte_vide"
            })
            continue

        multi_facture = pdf_est_multi_facture(nom_fichier, texte_complet)

        if multi_facture:
            for i, texte in enumerate(textes_pages):
                if not texte:
                    continue

                ligne = traiter_un_bloc(
                    row=row,
                    chemin_pdf=chemin_pdf,
                    nom_fichier=nom_fichier,
                    texte=texte,
                    page_num=i + 1,
                    exclu_hors_perimetre=exclu_hors_perimetre
                )
                resultats.append(ligne)

                if ligne["fournisseur"] is None:
                    print(f"⚠️ Fournisseur manquant : {nom_fichier} | page {i + 1}")
                if ligne["montant_ttc"] is None and ligne["a_conserver"]:
                    print(f"⚠️ Montant manquant : {nom_fichier} | page {i + 1}")
                if ligne["date_document"] is None and ligne["a_conserver"]:
                    print(f"⚠️ Date manquante : {nom_fichier} | page {i + 1}")
        else:
            ligne = traiter_un_bloc(
                row=row,
                chemin_pdf=chemin_pdf,
                nom_fichier=nom_fichier,
                texte=texte_complet,
                page_num=None,
                exclu_hors_perimetre=exclu_hors_perimetre
            )
            resultats.append(ligne)

            if ligne["fournisseur"] is None:
                print(f"⚠️ Fournisseur manquant : {nom_fichier}")
            if ligne["montant_ttc"] is None and ligne["a_conserver"]:
                print(f"⚠️ Montant manquant : {nom_fichier}")
            if ligne["date_document"] is None and ligne["a_conserver"]:
                print(f"⚠️ Date manquante : {nom_fichier}")

        doc.close()

    df = pd.DataFrame(resultats)

    chemins = df["chemin_fichier"].astype(str).str.lower()

    masque_clients = (
        chemins.str.contains("2022_clients", regex=False, na=False)
        | chemins.str.contains("2023_clients", regex=False, na=False)
        | chemins.str.contains("2024_clients", regex=False, na=False)
        | chemins.str.contains("2025_clients", regex=False, na=False)
        | chemins.str.contains("facture clients", regex=False, na=False)
        | chemins.str.contains("factures clients", regex=False, na=False)
        | chemins.str.contains("facture client", regex=False, na=False)
        | chemins.str.contains("factures client", regex=False, na=False)
        | (
            chemins.str.contains("tva", regex=False, na=False)
            & chemins.str.contains("client", regex=False, na=False)
        )
    )

    df.loc[masque_clients, "a_exclure"] = True
    df.loc[masque_clients, "a_conserver"] = False
    df.loc[masque_clients, "est_depense"] = False
    df.loc[masque_clients, "type_flux"] = "recette"
    df.loc[masque_clients, "motif_exclusion"] = "facture_client"

    print("Clients détectés et exclus :", masque_clients.sum())

    df.to_csv(OUTPUT_ALL, index=False, encoding="utf-8-sig")

    df_main = df[df["a_conserver"] == True].copy()
    df_main.to_csv(OUTPUT_MAIN, index=False, encoding="utf-8-sig")

    df_expenses = df[
        (df["est_depense"] == True)
        & (df["type_flux"] == "depense")
    ].copy()
    df_expenses.to_csv(OUTPUT_EXPENSES, index=False, encoding="utf-8-sig")
    df_expenses.to_csv(OUTPUT_EXPENSES_AVANT_NETTOYAGE, index=False, encoding="utf-8-sig")

    df_excluded = df[df["a_exclure"] == True].copy()
    df_excluded.to_csv(OUTPUT_EXCLUDED, index=False, encoding="utf-8-sig")

    print("\nExtraction terminée.")
    print(f"Fichier complet : {OUTPUT_ALL}")
    print(f"Factures + devis + reçus conservés : {OUTPUT_MAIN}")
    print(f"Dépenses réelles : {OUTPUT_EXPENSES}")
    print(f"Dépenses avant nettoyage : {OUTPUT_EXPENSES_AVANT_NETTOYAGE}")
    print(f"Documents exclus : {OUTPUT_EXCLUDED}")

    print("\nRésumé :")
    print(f"Total lignes extraites : {len(df)}")
    print(f"Documents conservés : {len(df_main)}")
    print(f"Dépenses réelles : {len(df_expenses)}")
    print(f"Documents exclus : {len(df_excluded)}")

    print("\nTaux de dates trouvées :")
    print(round(df_main["date_document"].notna().mean() * 100, 2), "%")

    print("\nTaux de montants trouvés :")
    print(round(df_main["montant_ttc"].notna().mean() * 100, 2), "%")

    print("\nTaux de numéros trouvés :")
    print(round(df_main["numero_document"].notna().mean() * 100, 2), "%")

    print("\nRépartition types :")
    print(df_main["type_piece"].value_counts(dropna=False))

    print("\nRépartition catégories :")
    print(df_expenses["categorie_depense"].value_counts(dropna=False))


if __name__ == "__main__":
    traiter_documents()